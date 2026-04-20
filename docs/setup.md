# Guia de Setup

## 1. Pre-requisitos

- Python 3.11+
- Git
- Ollama instalado e rodando localmente

## 2. Clonar e entrar no projeto

```bash
git clone https://github.com/Joao-Matheus-Amorim/pepe-ai.git
cd pepe-ai
```

## 3. Ambiente virtual

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Linux/Mac:
```bash
python -m venv venv
source venv/bin/activate
```

## 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 5. Configurar variaveis de ambiente

Windows:
```bash
copy .env.example .env
```

Linux/Mac:
```bash
cp .env.example .env
```

Configure o provider:

Ollama:
```env
PEPE_MODEL_PROVIDER=ollama
PEPE_OLLAMA_MODEL=llama3.1
```

## 6. Rodar a aplicacao

```bash
python main.py
```

## 7. Rodar testes

```bash
python -m unittest discover -s tests -v
```
