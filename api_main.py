"""Pepe API
API REST para expor o agente.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.agent import PepeAgent


app = FastAPI(title="Pepe AI", version="1.0.0")
_agents = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str


def _get_agent(session_id: str | None) -> PepeAgent:
    sid = session_id or "pepe"
    if sid not in _agents:
        _agents[sid] = PepeAgent(session_id=sid)
    return _agents[sid]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Mensagem vazia.")

    agente = _get_agent(req.session_id)
    resposta = agente.perguntar(message)
    return ChatResponse(response=resposta)
