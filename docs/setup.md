# 🚀 Guia de Instalação do Pepê

## Pré-requisitos

- Python 3.11+
- Git
- [Ollama](https://ollama.com) instalado
- Conta gratuita no [Google AI Studio](https://aistudio.google.com)

## Passo a Passo

### 1. Clone o repositório
```bash
git clone https://github.com/Joao-Matheus-Amorim/pepe-ai.git
cd pepe-ai
```

### 2. Crie o ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
cp .env.example .env
```
Edite o arquivo `.env` e adicione sua chave da API do Google AI Studio.

### 5. Baixe o modelo local (opcional)
```bash
ollama pull llama3
```

### 6. Inicie o Pepê
```bash
python main.py
```

## Obtendo a API Key do Google AI Studio (Grátis)

1. Acesse [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Copie e cole no seu arquivo `.env`

> ✅ O Gemini 2.0 Flash oferece 6 milhões de tokens por dia gratuitamente!
