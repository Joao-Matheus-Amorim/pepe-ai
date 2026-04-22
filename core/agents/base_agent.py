"""Classe base para todos os subagentes do Pepê.

Todo agente especializado herda desta classe e recebe:
- LLM configurado via core/llm.py
- Ferramentas (tools) opcionais
- Memória de longo prazo via PepeMemory
"""

from __future__ import annotations

from typing import List, Optional

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from loguru import logger

from core.llm import criar_llm
from core.memory import PepeMemory


class BaseAgent:
    """Agente base com LLM, ferramentas e memória."""

    # Subclasses devem definir estes atributos
    NOME: str = "base"
    SYSTEM_PROMPT: str = "Você é o Pepê, assistente pessoal. Responda sempre em português brasileiro."
    PROVIDER: str = "ollama"
    MODELO: str | None = None
    TEMPERATURA: float = 0.4

    def __init__(
        self,
        provider: str | None = None,
        modelo: str | None = None,
        temperatura: float | None = None,
        tools: List[BaseTool] | None = None,
        memory: PepeMemory | None = None,
    ):
        self.provider = provider or self.PROVIDER
        self.modelo = modelo or self.MODELO
        self.temperatura = temperatura if temperatura is not None else self.TEMPERATURA
        self.tools = tools or []
        self.memory = memory or PepeMemory()

        self.llm = criar_llm(
            provider=self.provider,
            modelo=self.modelo,
            temperatura=self.temperatura,
        )
        logger.info(f"[{self.NOME}] Agente iniciado — provider={self.provider} modelo={self.modelo}")

    # ------------------------------------------------------------------
    # Interface pública
    # ------------------------------------------------------------------

    def responder(self, pergunta: str, historico: List[BaseMessage] | None = None) -> str:
        """Gera uma resposta para a pergunta recebida.

        Args:
            pergunta: Texto da pergunta do usuário.
            historico: Mensagens anteriores da conversa (opcional).

        Returns:
            Texto da resposta gerada.
        """
        pergunta = (pergunta or "").strip()
        if not pergunta:
            raise ValueError("A pergunta não pode estar vazia.")

        historico = historico or []
        contexto = self._enriquecer_com_memoria(pergunta)
        mensagens = self._montar_mensagens(contexto, historico)

        try:
            if self.tools:
                llm_com_tools = self.llm.bind_tools(self.tools)
                resposta = llm_com_tools.invoke(mensagens)
            else:
                resposta = self.llm.invoke(mensagens)

            conteudo = self._extrair_conteudo(resposta)
            logger.debug(f"[{self.NOME}] Resposta gerada ({len(conteudo)} chars)")
            return conteudo

        except Exception as erro:
            logger.error(f"[{self.NOME}] Falha ao gerar resposta: {erro}")
            raise

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _enriquecer_com_memoria(self, pergunta: str) -> str:
        """Adiciona contexto de memória de longo prazo à pergunta."""
        try:
            fatos = self.memory.buscar_fatos(pergunta)
            perfil = self.memory.resumir_perfil()
        except Exception:
            return pergunta

        partes = []
        if perfil:
            partes.append(f"Perfil do usuário:\n{perfil}")
        if fatos:
            partes.append("Fatos relevantes: " + "; ".join(fatos))
        partes.append(f"Pergunta: {pergunta}")
        return "\n\n".join(partes)

    def _montar_mensagens(self, conteudo: str, historico: List[BaseMessage]) -> List[BaseMessage]:
        """Monta a lista de mensagens para o LLM."""
        mensagens: List[BaseMessage] = [SystemMessage(content=self.SYSTEM_PROMPT)]
        mensagens.extend(historico)
        mensagens.append(HumanMessage(content=conteudo))
        return mensagens

    @staticmethod
    def _extrair_conteudo(resposta) -> str:
        """Extrai texto de uma resposta do LLM."""
        if hasattr(resposta, "content"):
            return str(resposta.content).strip()
        return str(resposta).strip()
