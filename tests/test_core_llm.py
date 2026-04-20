import os
import unittest
from unittest.mock import patch

from core.llm import _obter_google_api_key, criar_llm


class LlmCoreTests(unittest.TestCase):
    def test_obter_google_api_key_quando_ausente(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                _obter_google_api_key()

    def test_obter_google_api_key_quando_presente(self):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "chave-teste"}, clear=True):
            self.assertEqual("chave-teste", _obter_google_api_key())

    @patch("core.llm.ChatGoogleGenerativeAI")
    def test_criar_llm_usa_modelo_padrao(self, mock_chat_model):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "chave-teste"}, clear=True):
            criar_llm()

        mock_chat_model.assert_called_once()
        kwargs = mock_chat_model.call_args.kwargs
        self.assertEqual("gemini-2.5-flash", kwargs["model"])
        self.assertEqual("chave-teste", kwargs["google_api_key"])

    @patch("core.llm.ChatGoogleGenerativeAI")
    def test_criar_llm_aceita_modelo_customizado(self, mock_chat_model):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "chave-teste"}, clear=True):
            criar_llm(modelo="gemini-2.5-pro", temperatura=0.2)

        kwargs = mock_chat_model.call_args.kwargs
        self.assertEqual("gemini-2.5-pro", kwargs["model"])
        self.assertEqual(0.2, kwargs["temperature"])


if __name__ == "__main__":
    unittest.main()
