# 🤖 Pepê — Personal AI Agent

> *"Não é um chatbot. É um parceiro inteligente que aprende, evolui e trabalha por você."*

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-latest-green)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Em%20Construção-orange)]()

---

## 🎯 Propósito

**Pepê** é um agente de IA pessoal, autônomo e evolutivo — criado para ser o assistente definitivo do seu criador. Diferente de assistentes comuns, Pepê:

- 🧠 **Aprende sozinho** — avalia as próprias respostas e melhora continuamente
- 💾 **Lembra de tudo** — memória de longo prazo persistente entre sessões
- 🗣️ **Fala e ouve** — interface por voz completa, sem depender de nuvem
- ⚙️ **Age no mundo real** — executa tarefas, pesquisa, agenda, envia mensagens
- 🤝 **Multiagente** — subagentes especializados colaborando internamente
- 💰 **100% gratuito** — stack open-source, sem dependências pagas

---

## 🗺️ Roadmap

| Fase | Nome | Status | Descrição |
|------|------|--------|-----------|
| **1** | Núcleo | 🔄 Em andamento | Agente base com voz, LLM e ferramentas |
| **2** | Memória | ⏳ Planejado | Memória vetorial persistente e perfil do usuário |
| **3** | Autonomia | ⏳ Planejado | Loop de auto-avaliação e planejamento complexo |
| **4** | Personalidade | ⏳ Planejado | Fine-tuning com estilo e dados pessoais |
| **5** | Multiagente | ⏳ Planejado | Subagentes: Pesquisador, Programador, Planejador, Crítico |
| **6** | Integração | ⏳ Planejado | WhatsApp, e-mail, calendário, casa inteligente |

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Descrição |
|--------|-----------|-----------|
| **Linguagem** | Python 3.11+ | Base do projeto |
| **Cérebro (LLM)** | Gemini 2.0 Flash + Ollama | LLM gratuito local e em nuvem |
| **Modelo local** | Llama 3 / Mistral | Roda 100% offline via Ollama |
| **Orquestração** | LangGraph | Controle de fluxo e estados do agente |
| **Memória vetorial** | ChromaDB | Banco de memória local e gratuito |
| **Fine-tuning** | LoRA + Hugging Face + Colab | Treinamento gratuito na nuvem |
| **Voz entrada** | Whisper (OpenAI OSS) | Reconhecimento de voz offline |
| **Voz saída** | pyttsx3 / Coqui TTS | Síntese de voz offline |
| **Busca web** | DuckDuckGo API | Pesquisa sem custo |
| **Automações** | n8n self-hosted | Integrações e workflows |
| **Monitoramento** | LangSmith (free tier) | Observabilidade do agente |

---

## 📁 Estrutura do Projeto

```
pepe-ai/
│
├── core/               # Núcleo do agente (LangGraph)
│   ├── agent.py        # Agente principal
│   ├── graph.py        # Grafo de estados e fluxo
│   └── prompts.py      # Prompts e personalidade do Pepê
│
├── memory/             # Sistema de memória
│   ├── short_term.py   # Memória de sessão
│   ├── long_term.py    # Memória vetorial persistente (ChromaDB)
│   └── profile.py      # Perfil e preferências do usuário
│
├── tools/              # Ferramentas disponíveis ao agente
│   ├── search.py       # Busca na web (DuckDuckGo)
│   ├── calendar.py     # Integração com agenda
│   ├── code.py         # Execução de código
│   └── files.py        # Leitura e escrita de arquivos
│
├── voice/              # Interface de voz
│   ├── listener.py     # Entrada de voz (Whisper)
│   └── speaker.py      # Saída de voz (pyttsx3/Coqui)
│
├── agents/             # Subagentes especializados (Fase 5)
│   ├── researcher.py   # Agente pesquisador
│   ├── coder.py        # Agente programador
│   ├── planner.py      # Agente planejador
│   └── critic.py       # Agente crítico/avaliador
│
├── training/           # Fine-tuning e treinamento
│   ├── datasets/       # Dados de treinamento
│   ├── finetune.py     # Script de fine-tuning com LoRA
│   └── evaluate.py     # Avaliação do modelo treinado
│
├── integrations/       # Integrações externas (Fase 6)
│   ├── whatsapp.py
│   ├── email.py
│   └── n8n/
│
├── docs/               # Documentação detalhada
│   ├── setup.md        # Guia de instalação
│   ├── architecture.md # Arquitetura do sistema
│   └── phases/         # Documentação por fase
│
├── tests/              # Testes automatizados
├── .env.example        # Variáveis de ambiente (modelo)
├── requirements.txt    # Dependências Python
└── README.md
```

---

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.11+
- Git
- [Ollama](https://ollama.com) (para LLM local)
- Conta no [Google AI Studio](https://aistudio.google.com) (API gratuita)

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/Joao-Matheus-Amorim/pepe-ai.git
cd pepe-ai

# 2. Crie o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com sua chave da API do Google AI Studio

# 5. Baixe o modelo local
ollama pull llama3

# 6. Inicie o Pepê
python main.py
```

---

## 🧠 Como o Pepê Aprende

```
[ Você fala/escreve ]
        ↓
  [ Pepê recebe a tarefa ]
        ↓
  [ Consulta memória de longo prazo ]
        ↓
  [ Planeja a ação ]
        ↓
  [ Executa com ferramentas ]
        ↓
  [ Auto-avalia o resultado ]
        ↓
  ¿Satisfatório? → NÃO → Reescreve estratégia → Repete
        ↓ SIM
  [ Responde + Salva aprendizado na memória ]
```

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 👤 Autor

**João Matheus Amorim**
- GitHub: [@Joao-Matheus-Amorim](https://github.com/Joao-Matheus-Amorim)
- Email: joaomatheus.lab@gmail.com

---

> *"Este é um projeto de vida. Cada commit é um passo em direção a um futuro onde a tecnologia trabalha para as pessoas, não o contrário."*
