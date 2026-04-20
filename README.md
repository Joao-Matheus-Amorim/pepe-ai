# Pepe AI

Agente pessoal em Python com foco em conversa contextual, LLM local via Ollama e ferramentas de busca web.

## Status atual

Este repositório esta em fase de nucleo funcional.

Ja implementado:
- Chat em terminal com contexto por sessao
- Integracao com LLM local via Ollama
- Roteamento simples para consultas de clima e busca web
- Suite de testes unitarios para nucleo de agente e LLM

Planejado (nao implementado ainda):
- Memoria persistente de longo prazo (vetorial)
- Voz (entrada e saida)
- Multiagentes
- Integracoes externas (email, WhatsApp, calendario)

## Arquitetura atual

Fluxo principal:
1. Usuario envia pergunta pelo terminal
2. `PepeAgent` classifica intencao (clima, busca web, resposta geral)
3. Para perguntas gerais, o agente usa cadeia LangChain com historico de sessao
4. Para clima/busca, usa ferramentas em `core/tools.py`

Arquivos principais:
- `main.py`: entrada da aplicacao
- `core/agent.py`: logica do agente e historico
- `core/llm.py`: selecao de provider e criacao do cliente de LLM
- `core/tools.py`: ferramentas de busca e clima
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
  tests/
    test_core_agent.py
    test_core_llm.py
  docs/
  main.py
  requirements.txt
  .env.example
```

## Licenca

MIT
