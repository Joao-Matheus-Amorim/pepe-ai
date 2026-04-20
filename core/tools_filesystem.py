import os
from loguru import logger

def ler_arquivo(caminho: str) -> str:
    """Lê o conteúdo de um arquivo no projeto."""
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Erro ao ler arquivo {caminho}: {e}")
        return f"Erro: {e}"

def escrever_arquivo(caminho: str, conteudo: str) -> str:
    """Cria ou sobrescreve um arquivo com o conteúdo fornecido."""
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        logger.info(f"Arquivo escrito com sucesso: {caminho}")
        return f"Sucesso: Arquivo {caminho} atualizado."
    except Exception as e:
        logger.error(f"Erro ao escrever arquivo {caminho}: {e}")
        return f"Erro: {e}"

def listar_arquivos(diretorio: str = ".") -> str:
    """Lista os arquivos em um diretório para dar contexto ao agente."""
    try:
        arquivos = []
        for root, dirs, files in os.walk(diretorio):
            # Ignorar pastas de ambiente virtual e git
            if any(x in root for x in ['venv', '.venv', '.git', '__pycache__']):
                continue
            for name in files:
                arquivos.append(os.path.join(root, name))
        return "\n".join(arquivos)
    except Exception as e:
        return f"Erro ao listar arquivos: {e}"
