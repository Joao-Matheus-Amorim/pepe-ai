import os
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_PROVIDERS = {"ollama", "perplexity"}


def _obter_provider(provider: str | None = None) -> str:
    valor = (provider or os.getenv("PEPE_MODEL_PROVIDER", "ollama")).strip().lower()
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


def criar_llm(provider: str | None = None, modelo: str | None = None, temperatura: float = 0.4):
    provider_final = _obter_provider(provider)

    if provider_final == "perplexity":
        modelo_perplexity = (modelo or os.getenv("PEPE_PERPLEXITY_MODEL", "sonar-reasoning")).strip()
        return _criar_cliente_perplexity(modelo_perplexity, temperatura)

    modelo_ollama = (modelo or os.getenv("PEPE_OLLAMA_MODEL", "llama3.1")).strip()
    return _criar_cliente_ollama(modelo_ollama, temperatura)


if __name__ == "__main__":
    llm = criar_llm()
    resposta = llm.invoke("Olá! Quem é você?")
    print(resposta.content)