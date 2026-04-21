"""Pepe AI — MCP Server
Expõe as capacidades do agente Pepe como ferramentas MCP.
Compatível com Claude Desktop, Claude Code e qualquer cliente MCP.

MCPs externos integrados:
- @modelcontextprotocol/server-github  (GitHub)
- mcp-server-git                        (Git local - Python)
- @modelcontextprotocol/server-filesystem
- @modelcontextprotocol/server-memory
- @modelcontextprotocol/server-sequential-thinking
- @modelcontextprotocol/server-brave-search
- @upstash/context7-mcp
- @playwright/mcp
- mcp-server-sqlite                     (Python)
"""
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any

# Adiciona o diretório raiz do pepe-ai ao PYTHONPATH
PEPE_ROOT = Path(os.getenv("PEPE_ROOT", str(Path(__file__).parent)))
sys.path.insert(0, str(PEPE_ROOT))

from dotenv import load_dotenv

load_dotenv(PEPE_ROOT / ".env")

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ImageContent,
    TextContent,
    Tool,
)

# ---------------------------------------------------------------------------
# Instância do servidor MCP
# ---------------------------------------------------------------------------
server = Server("pepe-ai")

# ---------------------------------------------------------------------------
# Gerenciamento de sessões (lazy init)
# ---------------------------------------------------------------------------
_agents: dict[str, Any] = {}
_sessions_ts: dict[str, float] = {}
MAX_SESSION_AGE = 3600  # 1 hora


def _cleanup_sessions() -> None:
    now = time.time()
    expired = [s for s, t in _sessions_ts.items() if now - t > MAX_SESSION_AGE]
    for sid in expired:
        _agents.pop(sid, None)
        _sessions_ts.pop(sid, None)


def _get_agent(session_id: str = "default") -> Any:
    """Obtém ou cria um PepeAgent para a sessão."""
    _cleanup_sessions()
    if session_id not in _agents:
        from core.agent import PepeAgent
        _agents[session_id] = PepeAgent(session_id=session_id)
        _sessions_ts[session_id] = time.time()
    return _agents[session_id]


# ---------------------------------------------------------------------------
# Definição das ferramentas
# ---------------------------------------------------------------------------
TOOLS: list[Tool] = [
    Tool(
        name="pepe_chat",
        description=(
            "Envia uma mensagem ao agente Pepe e recebe a resposta. "
            "O agente possui memória de contexto por sessão, acesso a busca web, "
            "clima, visão, comandos e sistema de arquivos. "
            "Use session_id para manter conversas separadas."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensagem ou pergunta para o Pepe.",
                },
                "session_id": {
                    "type": "string",
                    "description": "ID da sessão (padrão: 'default').",
                    "default": "default",
                },
            },
            "required": ["message"],
        },
    ),
    Tool(
        name="pepe_web_search",
        description=(
            "Realiza uma busca na web usando DuckDuckGo ou Perplexity. "
            "Retorna resultados com título, URL e trecho."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Termo ou pergunta a ser pesquisada.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Número máximo de resultados (padrão: 5).",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="pepe_weather",
        description="Retorna informações de clima para uma cidade.",
        inputSchema={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Nome da cidade (ex: 'São Paulo', 'Magé').",
                },
            },
            "required": ["city"],
        },
    ),
    Tool(
        name="pepe_execute_command",
        description=(
            "Executa um comando de shell no sistema e retorna stdout + stderr. "
            "⚠️ Use com cuidado — executa no sistema real."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Comando a executar (ex: 'git status', 'python --version').",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout em segundos (padrão: 30).",
                    "default": 30,
                },
            },
            "required": ["command"],
        },
    ),
    Tool(
        name="pepe_read_file",
        description="Lê e retorna o conteúdo de um arquivo do sistema.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Caminho absoluto ou relativo do arquivo.",
                },
                "encoding": {
                    "type": "string",
                    "description": "Encoding do arquivo (padrão: 'utf-8').",
                    "default": "utf-8",
                },
            },
            "required": ["path"],
        },
    ),
    Tool(
        name="pepe_write_file",
        description="Escreve conteúdo em um arquivo do sistema (cria ou sobrescreve).",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Caminho do arquivo a escrever.",
                },
                "content": {
                    "type": "string",
                    "description": "Conteúdo a escrever no arquivo.",
                },
                "encoding": {
                    "type": "string",
                    "description": "Encoding (padrão: 'utf-8').",
                    "default": "utf-8",
                },
            },
            "required": ["path", "content"],
        },
    ),
    Tool(
        name="pepe_list_files",
        description="Lista arquivos e diretórios em um caminho.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Diretório a listar (padrão: diretório atual).",
                    "default": ".",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Listar recursivamente (padrão: false).",
                    "default": False,
                },
            },
        },
    ),
    Tool(
        name="pepe_capture_screen",
        description=(
            "Captura a tela atual e analisa usando Ollama Vision. "
            "Útil para entender o que está sendo exibido na tela."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Pergunta sobre a tela (ex: 'O que está aberto?').",
                    "default": "O que está sendo exibido na tela?",
                },
            },
        },
    ),
    Tool(
        name="pepe_memory_search",
        description=(
            "Busca na memória de longo prazo do Pepe (ChromaDB). "
            "Retorna conversas e informações relevantes armazenadas."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Termo ou frase para buscar na memória.",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Número de resultados (padrão: 5).",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="pepe_list_sessions",
        description="Lista todas as sessões de agente ativas no momento.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="pepe_delete_session",
        description="Remove uma sessão de agente específica, limpando o histórico de contexto.",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "ID da sessão a remover.",
                },
            },
            "required": ["session_id"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    """Roteador principal de chamadas de ferramentas."""
    try:
        match name:
            case "pepe_chat":            return await _handle_chat(arguments)
            case "pepe_web_search":      return await _handle_web_search(arguments)
            case "pepe_weather":         return await _handle_weather(arguments)
            case "pepe_execute_command": return await _handle_execute(arguments)
            case "pepe_read_file":       return await _handle_read_file(arguments)
            case "pepe_write_file":      return await _handle_write_file(arguments)
            case "pepe_list_files":      return await _handle_list_files(arguments)
            case "pepe_capture_screen":  return await _handle_capture_screen(arguments)
            case "pepe_memory_search":   return await _handle_memory_search(arguments)
            case "pepe_list_sessions":   return await _handle_list_sessions(arguments)
            case "pepe_delete_session":  return await _handle_delete_session(arguments)
            case _:
                return [TextContent(type="text", text=f"❌ Ferramenta desconhecida: {name}")]
    except Exception as exc:
        return [TextContent(type="text", text=f"❌ Erro em '{name}': {exc}")]


# ---------------------------------------------------------------------------
# Implementações individuais
# ---------------------------------------------------------------------------

async def _handle_chat(args: dict) -> list[TextContent]:
    message = args.get("message", "").strip()
    session_id = args.get("session_id", "default")
    if not message:
        return [TextContent(type="text", text="❌ Mensagem vazia.")]
    loop = asyncio.get_event_loop()
    agente = _get_agent(session_id)
    resposta = await loop.run_in_executor(None, agente.perguntar, message)
    return [TextContent(type="text", text=resposta)]


async def _handle_web_search(args: dict) -> list[TextContent]:
    query = args.get("query", "").strip()
    max_results = int(args.get("max_results", 5))
    if not query:
        return [TextContent(type="text", text="❌ Query vazia.")]
    # Tenta ferramenta_busca (nome real no core/tools.py)
    try:
        from core.tools import ferramenta_busca as _busca
    except ImportError:
        try:
            from core.tools import buscar_web as _busca
        except ImportError:
            return [TextContent(type="text", text="❌ Função de busca não encontrada em core/tools.py.")]
    loop = asyncio.get_event_loop()
    resultados = await loop.run_in_executor(None, _busca, query, max_results)
    if not resultados:
        return [TextContent(type="text", text="Nenhum resultado encontrado.")]
    linhas = [f"🔍 Resultados para: **{query}**\n"]
    for i, r in enumerate(resultados, 1):
        titulo = r.get("title", "Sem título")
        url = r.get("href", r.get("url", ""))
        trecho = r.get("body", r.get("snippet", ""))[:300]
        linhas.append(f"**{i}. {titulo}**\n{url}\n{trecho}\n")
    return [TextContent(type="text", text="\n".join(linhas))]


async def _handle_weather(args: dict) -> list[TextContent]:
    city = args.get("city", "").strip()
    if not city:
        return [TextContent(type="text", text="❌ Cidade não informada.")]
    # Tenta consulta_clima (nome real) ou buscar_clima (alias)
    try:
        from core.tools import consulta_clima as _clima
    except ImportError:
        try:
            from core.tools import buscar_clima as _clima
        except ImportError:
            return [TextContent(type="text", text="❌ Função de clima não encontrada em core/tools.py.")]
    loop = asyncio.get_event_loop()
    resultado = await loop.run_in_executor(None, _clima, city)
    return [TextContent(type="text", text=str(resultado))]


async def _handle_execute(args: dict) -> list[TextContent]:
    command = args.get("command", "").strip()
    timeout = int(args.get("timeout", 30))
    if not command:
        return [TextContent(type="text", text="❌ Comando vazio.")]
    from core.tools_execute import executar_comando
    loop = asyncio.get_event_loop()
    resultado = await loop.run_in_executor(None, executar_comando, command, timeout)
    return [TextContent(type="text", text=str(resultado))]


async def _handle_read_file(args: dict) -> list[TextContent]:
    path = args.get("path", "").strip()
    encoding = args.get("encoding", "utf-8")
    if not path:
        return [TextContent(type="text", text="❌ Caminho não informado.")]
    try:
        from core.tools_filesystem import ler_arquivo
        loop = asyncio.get_event_loop()
        # Tenta com encoding; se a função não aceitar, chama sem
        try:
            conteudo = await loop.run_in_executor(None, ler_arquivo, path, encoding)
        except TypeError:
            conteudo = await loop.run_in_executor(None, ler_arquivo, path)
        return [TextContent(type="text", text=conteudo)]
    except FileNotFoundError:
        return [TextContent(type="text", text=f"❌ Arquivo não encontrado: {path}")]


async def _handle_write_file(args: dict) -> list[TextContent]:
    path = args.get("path", "").strip()
    content = args.get("content", "")
    encoding = args.get("encoding", "utf-8")
    if not path:
        return [TextContent(type="text", text="❌ Caminho não informado.")]
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding=encoding)
        return [TextContent(type="text", text=f"✅ Arquivo salvo: {path}")]
    except Exception as exc:
        return [TextContent(type="text", text=f"❌ Erro ao salvar: {exc}")]


async def _handle_list_files(args: dict) -> list[TextContent]:
    path = args.get("path", ".")
    recursive = bool(args.get("recursive", False))
    try:
        from core.tools_filesystem import listar_arquivos
        loop = asyncio.get_event_loop()
        resultado = await loop.run_in_executor(None, listar_arquivos, path, recursive)
        return [TextContent(type="text", text=str(resultado))]
    except Exception as exc:
        return [TextContent(type="text", text=f"❌ Erro ao listar: {exc}")]


async def _handle_capture_screen(args: dict) -> list[TextContent]:
    question = args.get("question", "O que está sendo exibido na tela?")
    # Tenta capturar_e_analisar_tela (nome real) ou capturar_e_analisar (alias)
    try:
        from core.tools_vision import capturar_e_analisar_tela as _visao
    except ImportError:
        try:
            from core.tools_vision import capturar_e_analisar as _visao
        except ImportError:
            return [TextContent(type="text", text="❌ Função de visão não encontrada em core/tools_vision.py.")]
    loop = asyncio.get_event_loop()
    resultado = await loop.run_in_executor(None, _visao, question)
    return [TextContent(type="text", text=str(resultado))]


async def _handle_memory_search(args: dict) -> list[TextContent]:
    query = args.get("query", "").strip()
    n_results = int(args.get("n_results", 5))
    if not query:
        return [TextContent(type="text", text="❌ Query vazia.")]
    try:
        import chromadb
        db_path = str(PEPE_ROOT / "memory" / "data")
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection("pepe_memory")
        results = collection.query(query_texts=[query], n_results=n_results)
        docs = results.get("documents", [[]])[0]
        if not docs:
            return [TextContent(type="text", text="Nenhuma memória encontrada.")]
        linhas = [f"🧠 Memórias relevantes para: **{query}**\n"]
        for i, doc in enumerate(docs, 1):
            linhas.append(f"**{i}.** {doc}\n")
        return [TextContent(type="text", text="\n".join(linhas))]
    except Exception as exc:
        return [TextContent(type="text", text=f"❌ Erro ao buscar memória: {exc}")]


async def _handle_list_sessions(args: dict) -> list[TextContent]:
    _cleanup_sessions()
    if not _agents:
        return [TextContent(type="text", text="Nenhuma sessão ativa.")]
    now = time.time()
    linhas = ["📋 **Sessões ativas:**\n"]
    for sid, ts in _sessions_ts.items():
        idade = int(now - ts)
        linhas.append(f"• `{sid}` — ativa há {idade}s")
    return [TextContent(type="text", text="\n".join(linhas))]


async def _handle_delete_session(args: dict) -> list[TextContent]:
    session_id = args.get("session_id", "").strip()
    if not session_id:
        return [TextContent(type="text", text="❌ session_id não informado.")]
    if session_id in _agents:
        del _agents[session_id]
        _sessions_ts.pop(session_id, None)
        return [TextContent(type="text", text=f"✅ Sessão '{session_id}' removida.")]
    return [TextContent(type="text", text=f"❌ Sessão '{session_id}' não encontrada.")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
