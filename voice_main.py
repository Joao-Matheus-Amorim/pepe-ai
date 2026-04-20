import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from core.agent import PepeAgent
from voice.engine import PepeVoice

load_dotenv()
console = Console()

def main():
    console.print(Panel.fit(
        "Pepê — Modo de Voz Ativado\n"
        "Diga algo para começar ou 'sair' para encerrar.",
        border_style="cyan"
    ))

    try:
        agente = PepeAgent()
        voz = PepeVoice()
    except Exception as erro:
        console.print(f"[bold red]Erro ao inicializar:[/bold red] {erro}")
        return

    voz.falar("Olá João Matheus! Como posso te ajudar hoje?")

    while True:
        # 1. Ouvir ou Digitar
        if voz.microphone:
            pergunta = voz.ouvir()
        else:
            pergunta = console.input("[bold green]Você (digite): [/bold green]").strip()
        
        if not pergunta:
            continue
            
        console.print(f"[bold green]Você disse:[/bold green] {pergunta}")

        if pergunta.lower() in ["sair", "encerrar", "parar", "quit", "exit"]:
            voz.falar("Tudo bem, até logo!")
            break

        # 2. Pensar
        try:
            with console.status("[bold cyan]Pepê está pensando..."):
                resposta = agente.perguntar(pergunta)
            
            console.print(f"[bold cyan]Pepê:[/bold cyan] {resposta}")
            
            # 3. Falar
            voz.falar(resposta)
            
        except Exception as erro:
            console.print(f"[bold red]Falha:[/bold red] {erro}")
            voz.falar("Desculpe, tive um problema ao processar isso.")

if __name__ == "__main__":
    main()
