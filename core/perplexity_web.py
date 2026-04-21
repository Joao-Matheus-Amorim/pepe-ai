"""Cliente web do Perplexity com sessão persistente via Playwright.

O objetivo deste módulo é permitir busca na conta do usuário sem API key.
O primeiro login pode ser feito manualmente no navegador aberto pelo helper
`python -m core.perplexity_web login`.
"""

from __future__ import annotations

import argparse
import atexit
import os
import re
import shutil
import subprocess
from time import monotonic
from pathlib import Path
from threading import Lock
from typing import Optional

LOGIN_URL = "https://www.perplexity.ai/?login-source=oneTapHome&login-new=false"
SEARCH_URL = "https://www.perplexity.ai/?login-source=computerPage&login-new=false"

_CONTEXT_LOCK = Lock()
_PLAYWRIGHT = None
_CONTEXT = None

_NOISE_EXACT = {
    "Computer",
    "Modelo",
    "Orquestrador",
    "Fechar",
    "Entendi",
    "Recusar",
    "Seu Computer está pronto.",
}

_NOISE_CONTAINS = (
    "Continue com Google",
    "Continue com Apple",
    "Continuar com e-mail",
    "Login único (SSO)",
    "política de privacidade",
    "privacy policy",
)


def _env_bool(name: str, default: bool) -> bool:
    valor = os.getenv(name)
    if valor is None:
        return default
    return valor.strip().lower() in {"1", "true", "yes", "sim", "on"}


def _profile_dir() -> Path:
    return Path(os.getenv("PEPE_PERPLEXITY_PROFILE_DIR", "memory/perplexity-profile"))


def _browser_channel() -> str:
    return os.getenv("PEPE_PERPLEXITY_BROWSER_CHANNEL", "chrome").strip()


def _browser_profile_args() -> list[str]:
    return [
        f"--user-data-dir={_profile_dir()}",
        "--no-first-run",
        "--no-default-browser-check",
    ]


def _encontrar_browser_externo() -> str | None:
    candidatos = [
        shutil.which("chrome.exe"),
        shutil.which("chrome"),
        shutil.which("msedge.exe"),
        shutil.which("msedge"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("LocalAppData", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
    ]
    for candidato in candidatos:
        if candidato and os.path.exists(candidato):
            return candidato
    return None


def _abrir_browser_externo(url: str) -> None:
    browser = _encontrar_browser_externo()
    if not browser:
        raise RuntimeError(
            "Não encontrei Chrome ou Edge instalado. Instale um navegador compatível para o login manual persistente."
        )

    _profile_dir().mkdir(parents=True, exist_ok=True)
    args = [browser, *_browser_profile_args(), "--new-window", url]
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _headless() -> bool:
    return _env_bool("PEPE_PERPLEXITY_HEADLESS", False)


def _login_method(override: str | None = None) -> str:
    metodo = (override or os.getenv("PEPE_PERPLEXITY_LOGIN_METHOD", "manual")).strip().lower()
    if metodo not in {"manual", "google", "email"}:
        return "manual"
    return metodo


def _clean_text(text: str) -> str:
    linhas = []
    for linha in re.split(r"\r?\n+", text or ""):
        limpa = re.sub(r"\s+", " ", linha).strip()
        if not limpa:
            continue
        if limpa in _NOISE_EXACT:
            continue
        if any(part in limpa for part in _NOISE_CONTAINS):
            continue
        if limpa.isdigit():
            continue
        linhas.append(limpa)

    saida = "\n".join(linhas)
    saida = re.sub(r"\n{3,}", "\n\n", saida)
    return saida.strip()


def _ensure_playwright_context(headless: Optional[bool] = None):
    global _PLAYWRIGHT, _CONTEXT

    with _CONTEXT_LOCK:
        if _CONTEXT is not None:
            return _CONTEXT

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as erro:
            raise RuntimeError(
                "Dependência ausente para busca web no Perplexity. Instale 'playwright'."
            ) from erro

        _profile_dir().mkdir(parents=True, exist_ok=True)
        _PLAYWRIGHT = sync_playwright().start()
        launch_kwargs = {
            "user_data_dir": str(_profile_dir()),
            "headless": _headless() if headless is None else headless,
            "viewport": {"width": 1400, "height": 1200},
            "locale": "pt-BR",
        }
        channel = _browser_channel()
        if channel:
            launch_kwargs["channel"] = channel

        try:
            _CONTEXT = _PLAYWRIGHT.chromium.launch_persistent_context(**launch_kwargs)
        except Exception:
            launch_kwargs.pop("channel", None)
            _CONTEXT = _PLAYWRIGHT.chromium.launch_persistent_context(**launch_kwargs)
        return _CONTEXT


def _shutdown_context() -> None:
    global _PLAYWRIGHT, _CONTEXT

    with _CONTEXT_LOCK:
        if _CONTEXT is not None:
            try:
                _CONTEXT.close()
            finally:
                _CONTEXT = None

        if _PLAYWRIGHT is not None:
            try:
                _PLAYWRIGHT.stop()
            finally:
                _PLAYWRIGHT = None


atexit.register(_shutdown_context)


def _get_page(context):
    if context.pages:
        return context.pages[0]
    return context.new_page()


def _dismiss_popups(page) -> None:
    for nome in ("Entendi", "Recusar", "Fechar"):
        try:
            botao = page.get_by_role("button", name=nome)
            if botao.count() > 0:
                botao.first.click(timeout=1500)
                page.wait_for_timeout(500)
        except Exception:
            pass


def _login_modal_visivel(page) -> bool:
    try:
        tem_email = page.locator('input[type="email"]').count() > 0
        tem_botao_email = page.get_by_role("button", name="Continuar com e-mail").count() > 0
        return tem_email or tem_botao_email
    except Exception:
        return False


def _session_ready(page) -> bool:
    try:
        return page.locator('#ask-input').count() > 0 and not _login_modal_visivel(page)
    except Exception:
        return False


def _acionar_modal_login(page, consulta: str = "login") -> None:
    try:
        caixa = page.locator('#ask-input').first
        caixa.click(timeout=10000)
        caixa.fill(consulta)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2500)
    except Exception:
        pass


def _first_visible_button(page, names: list[str]):
    for nome in names:
        try:
            botao = page.get_by_role("button", name=nome)
            if botao.count() > 0 and botao.first.is_visible():
                return botao.first
        except Exception:
            continue
    return None


def _fill_first(page, selectors: list[str], value: str) -> bool:
    for selector in selectors:
        try:
            campo = page.locator(selector)
            if campo.count() > 0:
                campo.first.fill(value)
                return True
        except Exception:
            continue
    return False


def _click_first(page, selectors: list[str]) -> bool:
    for selector in selectors:
        try:
            alvo = page.locator(selector)
            if alvo.count() > 0:
                alvo.first.click(timeout=5000)
                return True
        except Exception:
            continue
    return False


def _page_text(page) -> str:
    for selector in ("main", "body"):
        try:
            texto = page.locator(selector).inner_text(timeout=10000)
            if texto:
                return texto
        except Exception:
            continue
    return ""


def _extrair_resposta(page, query: str) -> str:
    candidatos: list[str] = []
    seletores = [
        "main",
        "article",
        "[role='article']",
        "[data-testid*='answer']",
        "[data-testid*='result']",
        "[class*='answer']",
        "[class*='response']",
    ]

    for seletor in seletores:
        try:
            locator = page.locator(seletor)
            for i in range(min(locator.count(), 5)):
                try:
                    texto = locator.nth(i).inner_text(timeout=5000)
                except Exception:
                    continue
                texto = _clean_text(texto)
                if texto:
                    candidatos.append(texto)
        except Exception:
            continue

    if not candidatos:
        candidatos.append(_clean_text(_page_text(page)))

    query_norm = query.strip().lower()
    filtrados = [
        texto for texto in candidatos
        if query_norm not in texto.lower() or len(texto) > len(query_norm) + 40
    ]
    melhor = max(filtrados or candidatos, key=len, default="")
    return melhor[:4000].strip()


def _aplicar_login_automatico(page, metodo_override: str | None = None) -> None:
    metodo = _login_method(metodo_override)
    if metodo == "google":
        email = os.getenv("PEPE_PERPLEXITY_EMAIL", "").strip()
        senha = os.getenv("PEPE_PERPLEXITY_PASSWORD", "").strip()

        try:
            botao = _first_visible_button(page, ["Continue com Google", "Continue with Google"])
            if botao is not None:
                before_pages = set(page.context.pages)
                botao.click(timeout=5000)
                page.wait_for_timeout(2500)
                auth_page = page
                novas_paginas = [p for p in page.context.pages if p not in before_pages]
                if novas_paginas:
                    auth_page = novas_paginas[-1]

                inicio = monotonic()
                while monotonic() - inicio < 120:
                    if _fill_first(auth_page, ['input[type="email"]', 'input[name="identifier"]', 'input[type="text"]'], email):
                        if _click_first(auth_page, ["text=Next", "text=Próxima", "text=Avançar", "text=Continuar"]):
                            auth_page.wait_for_timeout(2000)
                    if _fill_first(auth_page, ['input[type="password"]'], senha):
                        if _click_first(auth_page, ["text=Next", "text=Próxima", "text=Avançar", "text=Continuar", "button[type='submit']"]):
                            auth_page.wait_for_timeout(3000)

                    if "perplexity.ai" in auth_page.url:
                        page.wait_for_timeout(2000)
                        break
                    if "accounts.google.com" not in auth_page.url and auth_page.url != page.url:
                        page.wait_for_timeout(2000)
                        break
                    auth_page.wait_for_timeout(1000)
        except Exception:
            pass
        return

    if metodo == "email":
        email = os.getenv("PEPE_PERPLEXITY_EMAIL", "").strip()
        senha = os.getenv("PEPE_PERPLEXITY_PASSWORD", "").strip()

        try:
            botao = page.get_by_role("button", name="Continuar com e-mail")
            if botao.count() > 0:
                botao.first.click(timeout=5000)
                page.wait_for_timeout(1000)
        except Exception:
            pass

        if email:
            try:
                campo_email = page.locator('input[type="email"]').first
                campo_email.fill(email)
                page.wait_for_timeout(500)
                if page.get_by_role("button", name="Continuar").count() > 0:
                    page.get_by_role("button", name="Continuar").first.click(timeout=5000)
            except Exception:
                pass

        if senha:
            try:
                campo_senha = page.locator('input[type="password"]').first
                campo_senha.fill(senha)
                page.wait_for_timeout(500)
                for nome in ("Continuar", "Entrar", "Login", "Sign in"):
                    if page.get_by_role("button", name=nome).count() > 0:
                        page.get_by_role("button", name=nome).first.click(timeout=5000)
                        break
            except Exception:
                pass


def login(wait_for_user: bool = True, method: str | None = None) -> None:
    """Abre o navegador para autenticar o Perplexity uma vez."""
    metodo = _login_method(method)

    if metodo == "manual":
        _abrir_browser_externo(LOGIN_URL)
        print("Abra a janela do Chrome/Edge e faça login normalmente.")
        print("A sessão ficará salva no perfil persistente.")
        if wait_for_user:
            try:
                input("Pressione Enter depois de concluir o login...")
            except EOFError:
                pass
        return

    context = _ensure_playwright_context(headless=False)
    page = _get_page(context)
    try:
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(3000)
        _dismiss_popups(page)

        if metodo in {"google", "email"}:
            if not _login_modal_visivel(page):
                _acionar_modal_login(page)
            _aplicar_login_automatico(page, metodo)
            page.wait_for_timeout(2000)

        if not wait_for_user:
            limite = int(os.getenv("PEPE_PERPLEXITY_LOGIN_WAIT_MS", "120000"))
            inicio = monotonic()
            while monotonic() - inicio < limite / 1000:
                if _session_ready(page):
                    break
                page.wait_for_timeout(1500)
            else:
                raise RuntimeError("Login do Perplexity não concluiu dentro do tempo limite.")

        print("Complete o login na janela do navegador, se necessário.")
        print("Quando a interface principal do Perplexity aparecer, pressione Enter aqui.")
        if wait_for_user:
            try:
                input()
            except EOFError:
                pass
    finally:
        _shutdown_context()


def buscar_perplexity_web(query: str) -> str:
    """Executa busca web no Perplexity usando a sessão do navegador."""
    consulta = (query or "").strip()
    if not consulta:
        return "Consulta vazia."

    context = _ensure_playwright_context()
    page = _get_page(context)
    try:
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(3000)
        _dismiss_popups(page)
        try:
            page.wait_for_selector('#ask-input', timeout=15000)
        except Exception:
            page.wait_for_timeout(3000)
            if not _session_ready(page):
                raise RuntimeError(
                    "Perplexity não está pronto ou a sessão ainda não foi autenticada. Execute `python -m core.perplexity_web login` primeiro."
                )

        tentativa = 0
        while tentativa < 2:
            caixa = page.locator('#ask-input').first
            caixa.click(timeout=15000)
            caixa.fill(consulta)
            baseline = len(_page_text(page))
            page.keyboard.press("Enter")

            try:
                page.wait_for_function(
                    """(baseline) => {
                        const main = document.querySelector('main') || document.body;
                        return main && main.innerText && main.innerText.length > baseline + 60;
                    }""",
                    baseline,
                    timeout=120000,
                )
            except Exception:
                page.wait_for_timeout(8000)

            if _login_modal_visivel(page):
                metodo = _login_method()
                if metodo in {"google", "email"}:
                    _aplicar_login_automatico(page, metodo)
                    page.wait_for_timeout(3000)
                    tentativa += 1
                    continue

                raise RuntimeError(
                    "Sessão do Perplexity ausente ou expirada. Execute `python -m core.perplexity_web login` uma vez e tente novamente."
                )

            break

        resposta = _extrair_resposta(page, consulta)
        return resposta or "Nenhum resultado encontrado."
    finally:
        _shutdown_context()


def main() -> None:
    parser = argparse.ArgumentParser(description="Utilitários web do Perplexity")
    subparsers = parser.add_subparsers(dest="command", required=True)
    login_parser = subparsers.add_parser("login", help="Abrir o navegador para autenticar manualmente")
    login_parser.add_argument("--no-wait", action="store_true", help="Não aguardar confirmação manual")
    login_parser.add_argument("--method", choices=["manual", "google", "email"], help="Método de login a usar")

    search_parser = subparsers.add_parser("search", help="Executar uma busca")
    search_parser.add_argument("query", help="Consulta a enviar ao Perplexity")

    args = parser.parse_args()

    if args.command == "login":
        login(wait_for_user=not args.no_wait, method=args.method)
        return

    if args.command == "search":
        print(buscar_perplexity_web(args.query))


if __name__ == "__main__":
    main()
