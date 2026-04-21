"""Pepe API
API REST para expor o agente.
"""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.agent import PepeAgent


app = FastAPI(title="Pepe AI", version="1.0.0")
_agents = {}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Autenticação
PEPE_API_KEY = os.getenv("PEPE_API_KEY", "pepe-default-key")

async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verifica API key nos headers."""
    if x_api_key != PEPE_API_KEY:
        raise HTTPException(status_code=403, detail="API key inválida.")
    return x_api_key


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str


class SessionInfo(BaseModel):
    session_id: str
    created_at: float


# Gerenciamento de sessões com cleanup
import time
_sessions_timestamp = {}  # session_id -> timestamp
MAX_SESSION_AGE = 3600  # 1 hora em segundos


def _cleanup_old_sessions():
    """Remove sessões com mais de MAX_SESSION_AGE segundos."""
    current_time = time.time()
    expired = [
        sid for sid, created_at in _sessions_timestamp.items()
        if current_time - created_at > MAX_SESSION_AGE
    ]
    for sid in expired:
        if sid in _agents:
            del _agents[sid]
        del _sessions_timestamp[sid]


def _get_agent(session_id: str | None) -> PepeAgent:
    """Obtém ou cria agente para uma sessão."""
    _cleanup_old_sessions()
    
    sid = session_id or "pepe-default"
    if sid not in _agents:
        _agents[sid] = PepeAgent(session_id=sid)
        _sessions_timestamp[sid] = time.time()
    return _agents[sid]


@app.get("/health")
async def health(api_key: str = Depends(verify_api_key)) -> dict:
    """Health check do servidor."""
    return {"status": "ok", "service": "pepe-ai"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, api_key: str = Depends(verify_api_key)) -> ChatResponse:
    """Endpoint de chat."""
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Mensagem vazia.")

    agente = _get_agent(req.session_id)
    resposta = agente.perguntar(message)
    return ChatResponse(response=resposta)


@app.get("/sessions", response_model=list[SessionInfo])
async def list_sessions(api_key: str = Depends(verify_api_key)) -> list[SessionInfo]:
    """Lista sessões ativas."""
    _cleanup_old_sessions()
    return [
        SessionInfo(session_id=sid, created_at=_sessions_timestamp.get(sid, time.time()))
        for sid in _agents.keys()
    ]


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, api_key: str = Depends(verify_api_key)) -> dict:
    """Remove uma sessão específica."""
    if session_id in _agents:
        del _agents[session_id]
        if session_id in _sessions_timestamp:
            del _sessions_timestamp[session_id]
        return {"message": f"Sessão '{session_id}' removida."}
    raise HTTPException(status_code=404, detail="Sessão não encontrada.")
