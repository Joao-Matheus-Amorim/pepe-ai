from core.agent import criar_agente, invocar_agente

agente = criar_agente()
resposta = invocar_agente(agente, "Olá! Quem é você?")
print(resposta)