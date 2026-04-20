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

def invocar_agente(agente, pergunta, historico=[]):
    resposta = agente.invoke({
        "input": pergunta,
        "historico": historico
    })
    return resposta.content