from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TRAINING_DIR = ROOT_DIR / "training"
TRAINING_DATASETS_DIR = TRAINING_DIR / "datasets"
RAW_JSON_PATH = TRAINING_DATASETS_DIR / "pepe_dataset.json"
GENERATED_DIR = ROOT_DIR / "dataset"
GENERATOR_SCRIPT = TRAINING_DIR / "generate_dataset.py"

FULL_OUT = TRAINING_DATASETS_DIR / "pepe_full.jsonl"
TRAIN_OUT = TRAINING_DATASETS_DIR / "pepe_train.jsonl"
VAL_OUT = TRAINING_DATASETS_DIR / "pepe_val.jsonl"

SYSTEM_PEPE = (
    "Você é Pepê, um agente de IA pessoal inteligente, direto e eficiente. "
    "Você tem acesso a ferramentas de busca web, clima, visão de tela, execução de comandos, "
    "leitura de arquivos e memória persistente. "
    "Quando receber uma pergunta, classifique a intencao e use a ferramenta correta. "
    "Responda sempre em portugues do Brasil, de forma clara e concisa."
)

LAYER_FILE_PREFIXES = ("01_", "02_", "03_", "04_", "05_", "06_")
SPLIT_SEED = 42


def normalize_system_prompt(entry: dict) -> dict:
    messages = entry.get("messages")
    if not isinstance(messages, list):
        return entry

    normalized_messages: list[dict] = []
    system_replaced = False
    for msg in messages:
        if not isinstance(msg, dict):
            normalized_messages.append(msg)
            continue

        normalized_msg = dict(msg)
        if normalized_msg.get("role") == "system":
            normalized_msg["content"] = SYSTEM_PEPE
            system_replaced = True
        normalized_messages.append(normalized_msg)

    if not system_replaced:
        normalized_messages.insert(0, {"role": "system", "content": SYSTEM_PEPE})

    return {**entry, "messages": normalized_messages}


def user_signature(entry: dict) -> str | None:
    messages = entry.get("messages")
    if not isinstance(messages, list):
        return None

    user_parts: list[str] = []
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") != "user":
            continue
        content = msg.get("content")
        if content is None:
            continue
        text = str(content).strip()
        if text:
            user_parts.append(text)

    if not user_parts:
        return None
    return "\n".join(user_parts).casefold()


def run_generator() -> None:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    cmd = [sys.executable, str(GENERATOR_SCRIPT)]
    result = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env)
    if result.returncode != 0:
        raise RuntimeError("Falha ao executar training/generate_dataset.py")


def canonical_md5(entry: dict) -> str:
    normalized = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            text = line.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON invalido em {path}:{line_num}: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"Linha nao-objeto em {path}:{line_num}")
            rows.append(obj)
    return rows


def load_layer_jsonls() -> list[dict]:
    if not GENERATED_DIR.exists():
        return []

    selected = [
        p
        for p in sorted(GENERATED_DIR.glob("*.jsonl"))
        if p.name.startswith(LAYER_FILE_PREFIXES)
    ]

    entries: list[dict] = []
    for path in selected:
        entries.extend(load_jsonl(path))
    return entries


def convert_raw_dataset(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("pepe_dataset.json deve ser uma lista de objetos")

    entries: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        instruction = str(item.get("instruction", "")).strip()
        output = str(item.get("output", "")).strip()
        if not instruction or not output:
            continue
        entries.append(
            {
                "messages": [
                    {"role": "system", "content": SYSTEM_PEPE},
                    {"role": "user", "content": instruction},
                    {"role": "assistant", "content": output},
                ]
            }
        )
    return [normalize_system_prompt(entry) for entry in entries]


def dedupe_entries(entries: list[dict]) -> tuple[list[dict], int]:
    seen_user_signatures: set[str] = set()
    seen_fallback_hashes: set[str] = set()
    unique: list[dict] = []
    removed = 0
    for entry in entries:
        signature = user_signature(entry)
        if signature is not None:
            if signature in seen_user_signatures:
                removed += 1
                continue
            seen_user_signatures.add(signature)
            unique.append(entry)
            continue

        h = canonical_md5(entry)
        if h in seen_fallback_hashes:
            removed += 1
            continue
        seen_fallback_hashes.add(h)
        unique.append(entry)
    return unique, removed


def validate_entries(entries: list[dict]) -> list[str]:
    errors: list[str] = []
    for i, entry in enumerate(entries):
        msgs = entry.get("messages")
        if not isinstance(msgs, list) or not msgs:
            errors.append(f"Exemplo {i}: sem 'messages' valido")
            continue

        roles = [m.get("role") for m in msgs if isinstance(m, dict)]
        if not roles:
            errors.append(f"Exemplo {i}: mensagens invalidas")
            continue

        if roles[0] not in ("system", "user"):
            errors.append(f"Exemplo {i}: primeira role invalida ({roles[0]})")
        if "assistant" not in roles:
            errors.append(f"Exemplo {i}: sem resposta assistant")

        known_tool_calls: set[str] = set()
        for m_idx, msg in enumerate(msgs):
            if not isinstance(msg, dict):
                errors.append(f"Exemplo {i}, msg {m_idx}: mensagem nao e objeto")
                continue

            role = msg.get("role")
            if role == "assistant" and "tool_calls" in msg:
                if msg.get("content") is not None:
                    errors.append(
                        f"Exemplo {i}, msg {m_idx}: assistant com tool_calls deve ter content=None"
                    )
                calls = msg.get("tool_calls")
                if not isinstance(calls, list) or not calls:
                    errors.append(f"Exemplo {i}, msg {m_idx}: tool_calls invalido")
                    continue
                for call in calls:
                    if not isinstance(call, dict):
                        errors.append(f"Exemplo {i}, msg {m_idx}: tool_call invalido")
                        continue
                    call_id = call.get("id")
                    if not call_id:
                        errors.append(f"Exemplo {i}, msg {m_idx}: tool_call sem id")
                        continue
                    known_tool_calls.add(str(call_id))

            if role == "tool":
                tool_call_id = msg.get("tool_call_id")
                if not tool_call_id:
                    errors.append(f"Exemplo {i}, msg {m_idx}: tool sem tool_call_id")
                elif str(tool_call_id) not in known_tool_calls:
                    errors.append(
                        f"Exemplo {i}, msg {m_idx}: tool_call_id '{tool_call_id}' nao encontrado"
                    )

        for m_idx, msg in enumerate(msgs[:-1]):
            if isinstance(msg, dict) and msg.get("role") == "tool":
                next_msg = msgs[m_idx + 1]
                if not isinstance(next_msg, dict) or next_msg.get("role") != "assistant":
                    errors.append(f"Exemplo {i}, msg {m_idx}: tool deve ser seguida por assistant")

    return errors


def save_jsonl(entries: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def integrate_once() -> None:
    print("=" * 72)
    print("Pepe AI - Integracao de Datasets")
    print("=" * 72)

    run_generator()

    layer_entries = [normalize_system_prompt(entry) for entry in load_layer_jsonls()]
    converted_entries = convert_raw_dataset(RAW_JSON_PATH)
    merged_entries = layer_entries + converted_entries

    unique_entries, removed = dedupe_entries(merged_entries)
    errors = validate_entries(unique_entries)

    if errors:
        print("[WARN] Erros de validacao encontrados:")
        for err in errors[:50]:
            print(f"  - {err}")
        if len(errors) > 50:
            print(f"  - ... +{len(errors) - 50} erros adicionais")

    rng = random.Random(SPLIT_SEED)
    rng.shuffle(unique_entries)

    split_index = int(len(unique_entries) * 0.9)
    train_entries = unique_entries[:split_index]
    val_entries = unique_entries[split_index:]

    save_jsonl(unique_entries, FULL_OUT)
    save_jsonl(train_entries, TRAIN_OUT)
    save_jsonl(val_entries, VAL_OUT)

    print(f"[OK] Camadas JSONL carregadas: {len(layer_entries)}")
    print(f"[OK] JSON convertido de {RAW_JSON_PATH.name}: {len(converted_entries)}")
    print(f"[OK] Total mesclado: {len(merged_entries)}")
    print(f"[OK] Duplicatas removidas: {removed}")
    print(f"[OK] Dataset final: {len(unique_entries)}")
    print(f"[OK] Treino: {len(train_entries)} -> {TRAIN_OUT}")
    print(f"[OK] Validacao: {len(val_entries)} -> {VAL_OUT}")
    print(f"[OK] Completo: {FULL_OUT}")


def watched_files() -> list[Path]:
    files: list[Path] = [RAW_JSON_PATH, GENERATOR_SCRIPT]
    if GENERATED_DIR.exists():
        files.extend(sorted(GENERATED_DIR.glob("*.jsonl")))
    return files


def snapshot_mtimes(paths: list[Path]) -> dict[Path, float | None]:
    state: dict[Path, float | None] = {}
    for path in paths:
        state[path] = path.stat().st_mtime if path.exists() else None
    return state


def has_changes(previous: dict[Path, float | None], current: dict[Path, float | None]) -> bool:
    if set(previous.keys()) != set(current.keys()):
        return True
    for path, mtime in current.items():
        if previous.get(path) != mtime:
            return True
    return False


def watch_loop(interval: float) -> None:
    print(f"[WATCH] Modo observacao ativo (intervalo: {interval:.1f}s)")
    last_state = snapshot_mtimes(watched_files())

    while True:
        time.sleep(interval)
        state_now = snapshot_mtimes(watched_files())
        if has_changes(last_state, state_now):
            print("\n[WATCH] Mudanca detectada. Reintegrando...")
            try:
                integrate_once()
            except Exception as exc:
                print(f"[ERROR] Falha na reintegracao: {exc}")
            last_state = snapshot_mtimes(watched_files())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Integra e valida datasets do Pepe")
    parser.add_argument("--watch", action="store_true", help="Ativa modo observacao")
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Intervalo de checagem no modo --watch (segundos)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        integrate_once()
        if args.watch:
            watch_loop(interval=max(1.0, args.interval))
    except KeyboardInterrupt:
        print("\n[INFO] Encerrado pelo usuario")
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
