from core.agent import criar_agente, invocar_agente


def executar_teste_manual():
	agente = criar_agente()
	resposta = invocar_agente(agente, "Olá! Quem é você?")
	print(resposta)


if __name__ == "__main__":
	executar_teste_manual()