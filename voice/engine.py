import pyttsx3
import speech_recognition as sr
from loguru import logger

class PepeVoice:
    """Motor de voz do Pepê (Sintetizador e Reconhecimento)."""

    def __init__(self) -> None:
        """Inicializa as configurações de áudio do sistema."""
        # Inicializa o motor de síntese de voz (TTS)
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        # Tenta encontrar uma voz em português
        for voice in self.voices:
            if "brazil" in voice.name.lower() or "portuguese" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', 180)  # Velocidade da fala
        
        # Inicializa o reconhecedor de fala (STT)
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
            logger.info("Sistema de escuta (STT) inicializado.")
        except Exception:
            self.microphone = None
            logger.warning("Microfone não disponível (PyAudio ausente). O Pepê só poderá falar, não ouvir.")
        
        logger.info("Sistema de voz do Pepê inicializado.")

    def falar(self, texto: str) -> None:
        """Faz o Pepê falar o texto fornecido."""
        logger.info(f"Pepê falando: {texto}")
        self.engine.say(texto)
        self.engine.runAndWait()

    def ouvir(self) -> str:
        """Ouvir o usuário pelo microfone e converter em texto."""
        if not self.microphone:
            logger.error("Tentativa de ouvir sem microfone (PyAudio ausente).")
            return ""

        with self.microphone as source:
            logger.info("Ouvindo...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
        
        try:
            texto = self.recognizer.recognize_google(audio, language='pt-BR')
            logger.info(f"Usuário disse: {texto}")
            return texto
        except sr.UnknownValueError:
            logger.warning("Não entendi o áudio.")
            return ""
        except sr.RequestError as e:
            logger.error(f"Erro no serviço de reconhecimento: {e}")
            return ""

if __name__ == "__main__":
    # Teste de voz
    pv = PepeVoice()
    pv.falar("Olá João Matheus! Estou pronto para ser o seu mestre em tudo.")


