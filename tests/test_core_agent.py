import unittest
from unittest.mock import patch

from core.agent import PepeAgent


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


@patch("core.agent.PepeMemory")
class AgentCoreTests(unittest.TestCase):
    def setUp(self, mock_memory=None):
        # Configuração padrão para o mock do PepeMemory
        if mock_memory is not None:
            mock_memory.return_value.buscar_fatos.return_value = []

    def test_pepe_agent_rejeita_pergunta_vazia(self, mock_memory):
        pepe = PepeAgent(agente=_AgenteFake())
        with self.assertRaises(ValueError):
            pepe.perguntar("   ")

    def test_pepe_agent_envia_payload_correto(self, mock_memory):
        agente = _AgenteFake()
        pepe = PepeAgent(agente=agente, session_id="test-session")
        resposta = pepe.perguntar("Qual seu nome?")

        self.assertEqual("resposta-1", resposta)
        self.assertEqual("Qual seu nome?", agente.ultima_entrada["input"])
        self.assertEqual("test-session", agente.ultima_config["configurable"]["session_id"])

    def test_pepe_agent_invoca_com_session_id_padrao(self, mock_memory):
        agente = _AgenteFake()
        pepe = PepeAgent(agente=agente)

        primeira = pepe.perguntar("Olá")
        segunda = pepe.perguntar("Tudo bem?")

        self.assertEqual("resposta-1", primeira)
        self.assertEqual("resposta-2", segunda)
        self.assertEqual("pepe", agente.ultima_config["configurable"]["session_id"])

    def test_pepe_agent_cria_agente_por_padrao(self, mock_memory):
        with patch("core.agent.criar_agente", return_value=_AgenteFake()) as mock_criar:
            pepe = PepeAgent()

        self.assertIsNotNone(pepe)
        mock_criar.assert_called_once()

    def test_pepe_agent_clima_usa_consulta_dedicada(self, mock_memory):
        agente_fake = _AgenteFake()
        pepe = PepeAgent(agente=agente_fake)

        with patch("core.agent.consulta_clima", return_value="Em Magé RJ, a temperatura atual em torno de 25°C."):
            resposta = pepe.perguntar("Qual o clima em Magé?")

        self.assertIn("Magé", resposta)
        self.assertEqual(0, agente_fake.chamadas)

    def test_pepe_agent_busca_retorna_resultado_diretamente(self, mock_memory):
        agente_fake = _AgenteFake()
        pepe = PepeAgent(agente=agente_fake)

        with patch("core.agent.ferramenta_busca", return_value="Fonte X: conteudo"):
            resposta = pepe.perguntar("Quais as notícias de hoje?")

        self.assertEqual("Fonte X: conteudo", resposta)
        self.assertEqual(0, agente_fake.chamadas)

    @patch("core.agent.consulta_clima")
    def test_pepe_agent_clima_mantem_contexto_com_referencia(self, mock_consulta, mock_memory):
        agente_fake = _AgenteFake()
        pepe = PepeAgent(agente=agente_fake)
        mock_consulta.side_effect = [
            "Em Niterói, Rio de Janeiro, agora: 24°C.",
            "Em Niterói, Rio de Janeiro, agora: 24°C.",
        ]

        primeira = pepe.perguntar("clima em Niteroi RJ")
        segunda = pepe.perguntar("e lá?")

        self.assertIn("Niterói", primeira)
        self.assertIn("Niterói", segunda)
        self.assertEqual(2, mock_consulta.call_count)
        self.assertEqual("Niteroi RJ", mock_consulta.call_args_list[0].args[0])
        self.assertEqual("Niteroi RJ", mock_consulta.call_args_list[1].args[0])

    @patch("core.agent.consulta_clima")
    def test_pepe_agent_clima_aceita_follow_up_local(self, mock_consulta, mock_memory):
        agente_fake = _AgenteFake()
        pepe = PepeAgent(agente=agente_fake)
        mock_consulta.side_effect = [
            "Em Magé, Rio de Janeiro, agora: 23°C.",
            "Em Niterói, Rio de Janeiro, agora: 24°C.",
        ]

        pepe.perguntar("clima em Mage RJ")
        resposta = pepe.perguntar("e em Niteroi?")

        self.assertIn("Niterói", resposta)
        self.assertEqual("Mage RJ", mock_consulta.call_args_list[0].args[0])
        self.assertEqual("niteroi", mock_consulta.call_args_list[1].args[0].lower())


if __name__ == "__main__":
    unittest.main()
