import os
import ollama
from PIL import Image, ImageGrab
from loguru import logger

def capturar_e_analisar_tela(prompt_usuario: str = "O que você está vendo nesta tela? Seja breve e objetivo.") -> str:
    """Tira um print da tela e pede ao Llama 3.2 Vision local para analisar."""
    try:
        logger.info("Iniciando captura de tela local...")
        # 1. Tirar o print
        screenshot_path = "memory/last_screenshot.png"
        
        if not os.path.exists("memory"):
            os.makedirs("memory")
        
        # Tirar print usando PIL ImageGrab
        screenshot = ImageGrab.grab()
        screenshot.save(screenshot_path)
        logger.info(f"Screenshot salva em {screenshot_path}")

        # 2. Enviar para o Llama 3.2 Vision via Ollama
        logger.info("Iniciando análise LOCAL com Llama 3.2 Vision...")
        
        # O Ollama espera o caminho do arquivo ou bytes
        response = ollama.chat(
            model='llama3.2-vision',
            messages=[{
                'role': 'user',
                'content': prompt_usuario,
                'images': [screenshot_path]
            }]
        )
        
        logger.info("Análise local concluída!")
        return response['message']['content']

    except Exception as e:
        logger.error(f"FALHA NA VISÃO LOCAL: {str(e)}")
        if "not found" in str(e).lower():
            return "Estou terminando de instalar meus novos olhos locais. Tente novamente em 1 minuto!"
        return f"Erro ao tentar ver a tela localmente: {str(e)}"

if __name__ == "__main__":
    # Teste rápido
    print(capturar_e_analisar_tela())
