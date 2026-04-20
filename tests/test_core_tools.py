import unittest
from unittest.mock import patch

from core.tools import consulta_clima, ferramenta_busca


class CoreToolsTests(unittest.TestCase):
    def test_ferramenta_busca_valida_query_vazia(self):
        resposta = ferramenta_busca("   ")
        self.assertIn("Consulta vazia", resposta)

    @patch("core.tools._buscar_ddgs")
    def test_ferramenta_busca_formata_resultados(self, mock_busca):
        mock_busca.return_value = [
            {"title": "Titulo A", "body": "Corpo A"},
            {"title": "Titulo B", "body": "Corpo B"},
        ]

        resposta = ferramenta_busca("noticias")

        self.assertIn("Titulo A", resposta)
        self.assertIn("Titulo B", resposta)

    def test_consulta_clima_rejeita_local_vazio(self):
        resposta = consulta_clima("   ")
        self.assertIn("Local inválido", resposta)

    @patch("core.tools._buscar_ddgs")
    def test_consulta_clima_gera_resumo(self, mock_busca):
        mock_busca.return_value = [
            {
                "title": "Clima em Mage",
                "body": "Temperatura 24 C, parcialmente nublado",
            }
        ]

        resposta = consulta_clima("Mage RJ")

        self.assertIn("Mage RJ", resposta)
        self.assertIn("24", resposta)


if __name__ == "__main__":
    unittest.main()
