"""Router de intenção do Pepê.

Classifica a intenção da mensagem do usuário e despacha para o
agente especializado correto.

Intenções suportadas:
  - CODE    → CoderAgent  (Qwen2.5-Coder:7b)
  - SEARCH  → ResearcherAgent (Perplexity → Mistral + DDG)
  - GENERAL → GeneralAgent (pepe fine-tuned)

Classificação usa regex rápido primeiro; LLM como fallback.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import List

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from loguru import logger

from core.memory import PepeMemory


class Intencao(str, Enum):
    CODE = "code"
    SEARCH = "search"
    GENERAL = "general"


# ---------------------------------------------------------------------------
# Padrões de classificação rápida por regex
# ---------------------------------------------------------------------------

_PADROES_CODE = re.compile(
    r"\b("
    r"c[oó]dig[oa]|script|função|funcao|classe|método|metodo|bug|erro no c[oó]digo|"
    r"implementa|cria uma? func|debug|refatora|refactor|testa|teste unit|pytest|"
    r"javascript|typescript|python|react|node|html|css|sql|bash|shell|dockerfile|"
    r"git|commit|pull request|api rest|endpoint|async|await|loop|lista|dicion[aá]rio|"
    r"instala.*pacote|pip install|npm install|yarn add|como usar.*biblioteca|"
    r"retorna.*erro|stack trace|traceback|syntax error|import error"
    r")\b",
    re.IGNORECASE,
)

_PADROES_SEARCH = re.compile(
    r"\b("
    r"noticia|notícia|noticias|notícias|últimas|recente|agora|hoje|ontem|"
    r"cotacao|cotação|preço|dólar|euro|bitcoin|crypto|bolsa|mercado|"
    r"quem [eé]|o que [eé]|quando foi|onde fica|quantos|qual o presidente|"
    r"pesquisa|busca|procura|encontra|wikipedia|artigo sobre|"
    r"clima|tempo em|temperatura em|previsão|"
    r"lançamento|novo|novidade|update|versão|release"
    r")\b",
    re.IGNORECASE,
)


def _classificar_por_regex(texto: str) -> Intencao | None:
    """Tenta classificar a intenção apenas com regex — sem custo de LLM."""
    if _PADROES_CODE.search(texto):
        return Intencao.CODE
    if _PADROES_SEARCH.search(texto):
        return Intencao.SEARCH
    return None


def _classificar_por_llm(texto: str) -> Intencao:
    """Usa o LLM como classificador quando regex não é suficiente."""
    try:
        from core.llm import criar_llm
        llm = criar_llm(temperatura=0.0)
        prompt = [
            SystemMessage(content=(
                "Você é um classificador de intenção. "
                "Responda SOMENTE com uma das palavras: code, search ou general.\n"
                "- code: o usuário quer gerar, revisar, corrigir ou explicar código/programação\n"
                "- search: o usuário quer buscar informação na web, notícias, dados atuais\n"
                "- general: qualquer outra coisa (conversa, memória, tarefas, perguntas gerais)"
            )),
            HumanMessage(content=texto),
        ]
        resposta = llm.invoke(prompt)
        conteudo = str(getattr(resposta, "content", resposta)).strip().lower()

        if "code" in conteudo:
            return Intencao.CODE
        if "search" in conteudo:
            return Intencao.SEARCH
        return Intencao.GENERAL

    except Exception as erro:
        logger.warning(f"[Router] Classificação LLM falhou, usando GENERAL: {erro}")
        return Intencao.GENERAL


def classificar_intencao(texto: str) -> Intencao:
    """Classifica a intenção da mensagem.

    Tenta regex primeiro (sem custo); cai no LLM se ambíguo.

    Args:
        texto: Mensagem do usuário.

    Returns:
        Intencao detectada.
    """
    intencao = _classificar_por_regex(texto)
    if intencao is not None:
        logger.debug(f"[Router] Intenção por regex: {intencao.value}")
        return intencao

    intencao = _classificar_por_llm(texto)
    logger.debug(f"[Router] Intenção por LLM: {intencao.value}")
    return intencao


def rotear(
    pergunta: str,
    historico: List[BaseMessage] | None = None,
    memory: PepeMemory | None = None,
) -> str:
    """Ponto de entrada principal do router.

    Classifica a intenção e despacha para o agente correto.

    Args:
        pergunta: Texto do usuário.
        historico: Histórico de mensagens (opcional).
        memory: Instância compartilhada de PepeMemory (opcional).

    Returns:
        Resposta gerada pelo agente especializado.
    """
    pergunta = (pergunta or "").strip()
    if not pergunta:
        raise ValueError("A pergunta não pode estar vazia.")

    intencao = classificar_intencao(pergunta)
    logger.info(f"[Router] '{pergunta[:60]}' → {intencao.value}")

    if intencao == Intencao.CODE:
        from core.agents.coder_agent import CoderAgent
        agente = CoderAgent(memory=memory)
        return agente.responder(pergunta, historico)

    if intencao == Intencao.SEARCH:
        from core.agents.researcher_agent import ResearcherAgent
        agente = ResearcherAgent(memory=memory)
        return agente.responder(pergunta, historico)

    from core.agents.general_agent import GeneralAgent
    agente = GeneralAgent(memory=memory)
    return agente.responder(pergunta, historico)
