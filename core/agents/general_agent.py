"""Agente geral — fallback para conversas e tarefas não especializadas.

Usa o modelo pepe (fine-tuned) como padrão.
Ativado pelo router quando a intenção é GENERAL ou não identificada.
"""

from __future__ import annotations

import os
from typing import List

from langchain_core.messages import BaseMessage
from loguru import logger

from core.agents.base_agent import BaseAgent

# Modelo geral — usa o pepe fine-tuned por padrão
GENERAL_MODEL = os.getenv("OLLAMA_GENERAL_MODEL", "pepe")


GENERAL_SYSTEM_PROMPT = """Você é o Pepê, assistente pessoal inteligente do João Matheus.
Responda SEMPRE em português brasileiro. Seja direto e objetivo.
Nunca diga que é ChatGPT, Claude ou qualquer outro assistente.
Se não souber algo, diga: não sei.
Nunca invente links, código não solicitado ou informações não verificadas."""


class GeneralAgent(BaseAgent):
    """Agente de propósito geral — conversa, memória e tarefas cotidianas."""

    NOME = "general"
    SYSTEM_PROMPT = GENERAL_SYSTEM_PROMPT
    PROVIDER = "ollama"
    MODELO = GENERAL_MODEL
    TEMPERATURA = 0.4

    def __init__(self, memory=None):
        super().__init__(
            provider="ollama",
            modelo=GENERAL_MODEL,
            temperatura=self.TEMPERATURA,
            memory=memory,
        )

    def responder(self, pergunta: str, historico: List[BaseMessage] | None = None) -> str:
        logger.info(f"[GeneralAgent] Respondendo: {pergunta[:80]}")
        return super().responder(pergunta, historico)
