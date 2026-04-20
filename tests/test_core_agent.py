import unittest
from unittest.mock import patch, MagicMock

from core.agent import PepeAgent, invocar_agente
from langchain_core.messages import AIMessage


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
    def test_invocar_agente_rejeita_pergunta_vazia(self, mock_memory):
        with self.assertRaises(ValueError):
            invocar_agente(_AgenteFake(), "   ", [])

    def test_invocar_agente_envia_payload_correto(self, mock_memory):
        agente = _AgenteFake()
        resposta = invocar_agente(agente, "Qual seu nome?")
        self.assertEqual("resposta-1", resposta)
        self.assertEqual("Qual seu nome?", agente.ultima_entrada["input"])

    def test_pepe_agent_rejeita_pergunta_vazia(self, mock_memory):
        mock_memory.return_value.buscar_fatos.return_value = []
        pepe = PepeAgent(agente=_AgenteFake())
        with self.assertRaises(ValueError):
            pepe.perguntar("   ")


@patch("core.agent.criar_grafo")
@patch("core.agent.PepeMemory")
class AgentGraphTests(unittest.TestCase):
    def test_pepe_agent_envia_payload_correto(self, mock_memory, mock_criar_grafo):
        mock_graph = MagicMock()
        mock_criar_grafo.return_value = mock_graph
        mock_graph.invoke.return_value = {"messages": [AIMessage(content="resposta-teste")]}
        mock_memory.return_value.buscar_fatos.return_value = []
        pepe = PepeAgent(session_id="test-session")
        resposta = pepe.perguntar("Qual seu nome?")
        self.assertEqual("resposta-teste", resposta)
        mock_graph.invoke.assert_called_once()

    def test_pepe_agent_invoca_com_session_id_padrao(self, mock_memory, mock_criar_grafo):
        mock_graph = MagicMock()
        mock_criar_grafo.return_value = mock_graph
        mock_graph.invoke.return_value = {"messages": [AIMessage(content="resposta-1")]}
        mock_memory.return_value.buscar_fatos.return_value = []
        pepe = PepeAgent()
        primeira = pepe.perguntar("Olá")
        segunda = pepe.perguntar("Tudo bem?")
        self.assertIn("resposta", primeira.lower())
        self.assertEqual(2, mock_graph.invoke.call_count)

    def test_pepe_agent_cria_agente_por_padrao(self, mock_memory, mock_criar_grafo):
        mock_graph = MagicMock()
        mock_criar_grafo.return_value = mock_graph
        mock_memory.return_value.buscar_fatos.return_value = []
        pepe = PepeAgent()
        self.assertIsNotNone(pepe)

    def test_pepe_agent_clima_usa_consulta_dedicada(self, mock_memory, mock_criar_grafo):
        mock_graph = MagicMock()
        mock_criar_grafo.return_value = mock_graph
        mock_graph.invoke.return_value = {"messages": [AIMessage(content="Em Magé RJ, a temperatura atual em torno de 25°C.")]}
        mock_memory.return_value.buscar_fatos.return_value = []
        pepe = PepeAgent()
        resposta = pepe.perguntar("Qual o clima em Magé?")
        self.assertIn("Magé", resposta)

    def test_pepe_agent_busca_enriquece_prompt_e_invoca_llm(self, mock_memory, mock_criar_grafo):
        mock_graph = MagicMock()
        mock_criar_grafo.return_value = mock_graph
        mock_graph.invoke.return_value = {"messages": [AIMessage(content="Notícias de hoje.")]}
        mock_memory.return_value.buscar_fatos.return_value = []
        pepe = PepeAgent()
        resposta = pepe.perguntar("Quais as notícias de hoje?")
        self.assertIn("notícias", resposta.lower())

    def test_pepe_agent_clima_mantem_contexto_com_referencia(self, mock_memory, mock_criar_grafo):
        mock_graph = MagicMock()
        mock_criar_grafo.return_value = mock_graph
        mock_graph.invoke.return_value = {"messages": [AIMessage(content="Em Niterói, Rio de Janeiro, agora: 24°C.")]}
        mock_memory.return_value.buscar_fatos.return_value = []
        pepe = PepeAgent()
        primeira = pepe.perguntar("clima em Niteroi RJ")
        segunda = pepe.perguntar("e lá?")
        self.assertIn("Niterói", primeira)
        self.assertIn("Niterói", segunda)
        self.assertEqual(2, mock_graph.invoke.call_count)

    def test_pepe_agent_clima_aceita_follow_up_local(self, mock_memory, mock_criar_grafo):
        mock_graph = MagicMock()
        mock_criar_grafo.return_value = mock_graph
        mock_graph.invoke.return_value = {"messages": [AIMessage(content="Em Niterói, Rio de Janeiro, agora: 24°C.")]}
        mock_memory.return_value.buscar_fatos.return_value = []
        pepe = PepeAgent()
        pepe.perguntar("clima em Mage RJ")
        resposta = pepe.perguntar("e em Niteroi?")
        self.assertIn("Niterói", resposta)
        self.assertEqual(2, mock_graph.invoke.call_count)


if __name__ == "__main__":
    unittest.main()