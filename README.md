# Pepe AI

Agente pessoal em Python com foco em conversa contextual, LLM local via Ollama e ferramentas de busca web.

## Status atual

Este repositório esta em fase de nucleo funcional expandido.

Ja implementado:
- Chat em terminal com contexto por sessao
- Integracao com LLM local via Ollama
- Memoria persistente de longo prazo (ChromaDB)
- Roteamento para clima, busca web e LLM
- Voz (entrada e saida)
- Visao local (captura de tela via Ollama Vision)
- Execucao de comandos e acesso ao filesystem
- Suite de testes unitarios para nucleo de agente e LLM
- API REST basica

Planejado (nao implementado ainda):
- Multiagentes
- Integracoes externas (email, WhatsApp, calendario)

## Arquitetura atual

Fluxo principal:
1. Usuario envia pergunta pelo terminal
2. `PepeAgent` classifica intencao (clima, busca web, visao, comandos, arquivos)
3. Para perguntas gerais, o agente usa cadeia LangChain com historico de sessao
4. Para clima/busca, usa ferramentas em `core/tools.py`
5. Para visao, comandos e filesystem, usa `core/tools_vision.py`, `core/tools_execute.py` e `core/tools_filesystem.py`

Arquivos principais:
- `main.py`: entrada da aplicacao
- `api_main.py`: API REST (FastAPI)
- `voice_main.py`: entrada modo voz
- `core/agent.py`: logica do agente e historico
- `core/llm.py`: selecao de provider e criacao do cliente de LLM
- `core/tools.py`: ferramentas de busca e clima
- `core/tools_execute.py`: execucao de comandos
- `core/tools_filesystem.py`: leitura e listagem de arquivos
- `core/tools_vision.py`: captura e analise de tela
- `tests/`: testes unitarios

## Requisitos

- Python 3.11+
- Dependencias em `requirements.txt`
- Ollama local ativo

## Configuracao

1. Crie o ambiente virtual:

```bash
python -m venv venv
venv\Scripts\activate
```

2. Instale dependencias:

```bash
pip install -r requirements.txt
```

3. Configure variaveis:

```bash
copy .env.example .env
```

4. Ajuste o `.env`:

Configuracao Ollama:
```env
PEPE_MODEL_PROVIDER=ollama
PEPE_OLLAMA_MODEL=llama3.1
```

## Execucao

```bash
python main.py
```

## Execucao (API)

```bash
uvicorn api_main:app --reload
```

## Execucao (Voz)

```bash
python voice_main.py
```

## Testes

```bash
python -m unittest discover -s tests -v
```

## Estrutura do repositorio

```text
pepe-ai/
  core/
    agent.py
    llm.py
    tools.py
    tools_execute.py
    tools_filesystem.py
    tools_vision.py
  voice/
    engine.py
  memory/
    data/
  tests/
    test_core_agent.py
    test_core_llm.py
  docs/
  main.py
  api_main.py
  voice_main.py
  requirements.txt
  .env.example
```

## Licenca

MIT
