# 🧠 Arquitetura do Pepê

## Visão Geral

```
┌────────────────────────────────────────────┐
│            INTERFACE DO USUÁRIO                │
│     Texto (terminal) | Voz (Whisper+TTS)       │
└─────────────────────┬─────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────┐
│              AGENTE PRINCIPAL (LangGraph)      │
│  Plan → Act → Observe → Evaluate → Improve     │
└───────┬─────────┬─────────┬─────────┬────────┘
         │         │         │         │
         ▼         ▼         ▼         ▼
                  [LLM]   [Memória] [Ferramentas] [Subagentes]
            Ollama    ChromaDB   Busca/Agenda  Pesquisador
            Local     Vetorial   Código/Files  Programador
                                       Planejador
                                         Crítico
```

## Ciclo de Autoaperfeiçoamento

```
[ Input ] → [ Planejar ] → [ Executar ] → [ Avaliar ]
                                               │
                    ⬅ Insatisfatório ⬅───────┘
                    │
              [ Satisfatório ]
                    │
              [ Responder + Salvar na Memória ]
```

## Fluxo de Memória

| Tipo | Tecnologia | Descrição |
|------|-----------|----------|
| Curto prazo | Lista Python | Contexto da sessão atual |
| Longo prazo | ChromaDB | Conversas e fatos persistentes |
| Perfil | JSON/ChromaDB | Preferências e dados do usuário |

## Fases de Evolução

Cada fase adiciona uma camada de capacidade ao Pepê, sem quebrar o que já existe. O projeto segue princípios de arquitetura modular para facilitar a evolução gradual.
