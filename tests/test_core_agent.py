import unittest
from unittest.mock import patch

from core.agent import PepeAgent, invocar_agente


class _Resposta:
    def __init__(self, content: str):
        self.content = content


class _AgenteFake:
    def __init__(self):
        self.ultima_entrada = None
        self.chamadas = 0
        self.ultima_config = None

    def invoke(self, entrada, config=None):
        self.chamadas += 1
        self.ultima_entrada = entrada
        self.ultima_config = config
        return _Resposta(f"resposta-{self.chamadas}")


class AgentCoreTests(unittest.TestCase):
    def test_invocar_agente_rejeita_pergunta_vazia(self):
        with self.assertRaises(ValueError):
            invocar_agente(_AgenteFake(), "   ", [])

    def test_invocar_agente_envia_payload_correto(self):
        agente = _AgenteFake()
        resposta = invocar_agente(agente, "Qual seu nome?")

        self.assertEqual("resposta-1", resposta)
        self.assertEqual("Qual seu nome?", agente.ultima_entrada["input"])
        self.assertEqual("manual-invoke", agente.ultima_config["configurable"]["session_id"])

    def test_pepe_agent_invoca_com_session_id(self):
        agente = PepeAgent(agente=_AgenteFake())

        primeira = agente.perguntar("Olá")
        segunda = agente.perguntar("Tudo bem?")

        self.assertEqual("resposta-1", primeira)
        self.assertEqual("resposta-2", segunda)
        self.assertEqual("pepe", agente.agente.ultima_config["configurable"]["session_id"])

    def test_pepe_agent_cria_agente_por_padrao(self):
        with patch("core.agent.criar_agente", return_value=_AgenteFake()) as mock_criar:
            pepe = PepeAgent()

        self.assertIsNotNone(pepe)
        mock_criar.assert_called_once()

    def test_pepe_agent_clima_usa_consulta_dedicada(self):
        agente_fake = _AgenteFake()
        pepe = PepeAgent(agente=agente_fake)

        with patch("core.agent.consulta_clima", return_value="Em Magé RJ, a temperatura atual em torno de 25°C."):
            resposta = pepe.perguntar("Qual o clima em Magé?")

        self.assertIn("Magé", resposta)
        self.assertEqual(0, agente_fake.chamadas)

    def test_pepe_agent_busca_enriquece_prompt(self):
        agente_fake = _AgenteFake()
        pepe = PepeAgent(agente=agente_fake)

        with patch("core.agent.ferramenta_busca", return_value="Fonte X: conteudo"):
            pepe.perguntar("Quais as notícias de hoje?")

        entrada = agente_fake.ultima_entrada["input"]
        self.assertIn("informações da web", entrada)
        self.assertIn("Fonte X", entrada)


if __name__ == "__main__":
    unittest.main()
