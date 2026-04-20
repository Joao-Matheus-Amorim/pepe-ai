from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

def criar_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

if __name__ == "__main__":
    llm = criar_llm()
    resposta = llm.invoke("Olá! Quem é você?")
    print(resposta.content)