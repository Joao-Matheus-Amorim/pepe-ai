"""Agente especialista em pesquisa web.

Hierarquia de acesso:
  1. Perplexity API (se PERPLEXITY_API_KEY estiver no .env)
  2. Perplexity via navegador (sessão persistente via Playwright)
  3. Mistral:7b local + DuckDuckGo (fallback offline)

Instalação do modelo fallback:
    ollama pull mistral:7b
"""

from __future__ import annotations

import os
from typing import List

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from loguru import logger

from core.agents.base_agent import BaseAgent
from core.agents.model_manager import ModelManager

# Modelos
RESEARCHER_MODEL = os.getenv("OLLAMA_RESEARCHER_MODEL", "mistral:7b")
RESEARCHER_FALLBACK_MODEL = os.getenv("OLLAMA_RESEARCHER_FALLBACK_MODEL", "pepe")

# Flags de controle
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_LOGIN_METHOD = os.getenv("PEPE_PERPLEXITY_LOGIN_METHOD", "manual").strip().lower()


RESEARCHER_SYSTEM_PROMPT = """Você é o Pepê no modo Researcher — especialista em busca e síntese de informações.
Responda SEMPRE em português brasileiro.
Ao pesquisar:
  - Seja direto: responda a pergunta primeiro, depois dê contexto
  - Cite datas e fontes quando disponíveis
  - Se não encontrar resultado confiável, diga claramente
  - Nunca invente fatos, preços, datas ou notícias
  - Para notícias recentes, sempre use o resultado da busca, nunca sua memória interna"""


class ResearcherAgent(BaseAgent):
    """Agente especialista em pesquisa web com fallback em camadas."""

    NOME = "researcher"
    SYSTEM_PROMPT = RESEARCHER_SYSTEM_PROMPT
    PROVIDER = "ollama"
    TEMPERATURA = 0.3

    def __init__(self, memory=None):
        self._manager = ModelManager()
        modelo = self._resolver_modelo()
        super().__init__(
            provider="ollama",
            modelo=modelo,
            temperatura=self.TEMPERATURA,
            memory=memory,
        )

    def _resolver_modelo(self) -> str:
        """Verifica se o Mistral está disponível, senão usa fallback."""
        if self._manager.modelo_disponivel(RESEARCHER_MODEL):
            logger.info(f"[ResearcherAgent] Usando modelo: {RESEARCHER_MODEL}")
            return RESEARCHER_MODEL
        logger.warning(
            f"[ResearcherAgent] '{RESEARCHER_MODEL}' não encontrado. "
            f"Usando fallback: {RESEARCHER_FALLBACK_MODEL}. "
            f"Instale com: ollama pull {RESEARCHER_MODEL}"
        )
        return RESEARCHER_FALLBACK_MODEL

    def responder(self, pergunta: str, historico: List[BaseMessage] | None = None) -> str:
        """Pesquisa em camadas: Perplexity API → Perplexity Web → Mistral+DDG."""
        logger.info(f"[ResearcherAgent] Pesquisando: {pergunta[:80]}")

        # Camada 1: Perplexity via API
        if PERPLEXITY_API_KEY:
            resultado = self._buscar_perplexity_api(pergunta)
            if resultado:
                return self._sintetizar(pergunta, resultado, historico)

        # Camada 2: Perplexity via navegador (sessão persistente)
        resultado = self._buscar_perplexity_web(pergunta)
        if resultado:
            return resultado  # perplexity_web já retorna resposta formatada

        # Camada 3: Mistral local + DuckDuckGo
        logger.info("[ResearcherAgent] Usando fallback: Mistral + DuckDuckGo")
        resultado_ddg = self._buscar_duckduckgo(pergunta)
        return self._sintetizar(pergunta, resultado_ddg, historico)

    # ------------------------------------------------------------------
    # Camadas de busca
    # ------------------------------------------------------------------

    def _buscar_perplexity_api(self, pergunta: str) -> str:
        """Busca via API oficial do Perplexity."""
        try:
            from core.llm import criar_llm
            llm_perplexity = criar_llm(provider="perplexity", temperatura=0.3)
            resposta = llm_perplexity.invoke(pergunta)
            conteudo = self._extrair_conteudo(resposta)
            if conteudo and len(conteudo) > 20:
                logger.info("[ResearcherAgent] Resposta obtida via Perplexity API")
                return conteudo
        except Exception as erro:
            logger.warning(f"[ResearcherAgent] Perplexity API falhou: {erro}")
        return ""

    def _buscar_perplexity_web(self, pergunta: str) -> str:
        """Busca via Perplexity usando sessão de navegador (Playwright)."""
        try:
            from core.perplexity_web import buscar_perplexity_web
            resultado = buscar_perplexity_web(pergunta)
            if resultado and resultado != "Nenhum resultado encontrado." and len(resultado) > 20:
                logger.info("[ResearcherAgent] Resposta obtida via Perplexity Web")
                return resultado
        except RuntimeError as erro:
            # Sessão não autenticada — fallback silencioso
            logger.warning(f"[ResearcherAgent] Perplexity Web indisponível: {erro}")
        except Exception as erro:
            logger.warning(f"[ResearcherAgent] Perplexity Web falhou: {erro}")
        return ""

    def _buscar_duckduckgo(self, pergunta: str) -> str:
        """Busca via DuckDuckGo como último recurso."""
        try:
            from core.tools import ferramenta_busca
            return ferramenta_busca(pergunta)
        except Exception as erro:
            logger.error(f"[ResearcherAgent] DuckDuckGo falhou: {erro}")
            return "Não foi possível realizar a pesquisa no momento."

    def _sintetizar(self, pergunta: str, contexto: str, historico: List[BaseMessage] | None) -> str:
        """Usa o LLM local para sintetizar o resultado da busca."""
        if not contexto or contexto == "Não foi possível realizar a pesquisa no momento.":
            return contexto

        prompt_sintese = (
            f"Com base nas informações abaixo, responda a pergunta do usuário em português brasileiro.\n"
            f"Seja direto e objetivo.\n\n"
            f"Informações encontradas:\n{contexto}\n\n"
            f"Pergunta: {pergunta}"
        )
        try:
            self._manager.carregar(self.modelo, keep_alive=120)
            return super().responder(prompt_sintese, historico)
        except Exception as erro:
            logger.warning(f"[ResearcherAgent] Síntese falhou, retornando resultado bruto: {erro}")
            return contexto
