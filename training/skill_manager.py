"""
Pepe AI — Gerenciador de Skills

Lista, ativa, desativa e mostra estatísticas das skills de treinamento.

Uso:
  python training/skill_manager.py list              # lista todas as skills
  python training/skill_manager.py show programacao  # detalhes de uma skill
  python training/skill_manager.py enable programacao
  python training/skill_manager.py disable culinaria
  python training/skill_manager.py stats             # estatísticas gerais
  python training/skill_manager.py new minha_skill   # cria estrutura de uma nova skill
"""

import argparse
import json
from pathlib import Path

ROOT       = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "training" / "skills"
VIDEOS_DIR = ROOT / "videos" / "skills"
CONFIG     = SKILLS_DIR / "skills_config.json"

SKILLS_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SKILLS = [
    {"name": "programacao",  "description": "Python, IA, LangChain, algoritmos",        "enabled": True},
    {"name": "culinaria",    "description": "Churrasco, receitas, técnicas culinárias",  "enabled": True},
    {"name": "fitness",      "description": "Treinos, saúde, nutrição",                  "enabled": True},
    {"name": "financas",     "description": "Investimentos, gestão financeira",           "enabled": True},
    {"name": "custom",       "description": "Skills personalizadas",                      "enabled": True},
]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config() -> list[dict]:
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return DEFAULT_SKILLS


def save_config(config: list[dict]) -> None:
    CONFIG.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def get_skill(config: list[dict], name: str) -> dict | None:
    return next((s for s in config if s["name"] == name), None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def count_examples(skill_name: str) -> int:
    jsonl = SKILLS_DIR / f"{skill_name}.jsonl"
    if not jsonl.exists():
        return 0
    return sum(1 for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip())


def count_videos(skill_name: str) -> int:
    skill_dir = VIDEOS_DIR / skill_name
    if not skill_dir.exists():
        return 0
    exts = {".mp4", ".mp3", ".wav", ".m4a", ".mkv", ".avi", ".mov", ".webm"}
    return sum(1 for f in skill_dir.iterdir() if f.suffix.lower() in exts)


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------

def cmd_list(config: list[dict]) -> None:
    print("\n" + "="*60)
    print("  Pepe AI — Skills de Treinamento")
    print("="*60)
    print(f"  {'SKILL':<16} {'STATUS':<10} {'EXEMPLOS':>8} {'VÍDEOS':>7}  DESCRIÇÃO")
    print("  " + "-"*58)
    for s in config:
        status  = "✅ ativa" if s["enabled"] else "❌ desativa"
        exs     = count_examples(s["name"])
        vids    = count_videos(s["name"])
        print(f"  {s['name']:<16} {status:<10} {exs:>8} {vids:>7}  {s['description']}")
    print("="*60)


def cmd_show(config: list[dict], name: str) -> None:
    skill = get_skill(config, name)
    if not skill:
        print(f"  ✗  Skill '{name}' não encontrada")
        return

    exs  = count_examples(name)
    vids = count_videos(name)
    jsonl = SKILLS_DIR / f"{name}.jsonl"

    print(f"\n  Skill: {name}")
    print(f"  Descrição:  {skill['description']}")
    print(f"  Status:     {'ativa' if skill['enabled'] else 'desativada'}")
    print(f"  Exemplos:   {exs}")
    print(f"  Vídeos:     {vids}")
    print(f"  JSONL:      {jsonl}")
    print(f"  Videos dir: {VIDEOS_DIR / name}")

    # Mostra 3 exemplos
    if exs > 0:
        print(f"\n  --- Primeiros exemplos ---")
        with open(jsonl, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 3:
                    break
                entry = json.loads(line)
                msgs = entry.get("messages", [])
                user = next((m["content"] for m in msgs if m["role"] == "user"), "")
                asst = next((m["content"] for m in msgs if m["role"] == "assistant"), "")
                print(f"  [{i+1}] U: {user[:80]}")
                print(f"       A: {asst[:80]}\n")


def cmd_enable(config: list[dict], name: str) -> None:
    skill = get_skill(config, name)
    if not skill:
        print(f"  ✗  Skill '{name}' não encontrada")
        return
    skill["enabled"] = True
    save_config(config)
    print(f"  ✅  Skill '{name}' ativada")


def cmd_disable(config: list[dict], name: str) -> None:
    skill = get_skill(config, name)
    if not skill:
        print(f"  ✗  Skill '{name}' não encontrada")
        return
    skill["enabled"] = False
    save_config(config)
    print(f"  ❌  Skill '{name}' desativada")


def cmd_new(config: list[dict], name: str, description: str = "") -> None:
    if get_skill(config, name):
        print(f"  ⚠  Skill '{name}' já existe")
        return

    # Cria pastas
    (VIDEOS_DIR / name).mkdir(parents=True, exist_ok=True)
    (SKILLS_DIR / name).mkdir(parents=True, exist_ok=True)

    # Cria README na pasta de vídeos
    readme = VIDEOS_DIR / name / "README.md"
    readme.write_text(
        f"# Skill: {name}\n\n"
        f"{description or 'Coloque vídeos aqui para treinar esta skill.'}\n\n"
        "## Formatos suportados\n"
        "`.mp4`, `.mp3`, `.wav`, `.m4a`, `.mkv`, `.avi`, `.mov`, `.webm`\n\n"
        "## Como usar\n"
        "```bash\n"
        f"python training/extract_skills.py --skill {name}\n"
        "```\n",
        encoding="utf-8"
    )

    config.append({
        "name": name,
        "description": description or f"Skill personalizada: {name}",
        "enabled": True
    })
    save_config(config)
    print(f"  ✅  Skill '{name}' criada")
    print(f"     Coloque vídeos em: {VIDEOS_DIR / name}")
    print(f"     Extraia com: python training/extract_skills.py --skill {name}")


def cmd_stats(config: list[dict]) -> None:
    total_ex   = sum(count_examples(s["name"]) for s in config)
    total_vids = sum(count_videos(s["name"]) for s in config)
    ativas     = sum(1 for s in config if s["enabled"])

    # Total do dataset principal
    train_jsonl = ROOT / "training" / "datasets" / "pepe_train.jsonl"
    val_jsonl   = ROOT / "training" / "datasets" / "pepe_val.jsonl"
    train_count = sum(1 for l in train_jsonl.read_text().splitlines() if l.strip()) if train_jsonl.exists() else 0
    val_count   = sum(1 for l in val_jsonl.read_text().splitlines() if l.strip()) if val_jsonl.exists() else 0

    print("\n" + "="*60)
    print("  Pepe AI — Estatísticas de Treinamento")
    print("="*60)
    print(f"  Skills ativas:          {ativas}/{len(config)}")
    print(f"  Vídeos processados:     {total_vids}")
    print(f"  Exemplos de skills:     {total_ex}")
    print(f"  Dataset treino atual:   {train_count} exemplos")
    print(f"  Dataset val atual:      {val_count} exemplos")
    print(f"  Total com skills:       {train_count + val_count + total_ex} exemplos")
    print("="*60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pepe AI — Gerenciador de Skills")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list",  help="Lista todas as skills")
    sub.add_parser("stats", help="Estatísticas gerais")

    p_show = sub.add_parser("show", help="Detalhes de uma skill")
    p_show.add_argument("name")

    p_en = sub.add_parser("enable", help="Ativa uma skill")
    p_en.add_argument("name")

    p_dis = sub.add_parser("disable", help="Desativa uma skill")
    p_dis.add_argument("name")

    p_new = sub.add_parser("new", help="Cria uma nova skill")
    p_new.add_argument("name")
    p_new.add_argument("--description", type=str, default="")

    args = parser.parse_args()
    config = load_config()

    if   args.cmd == "list":    cmd_list(config)
    elif args.cmd == "show":    cmd_show(config, args.name)
    elif args.cmd == "enable":  cmd_enable(config, args.name)
    elif args.cmd == "disable": cmd_disable(config, args.name)
    elif args.cmd == "new":     cmd_new(config, args.name, args.description)
    elif args.cmd == "stats":   cmd_stats(config)
    else: parser.print_help()
