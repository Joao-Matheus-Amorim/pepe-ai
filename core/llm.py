import os
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_PROVIDERS = {"ollama", "perplexity", "anthropic", "groq", "openrouter"}
PROVIDER_ALIASES = {
    "claude": "anthropic",
    "llama": "ollama",
    "mixtral": "groq",
    "groq": "groq",
    "openrouter": "openrouter",
}

VALID_ANTHROPIC_MODELS = {
    "claude-opus-4-20251120",
    "claude-sonnet-4-20250514",
    "claude-3-opus-latest",
    "claude-3-5-sonnet-latest",
}


def _obter_provider(provider: str | None = None) -> str:
    valor = (provider or os.getenv("PEPE_MODEL_PROVIDER", "ollama")).strip().lower()
    valor = PROVIDER_ALIASES.get(valor, valor)
    if valor not in SUPPORTED_PROVIDERS:
        providers = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise ValueError(
            f"PEPE_MODEL_PROVIDER invalido: '{valor}'."
            f" Providers suportados: {providers}."
        )
    return valor


def _criar_cliente_ollama(modelo: str, temperatura: float):
    try:
        from langchain_ollama import ChatOllama
    except ImportError as erro:
        raise RuntimeError(
            "Dependência ausente para Ollama. Instale 'langchain-ollama'."
        ) from erro

    return ChatOllama(model=modelo, temperature=temperatura)


def _criar_cliente_perplexity(modelo: str, temperatura: float):
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as erro:
        raise RuntimeError(
            "Dependência ausente para Perplexity. Instale 'langchain-openai'."
        ) from erro

    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente PERPLEXITY_API_KEY não foi definida.")

    return ChatOpenAI(
        model=modelo,
        temperature=temperatura,
        openai_api_key=api_key,
        openai_api_base="https://api.perplexity.ai",
    )


def _criar_cliente_anthropic(modelo: str, temperatura: float):
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as erro:
        raise RuntimeError(
            "Dependência ausente para Anthropic. Instale 'langchain-anthropic'."
        ) from erro

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente ANTHROPIC_API_KEY não foi definida.")

    return ChatAnthropic(
        model=modelo,
        temperature=temperatura,
        anthropic_api_key=api_key,
    )


def _criar_cliente_groq(modelo: str, temperatura: float):
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as erro:
        raise RuntimeError(
            "Dependência ausente para Groq. Instale 'langchain-openai'."
        ) from erro

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente GROQ_API_KEY não foi definida.")

    return ChatOpenAI(
        model=modelo,
        temperature=temperatura,
        openai_api_key=api_key,
        openai_api_base="https://api.groq.com/openai/v1",
    )


def _criar_cliente_openrouter(modelo: str, temperatura: float):
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as erro:
        raise RuntimeError(
            "Dependência ausente para OpenRouter. Instale 'langchain-openai'."
        ) from erro

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente OPENROUTER_API_KEY não foi definida.")

    return ChatOpenAI(
        model=modelo,
        temperature=temperatura,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/pepe-ai",
            "X-Title": "Pepe AI",
        },
    )


def criar_llm(provider: str | None = None, modelo: str | None = None, temperatura: float = 0.4):
    provider_final = _obter_provider(provider)

    if provider_final == "perplexity":
        modelo_perplexity = (modelo or os.getenv("PEPE_PERPLEXITY_MODEL", "sonar-reasoning")).strip()
        return _criar_cliente_perplexity(modelo_perplexity, temperatura)

    if provider_final == "openrouter":
        modelo_openrouter = (modelo or os.getenv("PEPE_OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")).strip()
        return _criar_cliente_openrouter(modelo_openrouter, temperatura)

    if provider_final == "groq":
        modelo_groq = (modelo or os.getenv("PEPE_GROQ_MODEL", "llama-3.3-70b-versatile")).strip()
        return _criar_cliente_groq(modelo_groq, temperatura)

    if provider_final == "anthropic":
        modelo_anthropic = (modelo or os.getenv("PEPE_ANTHROPIC_MODEL", "claude-sonnet-4-20250514")).strip()
        return _criar_cliente_anthropic(modelo_anthropic, temperatura)

    modelo_ollama = (modelo or os.getenv("PEPE_OLLAMA_MODEL", "llama3.1")).strip()
    return _criar_cliente_ollama(modelo_ollama, temperatura)


if __name__ == "__main__":
    llm = criar_llm()
    resposta = llm.invoke("Olá! Quem é você?")
    print(resposta.content)