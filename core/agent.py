import re
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from core.llm import criar_llm
from core.tools import ferramenta_busca, consulta_clima

SYSTEM_PROMPT = """Você é o Pepê, um assistente pessoal inteligente e prestativo.
Seu nome é Pepê.
Responda sempre em português brasileiro.
Nunca diga que é ChatGPT.
Se apresentar, diga que é o Pepê.
"""

_store = {}

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

    # Compatibilidade com testes antigos: alguns dublês aceitam apenas invoke(payload).
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

    def perguntar(self, pergunta: str) -> str:
        pergunta_limpa = (pergunta or "").strip()
        if not pergunta_limpa:
            raise ValueError("A pergunta não pode estar vazia.")

        pergunta_lower = pergunta_limpa.lower()

        if self._eh_consulta_clima(pergunta_lower):
            if "piabeta" in pergunta_lower or "piabetá" in pergunta_lower:
                local = "Piabetá Magé RJ"
            elif "mage" in pergunta_lower or "magé" in pergunta_lower:
                local = "Magé RJ"
            else:
                local = self._extrair_local(pergunta_limpa) or "Magé RJ"

            info = consulta_clima(local)
            return info

        if self._eh_consulta_web(pergunta_lower):
            resultado_busca = ferramenta_busca(pergunta_limpa)
            if not resultado_busca.lower().startswith("erro"):
                pergunta_limpa = (
                    "Use estas informações da web para responder de forma direta e curta:\n"
                    f"{resultado_busca}\n\nPergunta original: {pergunta_limpa}"
                )

        resposta = self.agente.invoke(
            {"input": pergunta_limpa},
            config={"configurable": {"session_id": self.session_id}},
        )
        return resposta.content

    def resetar_contexto(self) -> None:
        if self.session_id in _store:
            _store[self.session_id] = InMemoryChatMessageHistory()

    def _extrair_local(self, pergunta: str) -> str | None:
        match = re.search(r"\bem\s+([\w\s\-]+)$", pergunta.strip(), flags=re.IGNORECASE)
        if match:
            local = match.group(1).strip(" ?.!")
            if local:
                return local

        partes = pergunta.replace("?", " ").replace(".", " ").split()
        if len(partes) >= 3:
            return " ".join(partes[-3:])

        return None

    def _eh_consulta_clima(self, pergunta_lower: str) -> bool:
        palavras = ["clima", "tempo", "previsao", "previsão", "chuva", "temperatura"]
        return any(palavra in pergunta_lower for palavra in palavras)

    def _eh_consulta_web(self, pergunta_lower: str) -> bool:
        palavras = [
            "noticia",
            "notícia",
            "noticias",
            "notícias",
            "atual",
            "agora",
            "hoje",
            "cotacao",
            "cotação",
            "preco",
            "preço",
            "precos",
            "preços",
            "valor",
        ]
        return any(palavra in pergunta_lower for palavra in palavras)