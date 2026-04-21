"""
Pepe AI — Extrator de Skills de Vídeos

Transcreve vídeos com Whisper e converte automaticamente
em pares instruction/output para treinamento do Pepê.

Uso:
  # Extrai uma skill de um vídeo
  python training/extract_skills.py --video videos/skills/programacao/aula.mp4 --skill programacao

  # Processa todos os vídeos novos de uma skill
  python training/extract_skills.py --skill programacao

  # Processa todas as skills de uma vez
  python training/extract_skills.py --all

  # Modo watch: monitora a pasta e extrai automaticamente
  python training/extract_skills.py --watch
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
ROOT         = Path(__file__).resolve().parent.parent
VIDEOS_DIR   = ROOT / "videos" / "skills"
SKILLS_DIR   = ROOT / "training" / "skills"
PROCESSED_DB = ROOT / "training" / "skills" / ".processed.json"

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_EXTS = {".mp4", ".mp3", ".wav", ".m4a", ".mkv", ".avi", ".mov", ".webm"}

SYSTEM_PEPE = (
    "Você é Pepê, um agente de IA pessoal inteligente, direto e eficiente. "
    "Você tem acesso a ferramentas de busca web, clima, visão de tela, execução de comandos, "
    "leitura de arquivos e memória persistente. "
    "Responda sempre em português do Brasil, de forma clara e concisa."
)

# ---------------------------------------------------------------------------
# Banco de arquivos já processados (evita reprocessar)
# ---------------------------------------------------------------------------

def load_processed() -> dict:
    if PROCESSED_DB.exists():
        return json.loads(PROCESSED_DB.read_text(encoding="utf-8"))
    return {}


def save_processed(db: dict) -> None:
    PROCESSED_DB.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Transcrição com Whisper
# ---------------------------------------------------------------------------

def check_whisper() -> bool:
    try:
        import whisper  # noqa
        return True
    except ImportError:
        return False


def install_whisper() -> None:
    print("  ▶  Instalando openai-whisper...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "openai-whisper"], check=True)
    print("  ✓  Whisper instalado")


def transcrever(video_path: Path, model_size: str = "base") -> str:
    """Transcreve áudio/vídeo usando Whisper local."""
    if not check_whisper():
        install_whisper()

    import whisper
    print(f"  ▶  Transcrevendo {video_path.name} (modelo: {model_size})...")
    model = whisper.load_model(model_size)
    result = model.transcribe(str(video_path), language="pt", verbose=False)
    texto = result["text"].strip()
    print(f"  ✓  Transcrição: {len(texto)} caracteres")
    return texto


# ---------------------------------------------------------------------------
# Conversão de transcrição em pares instruction/output via LLM
# ---------------------------------------------------------------------------

def carregar_llm():
    """Carrega o LLM do pepe-ai (respeita PEPE_MODEL_PROVIDER do .env)."""
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass

    provider = os.getenv("PEPE_MODEL_PROVIDER", "groq").lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=os.getenv("PEPE_MODEL_NAME", "llama-3.3-70b-versatile"),
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.3,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=os.getenv("PEPE_MODEL_NAME", "claude-3-5-haiku-20241022"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3,
        )
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("PEPE_MODEL_NAME", "llama3.1"),
            temperature=0.3,
        )
    else:
        raise ValueError(f"Provider '{provider}' não suportado em extract_skills.py")


PROMPT_EXTRACAO = """
Você é um especialista em criar datasets de fine-tuning para agentes de IA.

Abaixo está a transcrição de um vídeo sobre o tema: **{skill}**

Sua tarefa:
1. Leia a transcrição completa
2. Extraia os principais ensinamentos, conceitos e informações
3. Crie entre 10 e 30 pares de pergunta e resposta no formato JSON
4. As perguntas devem ser naturais, como um usuário faria ao Pepê
5. As respostas devem ser diretas, em português do Brasil, no estilo do Pepê: conciso, prático, sem enrolação

Formato de saída (JSON puro, sem markdown):
[
  {{"instruction": "pergunta aqui", "output": "resposta aqui"}},
  ...
]

Transcrição:
{transcricao}

JSON:"""


def extrair_pares(transcricao: str, skill: str, llm) -> list[dict]:
    """Usa LLM para extrair pares instruction/output da transcrição."""
    print(f"  ▶  Extraindo pares com LLM (skill: {skill})...")

    # Limita transcrição para não estourar contexto
    max_chars = 8000
    if len(transcricao) > max_chars:
        transcricao = transcricao[:max_chars] + "\n[... transcrição truncada ...]"

    prompt = PROMPT_EXTRACAO.format(skill=skill, transcricao=transcricao)

    from langchain_core.messages import HumanMessage
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()

    # Extrai JSON da resposta
    json_match = re.search(r'\[.*\]', raw, re.DOTALL)
    if not json_match:
        print("  ⚠  LLM não retornou JSON válido")
        return []

    pares = json.loads(json_match.group())
    print(f"  ✓  {len(pares)} pares extraídos")
    return pares


# ---------------------------------------------------------------------------
# Conversão para formato messages
# ---------------------------------------------------------------------------

def pares_para_messages(pares: list[dict]) -> list[dict]:
    entries = []
    for p in pares:
        instruction = p.get("instruction", "").strip()
        output      = p.get("output", "").strip()
        if not instruction or not output:
            continue
        entries.append({
            "messages": [
                {"role": "system",    "content": SYSTEM_PEPE},
                {"role": "user",      "content": instruction},
                {"role": "assistant", "content": output},
            ]
        })
    return entries


# ---------------------------------------------------------------------------
# Pipeline principal por vídeo
# ---------------------------------------------------------------------------

def processar_video(video_path: Path, skill: str, llm, whisper_model: str = "base") -> int:
    """
    Processa um vídeo:
    1. Transcreve com Whisper
    2. Extrai pares com LLM
    3. Salva em training/skills/{skill}.jsonl
    Retorna número de exemplos adicionados.
    """
    output_file = SKILLS_DIR / f"{skill}.jsonl"

    # Transcreve
    transcricao = transcrever(video_path, model_size=whisper_model)
    if not transcricao:
        print(f"  ⚠  Transcrição vazia para {video_path.name}")
        return 0

    # Salva transcrição para referência
    transcript_file = SKILLS_DIR / f"{skill}_{video_path.stem}_transcript.txt"
    transcript_file.write_text(transcricao, encoding="utf-8")

    # Extrai pares
    pares = extrair_pares(transcricao, skill, llm)
    if not pares:
        return 0

    # Converte para messages
    entries = pares_para_messages(pares)

    # Adiciona ao JSONL da skill (append)
    with open(output_file, "a", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"  ✓  {len(entries)} exemplos adicionados em {output_file.name}")
    return len(entries)


# ---------------------------------------------------------------------------
# Processamento em lote
# ---------------------------------------------------------------------------

def processar_skill(skill: str, llm, whisper_model: str = "base", force: bool = False) -> int:
    """Processa todos os vídeos novos de uma skill."""
    skill_dir = VIDEOS_DIR / skill
    if not skill_dir.exists():
        print(f"  ⚠  Pasta não encontrada: {skill_dir}")
        return 0

    processed = load_processed()
    total = 0

    videos = [f for f in skill_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXTS]
    if not videos:
        print(f"  ⚠  Nenhum vídeo encontrado em {skill_dir}")
        return 0

    for video in sorted(videos):
        h = file_hash(video)
        if not force and processed.get(str(video)) == h:
            print(f"  ⏭  {video.name} já processado — pulando")
            continue

        print(f"\n  🎥 Processando: {video.name}")
        n = processar_video(video, skill, llm, whisper_model)
        total += n

        processed[str(video)] = h
        save_processed(processed)

    return total


def processar_todas(llm, whisper_model: str = "base", force: bool = False) -> None:
    """Processa todas as skills disponíveis."""
    skills = [d.name for d in VIDEOS_DIR.iterdir() if d.is_dir()]
    if not skills:
        print("  ⚠  Nenhuma skill encontrada em videos/skills/")
        return

    print(f"  Skills encontradas: {', '.join(skills)}")
    total = 0
    for skill in skills:
        print(f"\n{'='*50}\n  Skill: {skill}\n{'='*50}")
        total += processar_skill(skill, llm, whisper_model, force)

    print(f"\n  ✓  Total: {total} exemplos gerados")


# ---------------------------------------------------------------------------
# Modo watch
# ---------------------------------------------------------------------------

def watch(interval: int = 10, whisper_model: str = "base") -> None:
    import time

    print(f"  👀 Modo watch ativo (verifica a cada {interval}s) — Ctrl+C para sair")
    print(f"  Monitorando: {VIDEOS_DIR}")

    llm = carregar_llm()
    processed = load_processed()

    def get_videos():
        result = {}
        if VIDEOS_DIR.exists():
            for skill_dir in VIDEOS_DIR.iterdir():
                if skill_dir.is_dir():
                    for f in skill_dir.iterdir():
                        if f.suffix.lower() in SUPPORTED_EXTS:
                            result[str(f)] = file_hash(f)
        return result

    last = get_videos()

    try:
        while True:
            time.sleep(interval)
            current = get_videos()
            novos = {k: v for k, v in current.items() if processed.get(k) != v}
            if novos:
                for video_str in novos:
                    video = Path(video_str)
                    skill = video.parent.name
                    print(f"\n  🔄 Novo vídeo detectado: {video.name} (skill: {skill})")
                    n = processar_video(video, skill, llm, whisper_model)
                    if n > 0:
                        processed[video_str] = current[video_str]
                        save_processed(processed)
                        # Dispara reintegração
                        subprocess.run([
                            sys.executable,
                            str(ROOT / "training" / "integrate_datasets.py")
                        ])
                last = current
    except KeyboardInterrupt:
        print("\n  ⏹  Watch encerrado.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pepe AI — Extrator de Skills de Vídeos")
    parser.add_argument("--video",   type=str, help="Caminho para um vídeo específico")
    parser.add_argument("--skill",   type=str, help="Nome da skill")
    parser.add_argument("--all",     action="store_true", help="Processa todas as skills")
    parser.add_argument("--watch",   action="store_true", help="Modo watch automático")
    parser.add_argument("--force",   action="store_true", help="Reprocessa mesmo já processados")
    parser.add_argument("--whisper", type=str, default="base",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Tamanho do modelo Whisper (default: base)")
    parser.add_argument("--interval",type=int, default=10, help="Intervalo do watch em segundos")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  Pepe AI — Extrator de Skills")
    print("="*60)

    if args.watch:
        watch(interval=args.interval, whisper_model=args.whisper)
        sys.exit(0)

    llm = carregar_llm()

    if args.video:
        skill = args.skill or Path(args.video).parent.name
        video = Path(args.video)
        if not video.exists():
            print(f"  ✗  Arquivo não encontrado: {video}")
            sys.exit(1)
        processar_video(video, skill, llm, args.whisper)

    elif args.all:
        processar_todas(llm, args.whisper, args.force)

    elif args.skill:
        processar_skill(args.skill, llm, args.whisper, args.force)

    else:
        parser.print_help()
