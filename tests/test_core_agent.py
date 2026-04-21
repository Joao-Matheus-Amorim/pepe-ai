import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from core.agent import PepeAgent, invocar_agente
from core.memory import PepeMemory


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


class _GrafoFake:
    def __init__(self):
        self.ultima_entrada = None
        self.ultima_config = None
        self.calls = []

    def invoke(self, entrada, config=None):
        self.ultima_entrada = entrada
        self.ultima_config = config
        self.calls.append((entrada, config))
        return {"messages": [SimpleNamespace(content="resposta-fake")]}


class _CollectionFake:
    def add(self, *args, **kwargs):
        return None

    def query(self, *args, **kwargs):
        return {"documents": [[]]}


class _ClientFake:
    def get_or_create_collection(self, name):
        return _CollectionFake()


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

    def test_pepe_agent_inclui_perfil_no_contexto(self):
        class _MemoriaFake:
            def __init__(self):
                self.perguntas = []

            def registrar_perfil(self, texto):
                self.perguntas.append(texto)
                return False

            def buscar_fatos(self, consulta, n_resultados=3):
                return []

            def resumir_perfil(self):
                return "Nome: João Matheus\nPreferências: prefere Python"

        memoria_fake = _MemoriaFake()
        grafo_fake = _GrafoFake()

        with patch("core.agent.PepeMemory", return_value=memoria_fake), patch(
            "core.agent.criar_grafo", return_value=grafo_fake
        ):
            pepe = PepeAgent()
            resposta = pepe.perguntar("Prefiro Python")

        entrada = grafo_fake.ultima_entrada["messages"][-1].content
        self.assertEqual("resposta-fake", resposta)
        self.assertIn("Perfil conhecido do usuário", entrada)
        self.assertIn("João Matheus", entrada)
        self.assertEqual(["Prefiro Python"], memoria_fake.perguntas)

    def test_pepe_memory_registra_e_carrega_perfil(self):
        with TemporaryDirectory() as temp_dir:
            with patch("core.memory.chromadb.PersistentClient", return_value=_ClientFake()):
                memoria = PepeMemory(persist_directory=temp_dir)
                atualizado = memoria.registrar_perfil(
                    "Me chamo João Matheus. Prefiro trabalhar com Python. Costumo estudar à noite. Estou desenvolvendo um app de finanças."
                )

                perfil_path = Path(temp_dir) / "pepe_user_profile.json"
                self.assertTrue(atualizado)
                self.assertTrue(perfil_path.exists())

                reaberta = PepeMemory(persist_directory=temp_dir)
                resumo = reaberta.resumir_perfil()

            self.assertIn("Nome: João Matheus", resumo)
            self.assertIn("prefere trabalhar com Python", resumo)
            self.assertIn("costuma estudar à noite", resumo)
            self.assertIn("projeto ativo: app de finanças", resumo)

    def test_pepe_agent_carrega_perfil_no_init(self):
        class _MemoriaFake:
            def __init__(self):
                self.profile = object()

        with patch("core.agent.PepeMemory", return_value=_MemoriaFake()) as mock_memoria:
            pepe = PepeAgent()

        self.assertIs(pepe.profile, pepe.memory.profile)
        mock_memoria.assert_called_once()

    def test_pepe_agent_monta_system_prompt_com_perfil(self):
        class _PerfilFake:
            def resumo_para_prompt(self):
                return "Seu usuário é João Matheus, 29 anos.\nPreferências: Python"

        class _MemoriaFake:
            def __init__(self):
                self.profile = _PerfilFake()

        with patch("core.agent.PepeMemory", return_value=_MemoriaFake()):
            pepe = PepeAgent()

        self.assertIn("Seu usuário é João Matheus, 29 anos.", pepe.system_prompt)
        self.assertIn("Preferências: Python", pepe.system_prompt)

    def test_pepe_agent_mantem_perfil_em_10_interacoes(self):
        entradas = [
            "Prefiro Python e estudo à noite.",
            "Quem sou eu?",
            "O que eu prefiro?",
            "Estou desenvolvendo um app de finanças.",
            "Resuma meu perfil.",
            "Gosto de documentação curta.",
            "Costumo revisar código antes de commitar.",
            "Qual é meu nome?",
            "Estou trabalhando em um bot de automação.",
            "Lembre do meu perfil agora.",
        ]

        with TemporaryDirectory() as temp_dir:
            with patch("core.memory.chromadb.PersistentClient", return_value=_ClientFake()):
                memoria = PepeMemory(persist_directory=temp_dir)
                memoria.registrar_perfil("Meu nome é João Matheus. Tenho 29 anos.")
                grafo_fake = _GrafoFake()

                with patch("core.agent.PepeMemory", return_value=memoria), patch(
                    "core.agent.criar_grafo", return_value=grafo_fake
                ):
                    pepe = PepeAgent(agente=object())
                    for entrada in entradas:
                        pepe.perguntar(entrada)

            resumo = memoria.resumir_perfil()

        self.assertEqual(10, len(grafo_fake.calls))
        self.assertIn("Nome:", resumo)
        self.assertIn("Idade:", resumo)
        self.assertIn("Preferências:", resumo)
        self.assertIn("Hábitos:", resumo)
        self.assertIn("Projetos ativos:", resumo)

    @patch("core.agent.consulta_clima")
    def test_pepe_agent_clima_mantem_contexto_com_referencia(self, mock_consulta):
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
    def test_pepe_agent_clima_aceita_follow_up_local(self, mock_consulta):
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
