import os
import unittest
from unittest.mock import patch

from core.llm import _obter_provider, criar_llm


class LlmCoreTests(unittest.TestCase):
    def test_obter_provider_padrao(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual("ollama", _obter_provider())

    def test_obter_provider_invalido(self):
        with patch.dict(os.environ, {"PEPE_MODEL_PROVIDER": "xpto"}, clear=True):
            with self.assertRaises(ValueError):
                _obter_provider()

    @patch("core.llm._criar_cliente_ollama")
    def test_criar_llm_ollama_usa_modelo_padrao(self, mock_criar_cliente):
        with patch.dict(os.environ, {"PEPE_MODEL_PROVIDER": "ollama"}, clear=True):
            criar_llm()

        mock_criar_cliente.assert_called_once_with("llama3.1", 0.4)

    @patch("core.llm._criar_cliente_ollama")
    def test_criar_llm_ollama_aceita_modelo_customizado(self, mock_criar_cliente):
        with patch.dict(os.environ, {"PEPE_MODEL_PROVIDER": "ollama"}, clear=True):
            criar_llm(modelo="llama3", temperatura=0.1)

        mock_criar_cliente.assert_called_once_with("llama3", 0.1)

    def test_criar_llm_rejeita_provider_nao_suportado(self):
        with self.assertRaises(ValueError):
            criar_llm(provider="gemini")

    @patch("core.llm._criar_cliente_anthropic")
    def test_criar_llm_anthropic_usa_modelo_padrao(self, mock_criar_cliente):
        with patch.dict(os.environ, {"PEPE_MODEL_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "test-key"}, clear=True):
            criar_llm()

        mock_criar_cliente.assert_called_once_with("claude-sonnet-4-20250514", 0.4)

    @patch("core.llm._criar_cliente_anthropic")
    def test_criar_llm_claude_alias_aponta_para_anthropic(self, mock_criar_cliente):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
            criar_llm(provider="claude", modelo="claude-opus-4-5")

        mock_criar_cliente.assert_called_once_with("claude-opus-4-5", 0.4)


if __name__ == "__main__":
    unittest.main()
