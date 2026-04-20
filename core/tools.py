import re


def _buscar_ddgs(query: str, max_results: int):
    try:
        from duckduckgo_search import DDGS
    except ImportError as erro:
        raise RuntimeError(
            "Dependência ausente para busca web. Instale 'duckduckgo-search'."
        ) from erro

    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))

def _extrair_temperatura(texto: str):
    if not texto:
        return None
    m = re.search(r'(\d{1,2})\s*°?\s*[Cc]', texto)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d{1,2})\s*graus', texto.lower())
    if m:
        return int(m.group(1))
    return None

def _extrair_condicao(texto: str):
    if not texto:
        return None
    t = texto.lower()
    for k in ["nublado", "ensolarado", "chuva", "chuvoso", "parcialmente nublado", "tempo limpo", "céu limpo", "vento", "trovoada"]:
        if k in t:
            return k
    return None

def consulta_clima(local: str) -> str:
    local_limpo = (local or "").strip()
    if not local_limpo:
        return "Local inválido para consulta de clima."

    query = f"{local_limpo} current weather temperature hoje"
    fontes = []

    try:
        results = _buscar_ddgs(query, max_results=8)
    except Exception as e:
        return f"Erro na busca de clima: {e}"

    if not results:
        return "Nenhum resultado encontrado."

    for r in results:
        titulo = r.get("title", "")
        corpo = r.get("body", "")
        texto = f"{titulo}. {corpo}"
        temp = _extrair_temperatura(texto)
        cond = _extrair_condicao(texto)
        if temp is not None or cond is not None:
            fontes.append({
                "titulo": titulo,
                "temp": temp,
                "cond": cond,
                "texto": texto
            })

    if not fontes:
        melhor = results[0]
        return f"{melhor.get('title', 'Clima')}: {melhor.get('body', '')[:250]}"

    temperaturas = [f["temp"] for f in fontes if f["temp"] is not None]
    condicoes = [f["cond"] for f in fontes if f["cond"]]

    temp_final = temperaturas[0] if temperaturas else None
    cond_final = condicoes[0] if condicoes else None

    partes = []
    if temp_final is not None:
        partes.append(f"temperatura atual em torno de {temp_final}°C")
    if cond_final:
        partes.append(f"tempo {cond_final}")
    if not partes:
        partes.append("sem dados climáticos explícitos suficientes")

    return f"Em {local_limpo}, a {', '.join(partes)}."
    
def ferramenta_busca(query: str) -> str:
    query_limpa = (query or "").strip()
    if not query_limpa:
        return "Consulta vazia. Informe uma pergunta para pesquisar."

    try:
        results = _buscar_ddgs(query_limpa, max_results=5)
        if not results:
            return "Nenhum resultado encontrado."
        saida = []
        for r in results:
            titulo = r.get("title", "Sem título")
            corpo = r.get("body", "")
            saida.append(f"{titulo}: {corpo[:250]}...")
        return "\n".join(saida)
    except Exception as e:
        return f"Erro na busca: {e}"