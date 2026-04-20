import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage

from core.agent import PepeAgent, invocar_agente


class _Resposta:
    def __init__(self, content: str):
        self.content = content


class _AgenteFake:
    def __init__(self):
        self.ultima_entrada = None
        self.chamadas = 0

    def invoke(self, entrada):
        self.chamadas += 1
        self.ultima_entrada = entrada
        return _Resposta(f"resposta-{self.chamadas}")


class AgentCoreTests(unittest.TestCase):
    def test_invocar_agente_rejeita_pergunta_vazia(self):
        with self.assertRaises(ValueError):
            invocar_agente(_AgenteFake(), "   ", [])

    def test_invocar_agente_envia_payload_correto(self):
        agente = _AgenteFake()
        historico = [HumanMessage(content="Oi")]

        resposta = invocar_agente(agente, "Qual seu nome?", historico)

        self.assertEqual("resposta-1", resposta)
        self.assertEqual("Qual seu nome?", agente.ultima_entrada["input"])
        self.assertIs(historico, agente.ultima_entrada["historico"])

    def test_pepe_agent_mantem_historico(self):
        agente = PepeAgent(agente=_AgenteFake())

        primeira = agente.perguntar("Olá")
        segunda = agente.perguntar("Tudo bem?")

        self.assertEqual("resposta-1", primeira)
        self.assertEqual("resposta-2", segunda)
        self.assertEqual(4, len(agente.historico))
        self.assertIsInstance(agente.historico[0], HumanMessage)
        self.assertIsInstance(agente.historico[1], AIMessage)

    def test_pepe_agent_cria_agente_por_padrao(self):
        with patch("core.agent.criar_agente", return_value=_AgenteFake()) as mock_criar:
            pepe = PepeAgent()

        self.assertIsNotNone(pepe)
        mock_criar.assert_called_once()


if __name__ == "__main__":
    unittest.main()
