"""Gerenciador de modelos Ollama.

Controla carga e descarga de modelos via API do Ollama,
usando keep_alive para liberar memória quando o modelo
não está em uso.

Uso:
    manager = ModelManager()
    manager.carregar("qwen2.5-coder:7b")
    # ... usa o modelo ...
    manager.descarregar("qwen2.5-coder:7b")
"""

from __future__ import annotations

import os
from typing import Set

import requests
from loguru import logger


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Tempo em segundos que o modelo fica na memória após o último uso.
# 0 = libera imediatamente após a resposta.
# -1 = nunca descarrega.
DEFAULT_KEEP_ALIVE = int(os.getenv("OLLAMA_KEEP_ALIVE_SECONDS", "300"))  # 5 min


class ModelManager:
    """Gerencia o ciclo de vida dos modelos Ollama em memória."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._modelos_ativos: Set[str] = set()

    # ------------------------------------------------------------------
    # Operações públicas
    # ------------------------------------------------------------------

    def carregar(self, modelo: str, keep_alive: int = DEFAULT_KEEP_ALIVE) -> bool:
        """Pré-carrega um modelo na memória do Ollama.

        Args:
            modelo: Nome do modelo (ex: 'qwen2.5-coder:7b').
            keep_alive: Segundos para manter na memória. 0 = libera imediatamente. -1 = sempre.

        Returns:
            True se carregado com sucesso, False caso contrário.
        """
        try:
            resposta = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": modelo, "keep_alive": keep_alive, "prompt": ""},
                timeout=30,
            )
            resposta.raise_for_status()
            self._modelos_ativos.add(modelo)
            logger.info(f"[ModelManager] Modelo '{modelo}' carregado (keep_alive={keep_alive}s)")
            return True
        except requests.exceptions.ConnectionError:
            logger.error("[ModelManager] Ollama não está rodando em %s", self.base_url)
            return False
        except Exception as erro:
            logger.warning(f"[ModelManager] Falha ao carregar '{modelo}': {erro}")
            return False

    def descarregar(self, modelo: str) -> bool:
        """Remove um modelo da memória do Ollama imediatamente.

        Args:
            modelo: Nome do modelo a descarregar.

        Returns:
            True se descarregado com sucesso, False caso contrário.
        """
        try:
            resposta = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": modelo, "keep_alive": 0, "prompt": ""},
                timeout=15,
            )
            resposta.raise_for_status()
            self._modelos_ativos.discard(modelo)
            logger.info(f"[ModelManager] Modelo '{modelo}' descarregado da memória")
            return True
        except Exception as erro:
            logger.warning(f"[ModelManager] Falha ao descarregar '{modelo}': {erro}")
            return False

    def listar_modelos_instalados(self) -> list[str]:
        """Retorna lista de modelos disponíveis no Ollama local."""
        try:
            resposta = requests.get(f"{self.base_url}/api/tags", timeout=10)
            resposta.raise_for_status()
            dados = resposta.json()
            return [m["name"] for m in dados.get("models", [])]
        except Exception as erro:
            logger.warning(f"[ModelManager] Não foi possível listar modelos: {erro}")
            return []

    def modelo_disponivel(self, modelo: str) -> bool:
        """Verifica se um modelo está instalado no Ollama."""
        instalados = self.listar_modelos_instalados()
        # Verifica correspondência exata ou por prefixo (ex: 'qwen2.5-coder' bate 'qwen2.5-coder:7b')
        for instalado in instalados:
            if instalado == modelo or instalado.startswith(modelo.split(":")[0]):
                return True
        return False

    @property
    def modelos_ativos(self) -> Set[str]:
        """Conjunto de modelos atualmente carregados via este manager."""
        return frozenset(self._modelos_ativos)
