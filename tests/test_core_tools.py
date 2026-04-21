import os
import unittest
from unittest.mock import patch

from core.tools import consulta_clima, ferramenta_busca, _candidatos_local


class CoreToolsTests(unittest.TestCase):
    def test_candidatos_local_inclui_fallback_para_mage(self):
        candidatos = _candidatos_local("Piabetá Magé RJ")
        texto = " | ".join(candidatos).lower()
        self.assertIn("mage", texto)

    def test_ferramenta_busca_valida_query_vazia(self):
        resposta = ferramenta_busca("   ")
        self.assertIn("Consulta vazia", resposta)

    @patch("core.tools._buscar_ddgs")
    def test_ferramenta_busca_formata_resultados(self, mock_busca):
        mock_busca.return_value = [
            {"title": "Titulo A", "body": "Corpo A"},
            {"title": "Titulo B", "body": "Corpo B"},
        ]

        with patch.dict(os.environ, {"PEPE_SEARCH_PROVIDER": "ddgs"}, clear=True):
            resposta = ferramenta_busca("noticias")

        self.assertIn("Titulo A", resposta)
        self.assertIn("Titulo B", resposta)

    @patch("core.tools._buscar_perplexity")
    def test_ferramenta_busca_usa_perplexity_quando_configurado(self, mock_busca):
        mock_busca.return_value = "Resposta via Perplexity"

        with patch.dict(os.environ, {"PEPE_SEARCH_PROVIDER": "perplexity", "PERPLEXITY_API_KEY": "test-key"}, clear=True):
            resposta = ferramenta_busca("noticias")

        self.assertEqual("Resposta via Perplexity", resposta)
        mock_busca.assert_called_once_with("noticias")

    @patch("core.tools._buscar_ddgs")
    @patch("core.tools._buscar_perplexity")
    def test_ferramenta_busca_faz_fallback_ddgs_quando_perplexity_falha(self, mock_perplexity, mock_ddgs):
        mock_perplexity.side_effect = RuntimeError("sem sessao")
        mock_ddgs.return_value = [{"title": "Titulo Fallback", "body": "Corpo fallback"}]

        with patch.dict(os.environ, {"PEPE_SEARCH_PROVIDER": "perplexity", "PEPE_SEARCH_FALLBACK_DDGS": "true"}, clear=True):
            resposta = ferramenta_busca("noticias")

        self.assertIn("Titulo Fallback", resposta)

    def test_consulta_clima_rejeita_local_vazio(self):
        resposta = consulta_clima("   ")
        self.assertIn("Local inválido", resposta)

    @patch("core.tools._http_get_json")
    def test_consulta_clima_gera_resumo(self, mock_http):
        mock_http.return_value = {
            "current": {
                "temperature_2m": 24,
                "weather_code": 2,
                "wind_speed_10m": 7,
            }
        }

        resposta = consulta_clima("Mage RJ")

        self.assertIn("Magé", resposta)
        self.assertIn("24", resposta)


if __name__ == "__main__":
    unittest.main()
