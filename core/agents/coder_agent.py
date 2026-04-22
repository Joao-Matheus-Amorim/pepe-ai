"""Agente especialista em código.

Usa Qwen2.5-Coder:7b como modelo principal via Ollama.
Ativado pelo router quando a intenção detectada é CODE.

Instalação do modelo:
    ollama pull qwen2.5-coder:7b
"""

from __future__ import annotations

import os
from typing import List

from langchain_core.messages import BaseMessage
from loguru import logger

from core.agents.base_agent import BaseAgent
from core.agents.model_manager import ModelManager

# Modelo principal de código
CODER_MODEL = os.getenv("OLLAMA_CODER_MODEL", "qwen2.5-coder:7b")

# Fallback se o Qwen não estiver instalado
CODER_FALLBACK_MODEL = os.getenv("OLLAMA_CODER_FALLBACK_MODEL", "pepe")


CODER_SYSTEM_PROMPT = """Você é o Pepê no modo Coder — especialista em programação.
Responda SEMPRE em português brasileiro.
Quando gerar código:
  - Use blocos de código com a linguagem correta (```python, ```javascript, etc.)
  - Explique o que o código faz em 1-2 linhas antes do bloco
  - Prefira soluções simples e legíveis
  - Aponte erros e sugira correções quando o usuário mostrar código com problemas
  - Nunca invente APIs ou funções que não existem
Se a tarefa não envolver código, responda normalmente."""


class CoderAgent(BaseAgent):
    """Agente especialista em geração e revisão de código."""

    NOME = "coder"
    SYSTEM_PROMPT = CODER_SYSTEM_PROMPT
    PROVIDER = "ollama"
    TEMPERATURA = 0.2  # Baixa temperatura para código mais preciso

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
        """Verifica se o Qwen está disponível, senão usa fallback."""
        if self._manager.modelo_disponivel(CODER_MODEL):
            logger.info(f"[CoderAgent] Usando modelo: {CODER_MODEL}")
            return CODER_MODEL
        logger.warning(
            f"[CoderAgent] '{CODER_MODEL}' não encontrado. "
            f"Usando fallback: {CODER_FALLBACK_MODEL}. "
            f"Instale com: ollama pull {CODER_MODEL}"
        )
        return CODER_FALLBACK_MODEL

    def responder(self, pergunta: str, historico: List[BaseMessage] | None = None) -> str:
        """Gera resposta de código com controle de memória do modelo."""
        logger.info(f"[CoderAgent] Processando tarefa de código: {pergunta[:80]}")

        # Carrega o modelo com keep_alive curto (libera após 2 min)
        self._manager.carregar(self.modelo, keep_alive=120)

        try:
            return super().responder(pergunta, historico)
        finally:
            # Mantém na memória por 2 min — se não houver nova tarefa, Ollama descarrega automaticamente
            pass
