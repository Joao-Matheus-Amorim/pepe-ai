import subprocess
import os
from loguru import logger

def executar_comando(comando: str) -> str:
    """Executa um comando no terminal do sistema e retorna o resultado."""
    try:
        logger.info(f"Pepê executando comando: {comando}")
        
        # Executa o comando e captura a saída
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60 # Timeout de 1 minuto para segurança
        )
        
        if resultado.returncode == 0:
            saida = resultado.stdout if resultado.stdout else "Comando executado com sucesso (sem saída)."
            logger.info("Comando executado com sucesso.")
            return saida
        else:
            erro = resultado.stderr if resultado.stderr else "Erro desconhecido."
            logger.error(f"Erro ao executar comando: {erro}")
            return f"Erro na execução:\n{erro}"
            
    except subprocess.TimeoutExpired:
        logger.error("O comando demorou demais e foi interrompido.")
        return "Erro: O comando demorou mais de 60 segundos e foi interrompido por segurança."
    except Exception as e:
        logger.error(f"Falha crítica na execução: {e}")
        return f"Falha ao tentar agir: {e}"

def criar_e_rodar_script(nome_arquivo: str, codigo: str) -> str:
    """Cria um arquivo Python temporário e o executa."""
    try:
        caminho = os.path.join("scratch", nome_arquivo)
        os.makedirs("scratch", exist_ok=True)
        
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(codigo)
        
        logger.info(f"Script criado em: {caminho}")
        return executar_comando(f"python {caminho}")
        
    except Exception as e:
        return f"Erro ao criar/rodar script: {e}"
