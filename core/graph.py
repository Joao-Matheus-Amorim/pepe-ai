import os
from typing import Annotated, TypedDict, Union, List, Optional
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from core.llm import criar_llm
from core.tools import ferramenta_busca, consulta_clima
from core.tools_vision import capturar_e_analisar_tela
from core.tools_execute import executar_comando
from core.tools_filesystem import ler_arquivo, listar_arquivos

class Intent(str, Enum):
    CLIMA = "clima"
    WEB = "web"
    VISION = "vision"
    FILES = "files"
    TERMINAL = "terminal"
    GENERAL = "general"

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    intent: Optional[Intent]
    context: dict


AUTO_EVALUATION_PROMPT = (
    "Você é o revisor de respostas do Pepê.\n"
    "Avalie a resposta atual com foco em: utilidade, clareza, objetividade e aderência à pergunta.\n"
    "Se a resposta já estiver boa, retorne exatamente <ok>.\n"
    "Se a resposta estiver ruim, genérica, incompleta, contraditória ou excessivamente longa, retorne somente uma versão final reescrita, em português brasileiro, sem explicações extras."
)

@tool
def search_tool(query: str):
    """Pesquisa informações na web."""
    return ferramenta_busca(query)

@tool
def weather_tool(location: str):
    """Consulta o clima para uma localização."""
    return consulta_clima(location)

@tool
def vision_tool(query: str):
    """Captura e analisa a tela."""
    return capturar_e_analisar_tela(query)

@tool
def terminal_tool(command: str):
    """Executa comandos no terminal."""
    return executar_comando(command)

@tool
def read_file_tool(path: str):
    """Lê um arquivo."""
    return ler_arquivo(path)

@tool
def list_files_tool():
    """Lista arquivos do projeto."""
    return listar_arquivos()


def _texto_da_resposta(resposta) -> str:
    if hasattr(resposta, "content"):
        return str(resposta.content).strip()
    return str(resposta).strip()


def revisar_resposta(llm, prompt_base: str, pergunta: str, resposta: str) -> str:
    """Executa uma autoavaliação e retorna a resposta original ou uma versão melhorada."""
    resposta_limpa = (resposta or "").strip()
    if not resposta_limpa:
        return resposta_limpa

    mensagens = [
        SystemMessage(content=f"{prompt_base}\n\n{AUTO_EVALUATION_PROMPT}"),
        HumanMessage(
            content=(
                f"Pergunta do usuário:\n{pergunta}\n\n"
                f"Resposta atual:\n{resposta_limpa}"
            )
        ),
    ]

    try:
        revisao = llm.invoke(mensagens)
        texto_revisado = _texto_da_resposta(revisao)
    except Exception:
        return resposta_limpa

    if not texto_revisado or texto_revisado.lower() == "<ok>":
        return resposta_limpa
    if texto_revisado.lower().startswith("<ok>"):
        return resposta_limpa
    return texto_revisado

SYSTEM_PROMPT = """Você é o Pepê, um assistente pessoal inteligente e prestativo.
Responda sempre em português brasileiro de forma direta e objetiva."""

def criar_grafo(
    provider: str | None = None,
    modelo: str | None = None,
    temperatura: float = 0.4,
    system_prompt: str | None = None,
):
    llm = criar_llm(provider=provider, modelo=modelo, temperatura=temperatura)
    tools = [search_tool, weather_tool, vision_tool, terminal_tool, read_file_tool, list_files_tool]
    prompt_base = system_prompt or SYSTEM_PROMPT
    
    def classify_intent(state: AgentState) -> AgentState:
        messages = state["messages"]
        user_msg = messages[-1].content if messages else ""
        
        system_msg = prompt_base + """
Classifique a intenção do usuário.
Responda apenas com uma das opções: clima, web, vision, files, terminal ou general.
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", f"{user_msg}"),
        ])
        
        try:
            chain = prompt | llm.with_structured_output(Intent)
            result = chain.invoke({})
        except Exception:
            result = Intent.GENERAL
        
        intent = result if isinstance(result, Intent) else result.get("intent", Intent.GENERAL)
        return {"intent": intent, "context": {}}

    def agent_node(state: AgentState):
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_base),
            MessagesPlaceholder(variable_name="messages"),
        ])
        llm_for_node = llm.bind_tools(tools)
        chain = prompt | llm_for_node
        response = chain.invoke(state)
        return {"messages": [response]}
        
    def respond_node(state: AgentState):
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_base),
            MessagesPlaceholder(variable_name="messages"),
        ])
        chain = prompt | llm
        response = chain.invoke({"messages": state["messages"]})
        pergunta = state["messages"][-1].content if state["messages"] else ""
        resposta_final = revisar_resposta(llm, prompt_base, pergunta, _texto_da_resposta(response))
        return {"messages": [AIMessage(content=resposta_final)]}

    workflow = StateGraph(AgentState)

    workflow.add_node("classify", classify_intent)
    workflow.add_node("agent", agent_node)
    workflow.add_node("respond", respond_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.set_entry_point("classify")

    workflow.add_conditional_edges(
        "classify",
        lambda state: "agent" if state.get("intent") not in [None, Intent.GENERAL] else "respond",
        {
            "agent": "agent",
            "respond": "respond",
        },
    )

    workflow.add_conditional_edges(
        "agent",
        tools_condition,
    )

    workflow.add_edge("tools", "agent")
    workflow.add_edge("respond", END)

    return workflow.compile()
