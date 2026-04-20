"""Pepê — Personal AI Agent
Entry point do projeto.
"""
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from core.agent import PepeAgent

load_dotenv()
console = Console()


def main():
    console.print(Panel.fit(
        "[bold cyan]🤖 Pepê — Personal AI Agent[/bold cyan]\n"
        "[dim]Iniciando sistema...[/dim]",
        border_style="cyan"
    ))

    try:
        agente = PepeAgent()
    except ValueError as erro:
        console.print(f"[bold red]Erro de configuração:[/bold red] {erro}")
        return
    except Exception as erro:  # pragma: no cover
        console.print(f"[bold red]Falha ao iniciar o agente:[/bold red] {erro}")
        return

    console.print("[green]Sistema pronto. Digite sua mensagem abaixo.[/green]")
    console.print("[dim]Comandos: sair | exit | quit[/dim]")

    while True:
        try:
            pergunta = console.input("[bold green]Você:[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Encerrando Pepê...[/yellow]")
            break

        if pergunta.lower() in {"sair", "exit", "quit"}:
            console.print("[yellow]Até logo![/yellow]")
            break

        if not pergunta:
            console.print("[dim]Digite uma pergunta para continuar.[/dim]")
            continue

        try:
            resposta = agente.perguntar(pergunta)
            console.print(f"[bold cyan]Pepê:[/bold cyan] {resposta}")
        except ValueError as erro:
            console.print(f"[yellow]{erro}[/yellow]")
        except Exception as erro:
            console.print(f"[bold red]Falha durante a execução:[/bold red] {erro}")

if __name__ == "__main__":
    main()
