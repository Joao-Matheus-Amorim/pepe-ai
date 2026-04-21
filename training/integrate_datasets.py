"""
Pepe AI — Integrador de Datasets

Converte pepe_dataset.json (instruction/output) para formato messages,
mescla com os 6 JSONL do generate_dataset.py, deduplica e salva os
splits finais em training/datasets/.

Uso:
  python training/integrate_datasets.py           # executa uma vez
  python training/integrate_datasets.py --watch   # monitora e reintegra automaticamente
"""

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
TRAINING_DIR = ROOT / "training"
DATASETS_DIR = TRAINING_DIR / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

GENERATE_SCRIPT = TRAINING_DIR / "generate_dataset.py"
JSON_DATASET    = DATASETS_DIR / "pepe_dataset.json"
GENERATED_DIR   = ROOT / "dataset"   # saída do generate_dataset.py

OUTPUT_TRAIN = DATASETS_DIR / "pepe_train.jsonl"
OUTPUT_VAL   = DATASETS_DIR / "pepe_val.jsonl"
OUTPUT_FULL  = DATASETS_DIR / "pepe_full.jsonl"

RANDOM_SEED  = 42
VAL_SPLIT    = 0.10

SYSTEM_PEPE = (
    "Você é Pepê, um agente de IA pessoal inteligente, direto e eficiente. "
    "Você tem acesso a ferramentas de busca web, clima, visão de tela, execução de comandos, "
    "leitura de arquivos e memória persistente. "
    "Quando receber uma pergunta, classifique a intenção e use a ferramenta correta. "
    "Responda sempre em português do Brasil, de forma clara e concisa."
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def entry_hash(entry: dict) -> str:
    """Hash estável do conteúdo para deduplicação."""
    raw = json.dumps(entry, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def convert_instruction_to_messages(raw: list[dict]) -> list[dict]:
    """Converte pares instruction/output para formato messages."""
    entries = []
    for item in raw:
        instruction = item.get("instruction", "").strip()
        output      = item.get("output", "").strip()
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


def load_json_dataset() -> list[dict]:
    """Carrega e converte pepe_dataset.json se existir."""
    if not JSON_DATASET.exists():
        print(f"  ⚠  {JSON_DATASET.name} não encontrado — pulando.")
        return []
    with open(JSON_DATASET, encoding="utf-8") as f:
        raw = json.load(f)
    converted = convert_instruction_to_messages(raw)
    print(f"  ✓  {JSON_DATASET.name}: {len(raw)} pares → {len(converted)} exemplos convertidos")
    return converted


def run_generate_script() -> None:
    """Executa generate_dataset.py para (re)gerar os 6 JSONL."""
    if not GENERATE_SCRIPT.exists():
        print(f"  ⚠  {GENERATE_SCRIPT.name} não encontrado — pulando geração.")
        return
    print(f"  ▶  Executando {GENERATE_SCRIPT.name}...")
    result = subprocess.run(
        [sys.executable, str(GENERATE_SCRIPT)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ✗  Erro ao executar generate_dataset.py:\n{result.stderr}")
    else:
        for line in result.stdout.splitlines():
            print(f"     {line}")


def load_generated_jsonl() -> list[dict]:
    """Carrega os 6 JSONL gerados pelo generate_dataset.py."""
    if not GENERATED_DIR.exists():
        print(f"  ⚠  Pasta {GENERATED_DIR} não encontrada — pulando JSONL gerados.")
        return []
    entries = []
    jsonl_files = sorted(GENERATED_DIR.glob("*.jsonl"))
    for path in jsonl_files:
        if path.stem in ("pepe_train", "pepe_val"):
            continue  # evita recarregar splits anteriores
        count = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
                    count += 1
        print(f"  ✓  {path.name}: {count} exemplos")
    return entries


def deduplicate(entries: list[dict]) -> list[dict]:
    seen, unique = set(), []
    for e in entries:
        h = entry_hash(e)
        if h not in seen:
            seen.add(h)
            unique.append(e)
    return unique


def save_jsonl(entries: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def validate(entries: list[dict]) -> list[str]:
    erros = []
    for i, e in enumerate(entries):
        msgs = e.get("messages", [])
        if not msgs:
            erros.append(f"Exemplo {i}: sem 'messages'")
            continue
        roles = [m.get("role") for m in msgs]
        if roles[0] not in ("system", "user"):
            erros.append(f"Exemplo {i}: começa com '{roles[0]}'")
        if "assistant" not in roles:
            erros.append(f"Exemplo {i}: sem assistant")
    return erros


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def integrate() -> None:
    print("\n" + "=" * 60)
    print("  Pepe AI — Integrador de Datasets")
    print("=" * 60)

    # 1. Gera JSONL frescos
    run_generate_script()
    print()

    # 2. Carrega fontes
    json_entries  = load_json_dataset()
    jsonl_entries = load_generated_jsonl()

    all_entries = json_entries + jsonl_entries
    print(f"\n  Total antes da deduplicação: {len(all_entries)} exemplos")

    # 3. Deduplica
    all_entries = deduplicate(all_entries)
    print(f"  Total após deduplicação:     {len(all_entries)} exemplos únicos")

    # 4. Valida
    erros = validate(all_entries)
    if erros:
        print(f"\n  ⚠  {len(erros)} problema(s) encontrado(s):")
        for e in erros[:10]:
            print(f"     {e}")
    else:
        print("  ✓  Validação OK — nenhum problema encontrado")

    # 5. Shuffle + split
    random.seed(RANDOM_SEED)
    random.shuffle(all_entries)
    split = int(len(all_entries) * (1 - VAL_SPLIT))
    train = all_entries[:split]
    val   = all_entries[split:]

    # 6. Salva
    save_jsonl(all_entries, OUTPUT_FULL)
    save_jsonl(train, OUTPUT_TRAIN)
    save_jsonl(val,   OUTPUT_VAL)

    print()
    print(f"  ✓  pepe_full.jsonl  → {len(all_entries)} exemplos")
    print(f"  ✓  pepe_train.jsonl → {len(train)} exemplos (90%)")
    print(f"  ✓  pepe_val.jsonl   → {len(val)} exemplos (10%)")
    print(f"\n  Pasta: {DATASETS_DIR}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Modo watch — monitora arquivos e reintegra ao detectar mudança
# ---------------------------------------------------------------------------

def get_mtimes() -> dict[str, float]:
    watched = [JSON_DATASET, GENERATE_SCRIPT]
    if GENERATED_DIR.exists():
        watched += list(GENERATED_DIR.glob("*.jsonl"))
    return {
        str(p): p.stat().st_mtime
        for p in watched if p.exists()
    }


def watch(interval: int = 5) -> None:
    print(f"  👀  Modo watch ativo (verifica a cada {interval}s) — Ctrl+C para sair")
    print(f"  Monitorando: {JSON_DATASET.name}, {GENERATE_SCRIPT.name} e dataset/*.jsonl\n")
    last = get_mtimes()
    integrate()
    try:
        while True:
            time.sleep(interval)
            current = get_mtimes()
            if current != last:
                changed = [
                    Path(k).name for k in current
                    if current.get(k) != last.get(k) or k not in last
                ]
                print(f"\n  🔄  Mudança detectada: {', '.join(changed)}")
                integrate()
                last = current
    except KeyboardInterrupt:
        print("\n  ⏹  Watch encerrado.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pepe AI — Integrador de Datasets")
    parser.add_argument(
        "--watch", action="store_true",
        help="Monitora arquivos e reintegra automaticamente ao detectar mudanças"
    )
    parser.add_argument(
        "--interval", type=int, default=5,
        help="Intervalo em segundos para o modo watch (padrão: 5)"
    )
    args = parser.parse_args()

    if args.watch:
        watch(interval=args.interval)
    else:
        integrate()
