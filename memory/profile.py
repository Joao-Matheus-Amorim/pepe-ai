import json
import re
from pathlib import Path


def _normalizar_item(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto or "").strip(" .,!?:;\"'")
    texto = re.sub(r"^(o|a|os|as|um|uma)\s+", "", texto, flags=re.IGNORECASE)
    return texto.strip()


def _titulo(texto: str) -> str:
    texto = _normalizar_item(texto)
    return texto[:1].upper() + texto[1:] if texto else texto


class PerfilUsuario:
    def __init__(self, persist_directory: str = "./memory/data"):
        self.persist_directory = persist_directory
        self.profile_path = Path(self.persist_directory) / "pepe_user_profile.json"
        self._perfil = self._carregar_perfil()

    def _perfil_padrao(self) -> dict:
        return {
            "nome": None,
            "idade": None,
            "preferencias": [],
            "habitos": [],
            "projetos_ativos": [],
        }

    def _carregar_perfil(self) -> dict:
        if not self.profile_path.exists():
            return self._perfil_padrao()

        try:
            dados = json.loads(self.profile_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self._perfil_padrao()

        perfil = self._perfil_padrao()
        for chave in perfil:
            valor = dados.get(chave)
            if isinstance(valor, list):
                perfil[chave] = [str(item) for item in valor if str(item).strip()]
            elif chave == "nome" and isinstance(valor, str) and valor.strip():
                perfil[chave] = valor.strip()
            elif chave == "idade":
                if isinstance(valor, int) and valor > 0:
                    perfil[chave] = valor
                elif isinstance(valor, str) and valor.strip().isdigit():
                    perfil[chave] = int(valor.strip())
        return perfil

    def _salvar_perfil(self) -> None:
        self.profile_path.write_text(
            json.dumps(self._perfil, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _adicionar_unico(self, chave: str, valor: str) -> bool:
        valor = _normalizar_item(valor)
        if not valor:
            return False
        itens = self._perfil.setdefault(chave, [])
        if valor in itens:
            return False
        itens.append(valor)
        return True

    def registrar(self, texto: str) -> bool:
        texto_limpo = (texto or "").strip()
        if not texto_limpo:
            return False

        atualizado = False
        regras = [
            (
                "preferencias",
                [
                    (r"\b(prefiro|quero|gosto de|curto|adoro|aprecio)\s+(.+?)(?:[.!?;]|$)", "prefere"),
                    (r"\b(n[aã]o gosto de|evito|detesto)\s+(.+?)(?:[.!?;]|$)", "não gosta de"),
                ],
            ),
            (
                "habitos",
                [
                    (r"\b(costumo|normalmente|geralmente|sempre|tenho o h[aá]bito de)\s+(.+?)(?:[.!?;]|$)", "costuma"),
                    (r"\b(geralmente eu|normalmente eu|sempre eu)\s+(.+?)(?:[.!?;]|$)", "costuma"),
                ],
            ),
            (
                "projetos_ativos",
                [
                    (r"\b(estou trabalhando em|estou desenvolvendo|estou construindo|estou montando|estou fazendo|estou focado em|meu projeto(?: atual)?(?: é|:)?|projeto ativo(?: é|:)?)\s+(.+?)(?:[.!?;]|$)", "projeto ativo"),
                    (r"\b(trabalho em|desenvolvo|construo)\s+(.+?)(?:[.!?;]|$)", "projeto ativo"),
                ],
            ),
        ]

        nome_match = re.search(
            r"\b(me chamo|meu nome e|meu nome é|sou o|sou a)\s+(.+?)(?:[.!?;]|$)",
            texto_limpo,
            flags=re.IGNORECASE,
        )
        if nome_match:
            nome = _titulo(nome_match.group(2))
            if nome and nome != self._perfil.get("nome"):
                self._perfil["nome"] = nome
                atualizado = True

        idade_match = re.search(
            r"\b(tenho|idade\s*[:=-]?|sou de)\s*(\d{1,3})\s*anos?\b",
            texto_limpo,
            flags=re.IGNORECASE,
        )
        if idade_match:
            idade = int(idade_match.group(2))
            if 0 < idade < 130 and idade != self._perfil.get("idade"):
                self._perfil["idade"] = idade
                atualizado = True

        for chave, padroes in regras:
            for padrao, rotulo in padroes:
                match = re.search(padrao, texto_limpo, flags=re.IGNORECASE)
                if not match:
                    continue
                trecho = match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(1)
                trecho = _normalizar_item(trecho)
                if not trecho:
                    continue
                if chave == "preferencias":
                    item = f"{rotulo} {trecho}"
                elif chave == "habitos":
                    item = f"{rotulo} {trecho}"
                else:
                    item = f"{rotulo}: {trecho}"
                if self._adicionar_unico(chave, item):
                    atualizado = True

        if atualizado:
            self._salvar_perfil()
        return atualizado

    def registrar_perfil(self, texto: str) -> bool:
        return self.registrar(texto)

    def resumo(self) -> str:
        partes: list[str] = []
        nome = self._perfil.get("nome")
        if nome:
            partes.append(f"Nome: {nome}")
        idade = self._perfil.get("idade")
        if idade:
            partes.append(f"Idade: {idade}")
        if self._perfil.get("preferencias"):
            partes.append("Preferências: " + "; ".join(self._perfil["preferencias"][:5]))
        if self._perfil.get("habitos"):
            partes.append("Hábitos: " + "; ".join(self._perfil["habitos"][:5]))
        if self._perfil.get("projetos_ativos"):
            partes.append("Projetos ativos: " + "; ".join(self._perfil["projetos_ativos"][:5]))
        return "\n".join(partes)

    def resumo_para_prompt(self) -> str:
        partes: list[str] = []
        nome = self._perfil.get("nome")
        idade = self._perfil.get("idade")
        if nome and idade:
            partes.append(f"Seu usuário é {nome}, {idade} anos.")
        elif nome:
            partes.append(f"Seu usuário é {nome}.")
        elif idade:
            partes.append(f"Seu usuário tem {idade} anos.")

        if self._perfil.get("preferencias"):
            partes.append("Preferências: " + "; ".join(self._perfil["preferencias"][:5]))
        if self._perfil.get("habitos"):
            partes.append("Hábitos: " + "; ".join(self._perfil["habitos"][:5]))
        if self._perfil.get("projetos_ativos"):
            partes.append("Projetos ativos: " + "; ".join(self._perfil["projetos_ativos"][:5]))
        return "\n".join(partes)

    def resumir_perfil(self) -> str:
        return self.resumo()
