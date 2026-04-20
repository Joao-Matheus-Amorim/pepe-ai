import os
import chromadb
from chromadb.config import Settings
from loguru import logger

class PepeMemory:
    def __init__(self, persist_directory: str = "./memory/data"):
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name="pepe_long_term_memory")
        logger.info(f"Memória persistente iniciada em: {self.persist_directory}")

    def adicionar_fato(self, fato: str, metadata: dict = None):
        """Adiciona um fato ou informação à memória de longo prazo."""
        self.collection.add(
            documents=[fato],
            metadatas=[metadata or {}],
            ids=[f"fact_{os.urandom(4).hex()}"]
        )
        logger.info(f"Fato adicionado à memória: {fato[:50]}...")

    def buscar_fatos(self, consulta: str, n_resultados: int = 3):
        """Busca fatos relevantes na memória com base em uma consulta."""
        resultados = self.collection.query(
            query_texts=[consulta],
            n_results=n_resultados
        )
        return resultados["documents"][0] if resultados["documents"] else []

if __name__ == "__main__":
    # Teste simples
    mem = PepeMemory()
    mem.adicionar_fato("O usuário João Matheus prefere o tema escuro.")
    print(mem.buscar_fatos("Qual a preferência do João?"))
