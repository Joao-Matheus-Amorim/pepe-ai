from PIL import ImageGrab
import os

try:
    print("Tentando capturar tela...")
    screenshot = ImageGrab.grab()
    print(f"Tela capturada! Tamanho: {screenshot.size}")
    path = "memory/test_screenshot.png"
    os.makedirs("memory", exist_ok=True)
    screenshot.save(path)
    print(f"Salvo com sucesso em: {path}")
except Exception as e:
    print(f"ERRO CRÍTICO NA CAPTURA: {e}")
