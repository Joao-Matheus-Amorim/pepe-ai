import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def _obter_google_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY não encontrada. Configure o arquivo .env antes de iniciar o Pepê."
        )
    return api_key


def criar_llm(modelo: str | None = None, temperatura: float = 0.7):
    modelo_configurado = (modelo or os.getenv("PEPE_GEMINI_MODEL", "gemini-2.5-flash")).strip()
    return ChatGoogleGenerativeAI(
        model=modelo_configurado,
        temperature=temperatura,
        google_api_key=_obter_google_api_key(),
    )

if __name__ == "__main__":
    llm = criar_llm()
    resposta = llm.invoke("Olá! Quem é você?")
    print(resposta.content)