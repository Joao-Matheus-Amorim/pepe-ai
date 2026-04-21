# 🔐 Segurança - Pepe AI

## Revisão de Segurança Implementada (21/04/2026)

Este documento descreve as melhorias de segurança implementadas no projeto Pepe AI baseado em análise de código.

---

## ✅ Problemas Resolvidos

### Prioridade Alta

#### 1. **Proteção de Secrets** ✅
- **Status**: ✅ RESOLVIDO
- **Verificação**: `.env` está corretamente no `.gitignore`
- **Ação**: Confirmado que segredos (API keys, senhas) nunca serão commitados
- **Detalhes**: 
  ```
  # .gitignore contém:
  .env                          # Arquivo de configuração local
  memory/perplexity-profile/    # Cache com credenciais
  .pytest_cache/                # Cache de testes
  ```

#### 2. **Autenticação na API REST** ✅
- **Status**: ✅ IMPLEMENTADO
- **Solução**: API key via header `X-API-Key`
- **Implementação**:
  ```python
  # Todos endpoints agora requerem autenticação
  @app.post("/chat")
  async def chat(req: ChatRequest, 
                 api_key: str = Depends(verify_api_key)) -> ChatResponse:
  ```
- **Configuração**: `PEPE_API_KEY` no `.env` (obrigatório em produção)
- **Endpoints Protegidos**:
  - `GET /health` → Requer API key
  - `POST /chat` → Requer API key
  - `GET /sessions` → Requer API key
  - `DELETE /sessions/{session_id}` → Requer API key

#### 3. **Memory Leak em Sessions** ✅
- **Status**: ✅ IMPLEMENTADO
- **Problema**: `_agents` dict nunca limpava sessões antigas
- **Solução**: Auto-cleanup de sessões com TTL de 1 hora
- **Implementação**:
  ```python
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
  ```
- **Monitoramento**: Cleanup executado automaticamente em cada requisição

### Prioridade Média

#### 4. **Endpoints Assíncronos** ✅
- **Status**: ✅ IMPLEMENTADO
- **Detalhes**: Todos endpoints convertidos para `async def`
- **Benefícios**: 
  - Melhor handling de I/O
  - Melhor performance em alta concorrência
  - Padrão moderno FastAPI
- **Endpoints**:
  ```python
  async def health(...)
  async def chat(...)
  async def list_sessions(...)
  async def delete_session(...)
  ```

#### 5. **Configurações Documentadas** ✅
- **Status**: ✅ IMPLEMENTADO
- **Arquivo**: `.env.example` atualizado
- **Novas Variáveis**:
  ```env
  PEPE_API_KEY=sua-chave-secreta-aqui-mudanca-obrigatoria
  PEPE_API_PORT=8000
  PEPE_API_HOST=0.0.0.0
  ```

#### 6. **Novos Endpoints** ✅
- **Status**: ✅ IMPLEMENTADO
- **Endpoints Adicionados**:
  - `GET /sessions` → Lista todas as sessões ativas
  - `DELETE /sessions/{session_id}` → Remove uma sessão específica

### Prioridade Baixa

#### 7. **Dependências Adicionadas** ✅
- **Status**: ✅ IMPLEMENTADO
- **Pacotes Adicionados**:
  - `playwright>=1.40.0` → Browser automation
  - `ruff>=0.3.0` → Code linter e formatter

#### 8. **Configuração de Linting** ✅
- **Status**: ✅ IMPLEMENTADO
- **Arquivo**: `pyproject.toml` criado
- **Regras**: 
  - E, F, W (erros, falhas, warnings básicos)
  - I (import sorting)
  - N (naming conventions)
  - UP (code upgrades)
  - B (bugbear)
- **Line Length**: 100 caracteres
- **Python Target**: 3.11+

---

## 🚀 Como Usar em Produção

### 1. Configurar API Key

```bash
# Gerar chave segura (exemplo)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

```env
# .env (NUNCA commitar!)
PEPE_API_KEY=seu-token-aleatorio-seguro-aqui
PEPE_API_HOST=0.0.0.0
PEPE_API_PORT=8000
```

### 2. Usar a API com Autenticação

```bash
# Requisição com API key
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: sua-chave-aqui" \
  -H "Content-Type: application/json" \
  -d '{"message": "Oi!", "session_id": "user123"}'
```

### 3. Gerenciar Sessões

```bash
# Listar todas as sessões
curl http://localhost:8000/sessions \
  -H "X-API-Key: sua-chave-aqui"

# Remover uma sessão específica
curl -X DELETE http://localhost:8000/sessions/user123 \
  -H "X-API-Key: sua-chave-aqui"
```

---

## 📋 Checklist de Segurança

- [x] API protegida com autenticação
- [x] Sessões limpas automaticamente
- [x] .env não vai para repositório
- [x] Endpoints convertidos para async
- [x] Configurações documentadas
- [x] Code linting configurado
- [x] Browser automation pronto (playwright)
- [x] Testes passando (20/20)

---

## ⚠️ Recomendações Adicionais

### Para Produção

1. **Use HTTPS**: Sempre use TLS/SSL em produção
2. **Rate Limiting**: Adicionar rate limiting por IP/API key
3. **CORS**: Configurar CORS appropriately para seus clientes
4. **Logging**: Implementar audit logging de todas as requisições
5. **Backup**: Manter backup do ChromaDB em `memory/data/`
6. **Secrets Management**: Use um secrets manager (ex: Vault, AWS Secrets)

### Para Desenvolvimento

1. Sempre usar `.env` local (nunca commitar)
2. Usar chaves de teste diferentes em dev vs prod
3. Testar rate limiting antes de deploy
4. Verificar logs regularmente

---

## 📝 Histórico de Mudanças

| Data | Mudança | Status |
|------|---------|--------|
| 21/04/2026 | Autenticação API | ✅ |
| 21/04/2026 | Cleanup de sessões | ✅ |
| 21/04/2026 | Endpoints async | ✅ |
| 21/04/2026 | Playwright + Ruff | ✅ |
| 21/04/2026 | pyproject.toml | ✅ |

---

## 📞 Suporte

Para dúvidas sobre segurança, revise:
- `.env.example` para variáveis de configuração
- `api_main.py` para implementação de autenticação
- `pyproject.toml` para regras de linting
