"""Pepê — Personal AI Agent
Entry point do projeto.
"""
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

def main():
    console.print(Panel.fit(
        "[bold cyan]🤖 Pepê — Personal AI Agent[/bold cyan]\n"
        "[dim]Iniciando sistema...[/dim]",
        border_style="cyan"
    ))
    
    # TODO: Fase 1 — importar e iniciar o agente principal
    # from core.agent import PepeAgent
    # agent = PepeAgent()
    # agent.run()
    
    console.print("[yellow]⚠ Agente ainda não implementado. Siga as issues no GitHub para construir fase a fase![/yellow]")
    console.print("[dim]https://github.com/Joao-Matheus-Amorim/pepe-ai/issues[/dim]")

if __name__ == "__main__":
    main()
