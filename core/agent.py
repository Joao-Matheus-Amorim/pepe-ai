from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from core.llm import criar_llm

SYSTEM_PROMPT = """Você é o Pepê, um assistente pessoal inteligente e prestativo.
Responda sempre em português brasileiro de forma clara e objetiva."""

def criar_agente():
    llm = criar_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="historico"),
        ("human", "{input}"),
    ])
    return prompt | llm


def invocar_agente(agente, pergunta, historico=None):
    if historico is None:
        historico = []

    pergunta_limpa = (pergunta or "").strip()
    if not pergunta_limpa:
        raise ValueError("A pergunta não pode estar vazia.")

    resposta = agente.invoke({
        "input": pergunta_limpa,
        "historico": historico
    })
    return resposta.content


class PepeAgent:
    def __init__(self, agente=None):
        self.agente = agente or criar_agente()
        self.historico = []

    def perguntar(self, pergunta: str) -> str:
        resposta = invocar_agente(self.agente, pergunta, self.historico)
        self.historico.append(HumanMessage(content=pergunta.strip()))
        self.historico.append(AIMessage(content=resposta))
        return resposta

    def resetar_contexto(self) -> None:
        self.historico.clear()