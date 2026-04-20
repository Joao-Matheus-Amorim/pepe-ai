import os
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_PROVIDERS = {"ollama"}


def _obter_provider(provider: str | None = None) -> str:
    valor = (provider or os.getenv("PEPE_MODEL_PROVIDER", "ollama")).strip().lower()
    if valor not in SUPPORTED_PROVIDERS:
        providers = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise ValueError(
            f"PEPE_MODEL_PROVIDER invalido: '{valor}'."
            f" Neste projeto o unico provider suportado e: {providers}."
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


def criar_llm(provider: str | None = None, modelo: str | None = None, temperatura: float = 0.4):
    _obter_provider(provider)

    modelo_ollama = (modelo or os.getenv("PEPE_OLLAMA_MODEL", "llama3.1")).strip()
    return _criar_cliente_ollama(modelo_ollama, temperatura)


if __name__ == "__main__":
    llm = criar_llm()
    resposta = llm.invoke("Olá! Quem é você?")
    print(resposta.content)