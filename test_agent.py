from core.agent import PepeAgent

def main():
    pepe = PepeAgent()
    print("Pepê pronto. Digite 'sair' para encerrar.\n")

    while True:
        entrada = input("Você: ").strip()
        if entrada.lower() in ("sair", "exit", "quit"):
            break

        try:
            resposta = pepe.perguntar(entrada)
            print(f"Pepê: {resposta}\n")
        except Exception as e:
            print(f"Erro: {e}\n")

if __name__ == "__main__":
    main()