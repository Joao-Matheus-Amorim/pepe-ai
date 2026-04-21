import json
import os
import re
from pathlib import Path

import chromadb
from loguru import logger


def _normalizar_item(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto or "").strip(" .,!?:;\"'")
    texto = re.sub(r"^(o|a|os|as|um|uma)\s+", "", texto, flags=re.IGNORECASE)
    return texto.strip()


def _titulo(texto: str) -> str:
    texto = _normalizar_item(texto)
    return texto[:1].upper() + texto[1:] if texto else texto

class PepeMemory:
    def __init__(self, persist_directory: str = "./memory/data"):
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        self.profile_path = Path(self.persist_directory) / "pepe_user_profile.json"
        
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name="pepe_long_term_memory")
        self._perfil = self._carregar_perfil()
        logger.info(f"Memória persistente iniciada em: {self.persist_directory}")

    def _perfil_padrao(self) -> dict:
        return {
            "nome": None,
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
            logger.warning(f"Falha ao carregar perfil do usuário em: {self.profile_path}")
            return self._perfil_padrao()

        perfil = self._perfil_padrao()
        for chave in perfil:
            valor = dados.get(chave)
            if isinstance(valor, list):
                perfil[chave] = [str(item) for item in valor if str(item).strip()]
            elif chave == "nome" and isinstance(valor, str) and valor.strip():
                perfil[chave] = valor.strip()
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

    def registrar_perfil(self, texto: str) -> bool:
        """Extrai sinais de perfil do texto do usuário e persiste o resultado."""
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

    def resumir_perfil(self) -> str:
        """Retorna um resumo curto do perfil do usuário para injeção no contexto."""
        partes: list[str] = []
        nome = self._perfil.get("nome")
        if nome:
            partes.append(f"Nome: {nome}")
        if self._perfil.get("preferencias"):
            partes.append("Preferências: " + "; ".join(self._perfil["preferencias"][:5]))
        if self._perfil.get("habitos"):
            partes.append("Hábitos: " + "; ".join(self._perfil["habitos"][:5]))
        if self._perfil.get("projetos_ativos"):
            partes.append("Projetos ativos: " + "; ".join(self._perfil["projetos_ativos"][:5]))
        return "\n".join(partes)

    def adicionar_fato(self, fato: str, metadata: dict = None):
        """Adiciona um fato ou informação à memória de longo prazo."""
        self.collection.add(
            documents=[fato],
            metadatas=[metadata or {}],
            ids=[f"fact_{os.urandom(4).hex()}"]
        )
        logger.info(f"Fato adicionado à memória: {fato[:50]}...")

    def buscar_fatos(self, consulta: str, n_resultados: int = 3):
        """Busca fatos relevantes na memória com base em uma consulta."""
        resultados = self.collection.query(
            query_texts=[consulta],
            n_results=n_resultados
        )
        return resultados["documents"][0] if resultados["documents"] else []

if __name__ == "__main__":
    # Teste simples
    mem = PepeMemory()
    mem.adicionar_fato("O usuário João Matheus prefere o tema escuro.")
    mem.registrar_perfil("Me chamo João Matheus. Prefiro trabalhar com Python. Costumo estudar à noite. Estou desenvolvendo um app de finanças.")
    print(mem.resumir_perfil())
    print(mem.buscar_fatos("Qual a preferência do João?"))
