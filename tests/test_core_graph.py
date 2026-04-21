import unittest
from types import SimpleNamespace

from core.graph import revisar_resposta


class _LlmRevisorFake:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def invoke(self, mensagens):
        self.chamadas.append(mensagens)
        texto = self.respostas.pop(0) if self.respostas else "<ok>"
        return SimpleNamespace(content=texto)


class GraphReviewTests(unittest.TestCase):
    def test_revisar_resposta_mantem_original_quando_ok(self):
        llm = _LlmRevisorFake(["<ok>"])

        resposta = revisar_resposta(
            llm,
            "Você é o Pepê.",
            "Explique o que é memória.",
            "Memória é o armazenamento de informações.",
        )

        self.assertEqual("Memória é o armazenamento de informações.", resposta)
        self.assertEqual(1, len(llm.chamadas))
        self.assertIn("Resposta atual", llm.chamadas[0][1].content)

    def test_revisar_resposta_reescreve_quando_precisa(self):
        llm = _LlmRevisorFake([
            "A resposta está vaga e genérica. Reescreva de forma direta: Memória é o mecanismo que salva e recupera informações úteis para conversas futuras.",
        ])

        resposta = revisar_resposta(
            llm,
            "Você é o Pepê.",
            "Explique o que é memória.",
            "Não sei dizer exatamente.",
        )

        self.assertIn("Memória é o mecanismo", resposta)
        self.assertEqual(1, len(llm.chamadas))
        self.assertIn("Pergunta do usuário", llm.chamadas[0][1].content)


if __name__ == "__main__":
    unittest.main()
