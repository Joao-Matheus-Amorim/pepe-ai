import re
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from core.llm import criar_llm
from core.tools import ferramenta_busca, consulta_clima, extrair_local_com_llm


SYSTEM_PROMPT = """Você é o Pepê, um assistente pessoal inteligente e prestativo.
Seu nome é Pepê.
Responda sempre em português brasileiro.
Nunca diga que é ChatGPT, Claude ou qualquer outro assistente.
Se apresentar, diga que é o Pepê.
Seja direto e objetivo nas respostas.
Nunca invente informações sobre clima, temperatura ou previsão do tempo.
"""

_store = {}

INTENCAO_CLIMA = "clima"
INTENCAO_WEB = "web"
INTENCAO_NENHUMA = None

SIGLAS_BR = {
    "ac": "Acre, Brasil", "al": "Alagoas, Brasil", "ap": "Amapá, Brasil",
    "am": "Amazonas, Brasil", "ba": "Bahia, Brasil", "ce": "Ceará, Brasil",
    "df": "Brasília, Brasil", "es": "Espírito Santo, Brasil", "go": "Goiás, Brasil",
    "ma": "Maranhão, Brasil", "mt": "Mato Grosso, Brasil", "ms": "Mato Grosso do Sul, Brasil",
    "mg": "Minas Gerais", "pa": "Pará, Brasil",
    "pb": "Paraíba, Brasil", "pr": "Paraná, Brasil", "pe": "Pernambuco, Brasil",
    "pi": "Piauí, Brasil", "rj": "Rio de Janeiro, Brasil", "rn": "Rio Grande do Norte, Brasil",
    "rs": "Rio Grande do Sul, Brasil", "ro": "Rondônia, Brasil", "rr": "Roraima, Brasil",
    "sc": "Santa Catarina, Brasil", "sp": "São Paulo, Brasil", "se": "Sergipe, Brasil",
    "to": "Tocantins, Brasil",
}

PALAVRAS_PROIBIDAS = {
    "também", "tambem", "agora", "hoje", "amanha", "amanhã",
    "neste", "momento", "atualmente", "currently", "now", "today",
    "tomorrow", "aqui", "ali", "la", "lá", "there", "here",
    "isso", "este", "esta", "esse", "essa", "nenhum", "nenhuma",
    "tudo", "nada", "algo", "alguém", "alguem",
}


def get_session_history(session_id: str):
    if session_id not in _store:
        _store[session_id] = InMemoryChatMessageHistory()
    return _store[session_id]


def criar_agente():
    llm = criar_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    chain = prompt | llm
    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )


def invocar_agente(agente, pergunta: str, historico=None) -> str:
    pergunta_limpa = (pergunta or "").strip()
    if not pergunta_limpa:
        raise ValueError("A pergunta não pode estar vazia.")

    payload = {"input": pergunta_limpa}
    try:
        resposta = agente.invoke(
            payload,
            config={"configurable": {"session_id": "manual-invoke"}},
        )
    except TypeError:
        if historico is not None:
            payload["historico"] = historico
        resposta = agente.invoke(payload)

    return resposta.content


class PepeAgent:
    def __init__(self, agente=None, session_id="pepe"):
        self.agente = agente or criar_agente()
        self.session_id = session_id
        self._ultimo_local: str | None = None
        self._ultima_intencao: str | None = INTENCAO_NENHUMA

    def perguntar(self, pergunta: str) -> str:
        pergunta_limpa = (pergunta or "").strip()
        if not pergunta_limpa:
            raise ValueError("A pergunta não pode estar vazia.")

        pergunta_lower = pergunta_limpa.lower()

        # ── 1. Intenção explícita de clima ─────────────────────────────────
        if self._eh_consulta_clima(pergunta_lower):
            local = self._resolver_local(pergunta_limpa, pergunta_lower)
            if local:
                self._ultimo_local = local
                self._ultima_intencao = INTENCAO_CLIMA
                return consulta_clima(local)
            else:
                self._ultima_intencao = INTENCAO_CLIMA
                return "Em qual cidade você quer saber o clima?"

        # ── 2. Nome/local solto após intenção de clima ─────────────────────
        if self._ultima_intencao == INTENCAO_CLIMA:
            local_solto = self._eh_local_solto(pergunta_limpa, pergunta_lower)
            if local_solto:
                self._ultimo_local = local_solto
                self._ultima_intencao = INTENCAO_CLIMA
                return consulta_clima(local_solto)

        # ── 3. Consulta web ────────────────────────────────────────────────
        if self._eh_consulta_web(pergunta_lower):
            self._ultima_intencao = INTENCAO_WEB
            resultado_busca = ferramenta_busca(pergunta_limpa)
            if not resultado_busca.lower().startswith("erro"):
                pergunta_limpa = (
                    "Use estas informações da web para responder de forma direta e curta:\n"
                    f"{resultado_busca}\n\nPergunta original: {pergunta_limpa}"
                )

        # ── 4. LLM ────────────────────────────────────────────────────────
        if self._ultima_intencao == INTENCAO_CLIMA:
            self._ultima_intencao = INTENCAO_NENHUMA

        resposta = self.agente.invoke(
            {"input": pergunta_limpa},
            config={"configurable": {"session_id": self.session_id}},
        )
        return resposta.content

    def resetar_contexto(self) -> None:
        if self.session_id in _store:
            _store[self.session_id] = InMemoryChatMessageHistory()
        self._ultimo_local = None
        self._ultima_intencao = None

    def _sanitizar_local(self, local: str) -> str | None:
        if not local:
            return None
        limpo = local.strip(" ,.!?").lower()
        if limpo in PALAVRAS_PROIBIDAS:
            return None
        if limpo in SIGLAS_BR:
            return SIGLAS_BR[limpo]
        resultado = local.strip(" ,.!?")
        return resultado if resultado else None

    def _eh_local_solto(self, pergunta: str, pergunta_lower: str) -> str | None:
        REFERENCIAS = {"la", "lá", "ali", "there"}
        palavras = set(re.sub(r"[?.!,]", "", pergunta_lower).split())
        if palavras & REFERENCIAS and self._ultimo_local:
            return self._ultimo_local

        match_cont = re.match(
            r"^e\s+(em|no|na|nos|nas|in|at|de|do|da)\s+(.+)",
            pergunta_lower
        )
        if match_cont:
            local = match_cont.group(2).strip(" ?.!,")
            return self._sanitizar_local(local)

        palavras_lista = pergunta.strip(" ?.!,").split()
        tem_verbo = bool(re.search(
            r"\b(é|e|está|esta|tem|vai|quer|quero|como|qual|quem|"
            r"is|are|has|have|what|how|who|preciso|pode|consigo|"
            r"nao|não|nunca|sempre|ajuda|ajude|fale|fala|me|meu|minha)\b",
            pergunta_lower
        ))
        if len(palavras_lista) <= 3 and not tem_verbo:
            candidato = pergunta.strip(" ?.!,")
            if re.match(r"^[\w\s\-,\.]+$", candidato) and len(candidato) >= 2:
                return self._sanitizar_local(candidato)

        return None

    def _resolver_local(self, pergunta: str, pergunta_lower: str) -> str | None:
        REFERENCIAS = {"la", "lá", "ali", "there"}
        palavras = set(re.sub(r"[?.!,]", "", pergunta_lower).split())
        if palavras & REFERENCIAS and self._ultimo_local:
            return self._ultimo_local

        match_cont = re.match(
            r"^e\s+(em|no|na|nos|nas|in|at|de|do|da)\s+(.+)",
            pergunta_lower
        )
        if match_cont:
            local = match_cont.group(2).strip(" ?.!,")
            return self._sanitizar_local(local)

        local_regex = self._extrair_local_regex(pergunta)
        if local_regex:
            sanitizado = self._sanitizar_local(local_regex)
            if sanitizado:
                return sanitizado

        if len(pergunta.split()) >= 4:
            local_llm = extrair_local_com_llm(pergunta)
            if local_llm:
                sanitizado = self._sanitizar_local(local_llm)
                if sanitizado:
                    return sanitizado

        if self._ultimo_local:
            return self._ultimo_local

        return None

    def _extrair_local_regex(self, pergunta: str) -> str | None:
        padroes = [
            r"\bclima\s+d[eo]\s+([\w\s\-,]+?)(?:\?|$|\.|hoje|agora|amanhã|amanha)",
            r"\btemperatura\s+(?:em|de|do|da|no|na)\s+([\w\s\-,]+?)(?:\?|$|\.|hoje|agora|amanhã|amanha)",
            r"\bprevis[aã]o\s+(?:de\s+tempo\s+)?(?:para|em|de)\s+([\w\s\-,]+?)(?:\?|$|\.|hoje|agora)",
            r"\btempo\s+em\s+([\w\s\-,]+?)(?:\?|$|\.|hoje|agora|amanhã|amanha)",
            r"\bchuva\s+em\s+([\w\s\-,]+?)(?:\?|$|\.|hoje|agora)",
            r"\bweather\s+in\s+([\w\s\-,]+?)(?:\?|$|\.|today|now)",
            r"\bclima\s+(?:em|no|na|nos|nas)\s+([\w\s\-,]+?)(?:\?|$|\.|hoje|agora)",
            r"\bem\s+([\w][^\s,?!]{1,40})(?:\s*[,?!]|$)",
        ]

        for padrao in padroes:
            match = re.search(padrao, pergunta.strip(), flags=re.IGNORECASE)
            if match:
                local = match.group(1).strip(" ,.!?")
                local = re.sub(
                    r"\b(agora|hoje|amanha|amanhã|now|today|tomorrow|"
                    r"neste momento|atualmente|currently|sudeste|nordeste|"
                    r"norte|sul|centro.oeste)\b.*$",
                    "", local, flags=re.IGNORECASE,
                ).strip(" ,")
                if local and len(local) >= 2:
                    return local

        return None

    def _eh_consulta_clima(self, pergunta_lower: str) -> bool:
        palavras_fortes = [
            "clima", "previsao", "previsão", "temperatura",
            "chuva", "neve", "vento", "umidade",
            "weather", "forecast", "rain", "snow", "humidity",
            "trovoada", "storm", "calor", "heat", "frio",
        ]
        if any(p in pergunta_lower for p in palavras_fortes):
            return True

        if "tempo" in pergunta_lower:
            if re.search(r"\btempo\s+(em|no|na|de|do|da|in|at)\s+\w", pergunta_lower):
                return True

        if re.match(r"^e\s+(em|no|na|nos|nas|in|at)\s+\w", pergunta_lower):
            if self._ultimo_local:
                return True

        if re.search(r"\be\s+(l[aá]|ali|there)\b", pergunta_lower):
            return True

        return False

    def _eh_consulta_web(self, pergunta_lower: str) -> bool:
        palavras = [
            "noticia", "notícia", "noticias", "notícias",
            "cotacao", "cotação", "preco", "preço",
            "precos", "preços", "valor", "news", "latest",
        ]
        return any(p in pergunta_lower for p in palavras)