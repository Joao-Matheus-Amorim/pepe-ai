import os
import re
import requests
import unicodedata


# ── LOCAIS CONHECIDOS (BR + capitais mundiais) ────────────────────────────────

_LOCAIS_CONHECIDOS = {
    # ── Estados e cidades brasileiras ──────────────────────────────────────
    "minas gerais": (-19.9167, -43.9345, "Belo Horizonte", "Minas Gerais", "Brasil"),
    "belo horizonte": (-19.9167, -43.9345, "Belo Horizonte", "Minas Gerais", "Brasil"),
    "sao paulo": (-23.5505, -46.6333, "São Paulo", "São Paulo", "Brasil"),
    "são paulo": (-23.5505, -46.6333, "São Paulo", "São Paulo", "Brasil"),
    "rio de janeiro": (-22.9068, -43.1729, "Rio de Janeiro", "Rio de Janeiro", "Brasil"),
    "mage": (-22.6519, -43.0386, "Magé", "Rio de Janeiro", "Brasil"),
    "magé": (-22.6519, -43.0386, "Magé", "Rio de Janeiro", "Brasil"),
    "niteroi": (-22.8833, -43.1036, "Niterói", "Rio de Janeiro", "Brasil"),
    "niterói": (-22.8833, -43.1036, "Niterói", "Rio de Janeiro", "Brasil"),
    "salvador": (-12.9714, -38.5014, "Salvador", "Bahia", "Brasil"),
    "bahia": (-12.9714, -38.5014, "Salvador", "Bahia", "Brasil"),
    "fortaleza": (-3.7172, -38.5433, "Fortaleza", "Ceará", "Brasil"),
    "ceara": (-3.7172, -38.5433, "Fortaleza", "Ceará", "Brasil"),
    "ceará": (-3.7172, -38.5433, "Fortaleza", "Ceará", "Brasil"),
    "curitiba": (-25.4297, -49.2711, "Curitiba", "Paraná", "Brasil"),
    "parana": (-25.4297, -49.2711, "Curitiba", "Paraná", "Brasil"),
    "paraná": (-25.4297, -49.2711, "Curitiba", "Paraná", "Brasil"),
    "recife": (-8.0539, -34.8811, "Recife", "Pernambuco", "Brasil"),
    "pernambuco": (-8.0539, -34.8811, "Recife", "Pernambuco", "Brasil"),
    "manaus": (-3.1019, -60.0250, "Manaus", "Amazonas", "Brasil"),
    "amazonas": (-3.1019, -60.0250, "Manaus", "Amazonas", "Brasil"),
    "porto alegre": (-30.0346, -51.2177, "Porto Alegre", "Rio Grande do Sul", "Brasil"),
    "rio grande do sul": (-30.0346, -51.2177, "Porto Alegre", "Rio Grande do Sul", "Brasil"),
    "brasilia": (-15.7801, -47.9292, "Brasília", "Distrito Federal", "Brasil"),
    "brasília": (-15.7801, -47.9292, "Brasília", "Distrito Federal", "Brasil"),
    "distrito federal": (-15.7801, -47.9292, "Brasília", "Distrito Federal", "Brasil"),
    "belem": (-1.4558, -48.5044, "Belém", "Pará", "Brasil"),
    "belém": (-1.4558, -48.5044, "Belém", "Pará", "Brasil"),
    "para": (-1.4558, -48.5044, "Belém", "Pará", "Brasil"),
    "pará": (-1.4558, -48.5044, "Belém", "Pará", "Brasil"),
    "florianopolis": (-27.5954, -48.5480, "Florianópolis", "Santa Catarina", "Brasil"),
    "florianópolis": (-27.5954, -48.5480, "Florianópolis", "Santa Catarina", "Brasil"),
    "santa catarina": (-27.5954, -48.5480, "Florianópolis", "Santa Catarina", "Brasil"),
    "goiania": (-16.6869, -49.2648, "Goiânia", "Goiás", "Brasil"),
    "goiânia": (-16.6869, -49.2648, "Goiânia", "Goiás", "Brasil"),
    "goias": (-16.6869, -49.2648, "Goiânia", "Goiás", "Brasil"),
    "goiás": (-16.6869, -49.2648, "Goiânia", "Goiás", "Brasil"),
    "maceio": (-9.6658, -35.7350, "Maceió", "Alagoas", "Brasil"),
    "maceió": (-9.6658, -35.7350, "Maceió", "Alagoas", "Brasil"),
    "alagoas": (-9.6658, -35.7350, "Maceió", "Alagoas", "Brasil"),
    "natal": (-5.7945, -35.2110, "Natal", "Rio Grande do Norte", "Brasil"),
    "rio grande do norte": (-5.7945, -35.2110, "Natal", "Rio Grande do Norte", "Brasil"),
    "campo grande": (-20.4697, -54.6201, "Campo Grande", "Mato Grosso do Sul", "Brasil"),
    "mato grosso do sul": (-20.4697, -54.6201, "Campo Grande", "Mato Grosso do Sul", "Brasil"),
    "cuiaba": (-15.5989, -56.0949, "Cuiabá", "Mato Grosso", "Brasil"),
    "cuiabá": (-15.5989, -56.0949, "Cuiabá", "Mato Grosso", "Brasil"),
    "mato grosso": (-15.5989, -56.0949, "Cuiabá", "Mato Grosso", "Brasil"),
    "teresina": (-5.0892, -42.8019, "Teresina", "Piauí", "Brasil"),
    "piaui": (-5.0892, -42.8019, "Teresina", "Piauí", "Brasil"),
    "piauí": (-5.0892, -42.8019, "Teresina", "Piauí", "Brasil"),
    "joao pessoa": (-7.1195, -34.8450, "João Pessoa", "Paraíba", "Brasil"),
    "joão pessoa": (-7.1195, -34.8450, "João Pessoa", "Paraíba", "Brasil"),
    "paraiba": (-7.1195, -34.8450, "João Pessoa", "Paraíba", "Brasil"),
    "paraíba": (-7.1195, -34.8450, "João Pessoa", "Paraíba", "Brasil"),
    "aracaju": (-10.9472, -37.0731, "Aracaju", "Sergipe", "Brasil"),
    "sergipe": (-10.9472, -37.0731, "Aracaju", "Sergipe", "Brasil"),
    "porto velho": (-8.7612, -63.9004, "Porto Velho", "Rondônia", "Brasil"),
    "rondonia": (-8.7612, -63.9004, "Porto Velho", "Rondônia", "Brasil"),
    "rondônia": (-8.7612, -63.9004, "Porto Velho", "Rondônia", "Brasil"),
    "macapa": (0.0356, -51.0705, "Macapá", "Amapá", "Brasil"),
    "macapá": (0.0356, -51.0705, "Macapá", "Amapá", "Brasil"),
    "amapa": (0.0356, -51.0705, "Macapá", "Amapá", "Brasil"),
    "amapá": (0.0356, -51.0705, "Macapá", "Amapá", "Brasil"),
    "boa vista": (2.8235, -60.6758, "Boa Vista", "Roraima", "Brasil"),
    "roraima": (2.8235, -60.6758, "Boa Vista", "Roraima", "Brasil"),
    "rio branco": (-9.9754, -67.8249, "Rio Branco", "Acre", "Brasil"),
    "acre": (-9.9754, -67.8249, "Rio Branco", "Acre", "Brasil"),
    "palmas": (-10.2491, -48.3243, "Palmas", "Tocantins", "Brasil"),
    "tocantins": (-10.2491, -48.3243, "Palmas", "Tocantins", "Brasil"),
    "sao luis": (-2.5297, -44.3028, "São Luís", "Maranhão", "Brasil"),
    "são luís": (-2.5297, -44.3028, "São Luís", "Maranhão", "Brasil"),
    "maranhao": (-2.5297, -44.3028, "São Luís", "Maranhão", "Brasil"),
    "maranhão": (-2.5297, -44.3028, "São Luís", "Maranhão", "Brasil"),
    "vitoria": (-20.3155, -40.3128, "Vitória", "Espírito Santo", "Brasil"),
    "vitória": (-20.3155, -40.3128, "Vitória", "Espírito Santo", "Brasil"),
    "espirito santo": (-20.3155, -40.3128, "Vitória", "Espírito Santo", "Brasil"),
    "espírito santo": (-20.3155, -40.3128, "Vitória", "Espírito Santo", "Brasil"),
    "duque de caxias": (-22.7856, -43.3117, "Duque de Caxias", "Rio de Janeiro", "Brasil"),
    "nova iguacu": (-22.7592, -43.4511, "Nova Iguaçu", "Rio de Janeiro", "Brasil"),
    "nova iguaçu": (-22.7592, -43.4511, "Nova Iguaçu", "Rio de Janeiro", "Brasil"),
    "petropolis": (-22.5050, -43.1786, "Petrópolis", "Rio de Janeiro", "Brasil"),
    "petrópolis": (-22.5050, -43.1786, "Petrópolis", "Rio de Janeiro", "Brasil"),
    "volta redonda": (-22.5231, -44.1040, "Volta Redonda", "Rio de Janeiro", "Brasil"),
    "campos dos goytacazes": (-21.7545, -41.3244, "Campos dos Goytacazes", "Rio de Janeiro", "Brasil"),
    "angra dos reis": (-23.0067, -44.3181, "Angra dos Reis", "Rio de Janeiro", "Brasil"),
    "cabo frio": (-22.8794, -42.0186, "Cabo Frio", "Rio de Janeiro", "Brasil"),
    "buzios": (-22.7469, -41.8816, "Búzios", "Rio de Janeiro", "Brasil"),
    "búzios": (-22.7469, -41.8816, "Búzios", "Rio de Janeiro", "Brasil"),
    "sao goncalo": (-22.8269, -43.0539, "São Gonçalo", "Rio de Janeiro", "Brasil"),
    "são gonçalo": (-22.8269, -43.0539, "São Gonçalo", "Rio de Janeiro", "Brasil"),
    "campinas": (-22.9056, -47.0608, "Campinas", "São Paulo", "Brasil"),
    "santos": (-23.9608, -46.3336, "Santos", "São Paulo", "Brasil"),
    "ribeirao preto": (-21.1775, -47.8103, "Ribeirão Preto", "São Paulo", "Brasil"),
    "ribeirão preto": (-21.1775, -47.8103, "Ribeirão Preto", "São Paulo", "Brasil"),
    "sorocaba": (-23.5015, -47.4526, "Sorocaba", "São Paulo", "Brasil"),
    "sao jose dos campos": (-23.1794, -45.8869, "São José dos Campos", "São Paulo", "Brasil"),
    "são josé dos campos": (-23.1794, -45.8869, "São José dos Campos", "São Paulo", "Brasil"),
    "uberlandia": (-18.9186, -48.2772, "Uberlândia", "Minas Gerais", "Brasil"),
    "uberlândia": (-18.9186, -48.2772, "Uberlândia", "Minas Gerais", "Brasil"),
    "contagem": (-19.9317, -44.0536, "Contagem", "Minas Gerais", "Brasil"),
    "juiz de fora": (-21.7642, -43.3503, "Juiz de Fora", "Minas Gerais", "Brasil"),
    "joinville": (-26.3044, -48.8487, "Joinville", "Santa Catarina", "Brasil"),
    "blumenau": (-26.9194, -49.0661, "Blumenau", "Santa Catarina", "Brasil"),
    "londrina": (-23.3045, -51.1696, "Londrina", "Paraná", "Brasil"),
    "maringa": (-23.4273, -51.9375, "Maringá", "Paraná", "Brasil"),
    "maringá": (-23.4273, -51.9375, "Maringá", "Paraná", "Brasil"),
    "feira de santana": (-12.2664, -38.9663, "Feira de Santana", "Bahia", "Brasil"),
    "ilheus": (-14.7890, -39.0428, "Ilhéus", "Bahia", "Brasil"),
    "ilhéus": (-14.7890, -39.0428, "Ilhéus", "Bahia", "Brasil"),
    "porto seguro": (-16.4497, -39.0642, "Porto Seguro", "Bahia", "Brasil"),
    "mossoro": (-5.1878, -37.3444, "Mossoró", "Rio Grande do Norte", "Brasil"),
    "mossoró": (-5.1878, -37.3444, "Mossoró", "Rio Grande do Norte", "Brasil"),
    "caruaru": (-8.2760, -35.9753, "Caruaru", "Pernambuco", "Brasil"),
    "olinda": (-8.0089, -34.8553, "Olinda", "Pernambuco", "Brasil"),
    "macae": (-22.3711, -41.7869, "Macaé", "Rio de Janeiro", "Brasil"),
    "macaé": (-22.3711, -41.7869, "Macaé", "Rio de Janeiro", "Brasil"),
    "piabeta": (-22.6519, -43.0386, "Piabetá", "Rio de Janeiro", "Brasil"),
    "piabetá": (-22.6519, -43.0386, "Piabetá", "Rio de Janeiro", "Brasil"),

    # ── Capitais e países mundiais ─────────────────────────────────────────
    "china": (39.9042, 116.4074, "Pequim", "Pequim", "China"),
    "pequim": (39.9042, 116.4074, "Pequim", "Pequim", "China"),
    "beijing": (39.9042, 116.4074, "Pequim", "Pequim", "China"),
    "xangai": (31.2304, 121.4737, "Xangai", "Xangai", "China"),
    "shanghai": (31.2304, 121.4737, "Xangai", "Xangai", "China"),
    "japao": (35.6762, 139.6503, "Tóquio", "Tóquio", "Japão"),
    "japão": (35.6762, 139.6503, "Tóquio", "Tóquio", "Japão"),
    "japan": (35.6762, 139.6503, "Tóquio", "Tóquio", "Japão"),
    "toquio": (35.6762, 139.6503, "Tóquio", "Tóquio", "Japão"),
    "tóquio": (35.6762, 139.6503, "Tóquio", "Tóquio", "Japão"),
    "tokyo": (35.6762, 139.6503, "Tóquio", "Tóquio", "Japão"),
    "franca": (48.8566, 2.3522, "Paris", "Île-de-France", "França"),
    "frança": (48.8566, 2.3522, "Paris", "Île-de-France", "França"),
    "france": (48.8566, 2.3522, "Paris", "Île-de-France", "França"),
    "paris": (48.8566, 2.3522, "Paris", "Île-de-France", "França"),
    "alemanha": (52.5200, 13.4050, "Berlim", "Berlim", "Alemanha"),
    "germany": (52.5200, 13.4050, "Berlim", "Berlim", "Alemanha"),
    "berlim": (52.5200, 13.4050, "Berlim", "Berlim", "Alemanha"),
    "berlin": (52.5200, 13.4050, "Berlim", "Berlim", "Alemanha"),
    "italia": (41.9028, 12.4964, "Roma", "Lácio", "Itália"),
    "itália": (41.9028, 12.4964, "Roma", "Lácio", "Itália"),
    "italy": (41.9028, 12.4964, "Roma", "Lácio", "Itália"),
    "roma": (41.9028, 12.4964, "Roma", "Lácio", "Itália"),
    "rome": (41.9028, 12.4964, "Roma", "Lácio", "Itália"),
    "espanha": (40.4168, -3.7038, "Madri", "Comunidade de Madri", "Espanha"),
    "spain": (40.4168, -3.7038, "Madri", "Comunidade de Madri", "Espanha"),
    "madri": (40.4168, -3.7038, "Madri", "Comunidade de Madri", "Espanha"),
    "madrid": (40.4168, -3.7038, "Madri", "Comunidade de Madri", "Espanha"),
    "portugal": (38.7169, -9.1395, "Lisboa", "Lisboa", "Portugal"),
    "lisboa": (38.7169, -9.1395, "Lisboa", "Lisboa", "Portugal"),
    "lisbon": (38.7169, -9.1395, "Lisboa", "Lisboa", "Portugal"),
    "argentina": (-34.6037, -58.3816, "Buenos Aires", "Buenos Aires", "Argentina"),
    "buenos aires": (-34.6037, -58.3816, "Buenos Aires", "Buenos Aires", "Argentina"),
    "chile": (-33.4489, -70.6693, "Santiago", "Santiago", "Chile"),
    "santiago": (-33.4489, -70.6693, "Santiago", "Santiago", "Chile"),
    "colombia": (4.7110, -74.0721, "Bogotá", "Bogotá", "Colômbia"),
    "colômbia": (4.7110, -74.0721, "Bogotá", "Bogotá", "Colômbia"),
    "bogota": (4.7110, -74.0721, "Bogotá", "Bogotá", "Colômbia"),
    "bogotá": (4.7110, -74.0721, "Bogotá", "Bogotá", "Colômbia"),
    "peru": (-12.0464, -77.0428, "Lima", "Lima", "Peru"),
    "lima": (-12.0464, -77.0428, "Lima", "Lima", "Peru"),
    "mexico": (19.4326, -99.1332, "Cidade do México", "CDMX", "México"),
    "méxico": (19.4326, -99.1332, "Cidade do México", "CDMX", "México"),
    "estados unidos": (38.9072, -77.0369, "Washington D.C.", "D.C.", "EUA"),
    "eua": (38.9072, -77.0369, "Washington D.C.", "D.C.", "EUA"),
    "usa": (40.7128, -74.0060, "Nova York", "Nova York", "EUA"),
    "nova york": (40.7128, -74.0060, "Nova York", "Nova York", "EUA"),
    "new york": (40.7128, -74.0060, "Nova York", "Nova York", "EUA"),
    "washington": (38.9072, -77.0369, "Washington D.C.", "D.C.", "EUA"),
    "los angeles": (34.0522, -118.2437, "Los Angeles", "Califórnia", "EUA"),
    "miami": (25.7617, -80.1918, "Miami", "Flórida", "EUA"),
    "canada": (45.4215, -75.6919, "Ottawa", "Ontário", "Canadá"),
    "canadá": (45.4215, -75.6919, "Ottawa", "Ontário", "Canadá"),
    "toronto": (43.6510, -79.3470, "Toronto", "Ontário", "Canadá"),
    "russia": (55.7558, 37.6173, "Moscou", "Moscou", "Rússia"),
    "rússia": (55.7558, 37.6173, "Moscou", "Moscou", "Rússia"),
    "moscou": (55.7558, 37.6173, "Moscou", "Moscou", "Rússia"),
    "moscow": (55.7558, 37.6173, "Moscou", "Moscou", "Rússia"),
    "australia": (-35.2809, 149.1300, "Canberra", "ACT", "Austrália"),
    "austrália": (-35.2809, 149.1300, "Canberra", "ACT", "Austrália"),
    "sydney": (-33.8688, 151.2093, "Sydney", "Nova Gales do Sul", "Austrália"),
    "india": (28.6139, 77.2090, "Nova Délhi", "Délhi", "Índia"),
    "índia": (28.6139, 77.2090, "Nova Délhi", "Délhi", "Índia"),
    "nova delhi": (28.6139, 77.2090, "Nova Délhi", "Délhi", "Índia"),
    "mumbai": (19.0760, 72.8777, "Mumbai", "Maharashtra", "Índia"),
    "reino unido": (51.5074, -0.1278, "Londres", "Inglaterra", "Reino Unido"),
    "inglaterra": (51.5074, -0.1278, "Londres", "Inglaterra", "Reino Unido"),
    "uk": (51.5074, -0.1278, "Londres", "Inglaterra", "Reino Unido"),
    "londres": (51.5074, -0.1278, "Londres", "Inglaterra", "Reino Unido"),
    "london": (51.5074, -0.1278, "Londres", "Inglaterra", "Reino Unido"),
    "congo": (-4.3217, 15.3222, "Kinshasa", "Kinshasa", "Congo (RDC)"),
    "kinshasa": (-4.3217, 15.3222, "Kinshasa", "Kinshasa", "Congo (RDC)"),
    "africa do sul": (-25.7479, 28.2293, "Pretória", "Gauteng", "África do Sul"),
    "áfrica do sul": (-25.7479, 28.2293, "Pretória", "Gauteng", "África do Sul"),
    "south africa": (-25.7479, 28.2293, "Pretória", "Gauteng", "África do Sul"),
    "nigeria": (9.0765, 7.3986, "Abuja", "FCT", "Nigéria"),
    "nigéria": (9.0765, 7.3986, "Abuja", "FCT", "Nigéria"),
    "egito": (30.0444, 31.2357, "Cairo", "Cairo", "Egito"),
    "egypt": (30.0444, 31.2357, "Cairo", "Cairo", "Egito"),
    "cairo": (30.0444, 31.2357, "Cairo", "Cairo", "Egito"),
    "turquia": (39.9334, 32.8597, "Ancara", "Ancara", "Turquia"),
    "turkey": (39.9334, 32.8597, "Ancara", "Ancara", "Turquia"),
    "coreia do sul": (37.5665, 126.9780, "Seul", "Seul", "Coreia do Sul"),
    "coreia": (37.5665, 126.9780, "Seul", "Seul", "Coreia do Sul"),
    "korea": (37.5665, 126.9780, "Seul", "Seul", "Coreia do Sul"),
    "seul": (37.5665, 126.9780, "Seul", "Seul", "Coreia do Sul"),
    "seoul": (37.5665, 126.9780, "Seul", "Seul", "Coreia do Sul"),
    "holanda": (52.3676, 4.9041, "Amsterdã", "Holanda do Norte", "Países Baixos"),
    "amsterdam": (52.3676, 4.9041, "Amsterdã", "Holanda do Norte", "Países Baixos"),
    "amsterdã": (52.3676, 4.9041, "Amsterdã", "Holanda do Norte", "Países Baixos"),
    "suecia": (59.3293, 18.0686, "Estocolmo", "Estocolmo", "Suécia"),
    "suécia": (59.3293, 18.0686, "Estocolmo", "Estocolmo", "Suécia"),
    "estocolmo": (59.3293, 18.0686, "Estocolmo", "Estocolmo", "Suécia"),
    "noruega": (59.9139, 10.7522, "Oslo", "Oslo", "Noruega"),
    "oslo": (59.9139, 10.7522, "Oslo", "Oslo", "Noruega"),
    "suica": (46.9481, 7.4474, "Berna", "Berna", "Suíça"),
    "suíça": (46.9481, 7.4474, "Berna", "Berna", "Suíça"),
    "polonia": (52.2297, 21.0122, "Varsóvia", "Mazóvia", "Polônia"),
    "polônia": (52.2297, 21.0122, "Varsóvia", "Mazóvia", "Polônia"),
    "grecia": (37.9838, 23.7275, "Atenas", "Ática", "Grécia"),
    "grécia": (37.9838, 23.7275, "Atenas", "Ática", "Grécia"),
    "atenas": (37.9838, 23.7275, "Atenas", "Ática", "Grécia"),
    "tailandia": (13.7563, 100.5018, "Bangkok", "Bangkok", "Tailândia"),
    "tailândia": (13.7563, 100.5018, "Bangkok", "Bangkok", "Tailândia"),
    "bangkok": (13.7563, 100.5018, "Bangkok", "Bangkok", "Tailândia"),
    "indonesia": (-6.2088, 106.8456, "Jacarta", "Jacarta", "Indonésia"),
    "indonésia": (-6.2088, 106.8456, "Jacarta", "Jacarta", "Indonésia"),
    "singapura": (1.3521, 103.8198, "Singapura", "", "Singapura"),
    "singapore": (1.3521, 103.8198, "Singapura", "", "Singapura"),
    "dubai": (25.2048, 55.2708, "Dubai", "Dubai", "Emirados Árabes"),
    "emirados": (25.2048, 55.2708, "Dubai", "Dubai", "Emirados Árabes"),
    "israel": (31.7683, 35.2137, "Jerusalém", "Jerusalém", "Israel"),
    "venezuela": (10.4806, -66.9036, "Caracas", "Distrito Capital", "Venezuela"),
    "caracas": (10.4806, -66.9036, "Caracas", "Distrito Capital", "Venezuela"),
    "bolivia": (-16.5000, -68.1500, "La Paz", "La Paz", "Bolívia"),
    "bolívia": (-16.5000, -68.1500, "La Paz", "La Paz", "Bolívia"),
    "paraguai": (-25.2867, -57.6470, "Assunção", "Assunção", "Paraguai"),
    "uruguai": (-34.9011, -56.1645, "Montevidéu", "Montevidéu", "Uruguai"),
    "montevideu": (-34.9011, -56.1645, "Montevidéu", "Montevidéu", "Uruguai"),
    "marrocos": (33.9716, -6.8498, "Rabat", "Rabat", "Marrocos"),
    "morocco": (33.9716, -6.8498, "Rabat", "Rabat", "Marrocos"),
    "africa": (-8.7832, 34.5085, "África", "", "África"),
    "europa": (54.5260, 15.2551, "Europa", "", "Europa"),
}


# ── HTTP ──────────────────────────────────────────────────────────────────────

def _http_get_json(url: str, params: dict, timeout: int = 6) -> dict:
    for tentativa in range(2):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.Timeout:
            if tentativa == 1:
                raise
        except requests.HTTPError as e:
            raise RuntimeError(f"Erro HTTP {e.response.status_code}: {url}") from e


# ── GEOCODING ─────────────────────────────────────────────────────────────────

def _remover_acentos(texto: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", texto)
        if unicodedata.category(ch) != "Mn"
    )


def _normalizar_chave_local(local: str) -> str:
    chave = _remover_acentos(local.strip().lower())
    chave = re.sub(
        r"\s+(no|na|nos|nas)\s+(norte|sul|sudeste|nordeste|centro|oeste|leste|"
        r"regiao|região|interior|litoral|brasil|brazil)\b.*",
        "",
        chave,
    )
    chave = re.sub(
        r"\s*,?\s*(brasil|brazil|rj|sp|mg|ba|rs|pr|sc|ce|pe|am|df|"
        r"go|mt|ms|pa|pb|pi|rn|ro|rr|se|to|al|ap|ac|ma|es)$",
        "",
        chave,
    ).strip()
    return chave


def _candidatos_local(local: str) -> list[str]:
    base = _normalizar_chave_local(local)
    sem_acentos = _remover_acentos(base)
    candidatos = [local.strip(), base, sem_acentos]

    base_lower = sem_acentos.lower()
    if "piabeta" in base_lower and "mage" not in base_lower:
        candidatos.extend(["piabeta mage", "mage rio de janeiro", "mage"])
    elif "mage" in base_lower:
        candidatos.extend(["mage rio de janeiro", "mage"])
    elif "niteroi" in base_lower:
        candidatos.extend(["niteroi rio de janeiro", "niteroi"])

    unicos = []
    vistos = set()
    for candidato in candidatos:
        valor = candidato.strip()
        if valor and valor.lower() not in vistos:
            unicos.append(valor)
            vistos.add(valor.lower())
    return unicos


def _buscar_local_conhecido(local: str) -> dict | None:
    chave = _normalizar_chave_local(local)

    if chave in _LOCAIS_CONHECIDOS:
        lat, lon, nome, admin1, pais = _LOCAIS_CONHECIDOS[chave]
        return {"latitude": lat, "longitude": lon,
                "name": nome, "admin1": admin1, "country": pais}

    chave_sem = _remover_acentos(chave)
    if chave_sem in _LOCAIS_CONHECIDOS:
        lat, lon, nome, admin1, pais = _LOCAIS_CONHECIDOS[chave_sem]
        return {"latitude": lat, "longitude": lon,
                "name": nome, "admin1": admin1, "country": pais}

    return None


def _geocodificar(local: str) -> dict:
    # 1. Locais conhecidos (zero ambiguidade)
    conhecido = _buscar_local_conhecido(local)
    if conhecido:
        return conhecido

    # 2. Geocoding global para cidades não mapeadas
    tentativas = _candidatos_local(local)

    for consulta in tentativas:
        if not consulta:
            continue
        dados = _http_get_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            {"name": consulta, "count": 5, "language": "pt", "format": "json"},
        )
        resultados = dados.get("results") or []
        if resultados:
            return _escolher_melhor_resultado(local, resultados)

    return {}


def _escolher_melhor_resultado(local_original: str, resultados: list[dict]) -> dict:
    texto = _remover_acentos(local_original.lower())

    paises = {
        "eua": "US", "usa": "US", "estados unidos": "US", "united states": "US",
        "reino unido": "GB", "uk": "GB", "england": "GB", "inglaterra": "GB",
        "franca": "FR", "france": "FR",
        "japao": "JP", "japan": "JP",
        "alemanha": "DE", "germany": "DE",
        "italia": "IT", "italy": "IT",
        "espanha": "ES", "spain": "ES",
        "portugal": "PT",
        "argentina": "AR",
        "china": "CN",
        "india": "IN",
        "australia": "AU",
        "canada": "CA",
        "mexico": "MX",
        "russia": "RU",
        "coreia": "KR", "korea": "KR",
        "turquia": "TR", "turkey": "TR",
        "holanda": "NL", "netherlands": "NL",
        "belgica": "BE", "belgium": "BE",
        "suica": "CH", "switzerland": "CH",
        "austria": "AT",
        "suecia": "SE", "sweden": "SE",
        "noruega": "NO", "norway": "NO",
        "dinamarca": "DK", "denmark": "DK",
        "finlandia": "FI", "finland": "FI",
        "polonia": "PL", "poland": "PL",
        "ucrania": "UA", "ukraine": "UA",
        "grecia": "GR", "greece": "GR",
        "colombia": "CO",
        "chile": "CL",
        "peru": "PE",
        "venezuela": "VE",
        "paraguai": "PY", "paraguay": "PY",
        "uruguai": "UY", "uruguay": "UY",
        "bolivia": "BO",
        "africa do sul": "ZA", "south africa": "ZA",
        "nigeria": "NG",
        "egito": "EG", "egypt": "EG",
        "marrocos": "MA", "morocco": "MA",
        "arabia saudita": "SA", "saudi arabia": "SA",
        "emirados": "AE", "uae": "AE",
        "israel": "IL",
        "tailandia": "TH", "thailand": "TH",
        "vietnam": "VN",
        "indonesia": "ID",
        "filipinas": "PH", "philippines": "PH",
        "singapura": "SG", "singapore": "SG",
        "nova zelandia": "NZ", "new zealand": "NZ",
    }

    codigo_pais = None
    for nome_pais, codigo in paises.items():
        if nome_pais in texto:
            codigo_pais = codigo
            break

    if codigo_pais:
        for r in resultados:
            if (r.get("country_code") or "").upper() == codigo_pais:
                return r

    return resultados[0]


# ── DESCRIÇÃO DO TEMPO ────────────────────────────────────────────────────────

_DESCRICAO_TEMPO = {
    0: "céu limpo", 1: "predominantemente limpo", 2: "parcialmente nublado",
    3: "nublado", 45: "nevoeiro", 48: "nevoeiro com geada",
    51: "garoa fraca", 53: "garoa moderada", 55: "garoa forte",
    56: "garoa congelante fraca", 57: "garoa congelante forte",
    61: "chuva fraca", 63: "chuva moderada", 65: "chuva forte",
    66: "chuva congelante fraca", 67: "chuva congelante forte",
    71: "neve fraca", 73: "neve moderada", 75: "neve forte",
    77: "flocos de neve", 80: "pancadas de chuva fracas",
    81: "pancadas de chuva moderadas", 82: "pancadas de chuva fortes",
    85: "pancadas de neve fracas", 86: "pancadas de neve fortes",
    95: "trovoada", 96: "trovoada com granizo fraco",
    99: "trovoada com granizo forte",
}


# ── CONSULTA DE CLIMA ─────────────────────────────────────────────────────────

def consulta_clima(local: str) -> str:
    local_limpo = (local or "").strip()
    if not local_limpo:
        return "Local inválido para consulta de clima."

    try:
        lugar = _geocodificar(local_limpo)
        if not lugar:
            return (
                f"Não encontrei '{local_limpo}'. "
                f"Tente ser mais específico (ex: 'Belo Horizonte, MG' ou 'Paris, França')."
            )

        lat = lugar.get("latitude")
        lon = lugar.get("longitude")
        if lat is None or lon is None:
            return f"Não foi possível obter coordenadas para '{local_limpo}'."

        previsao = _http_get_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "temperature_2m,apparent_temperature,weather_code,"
                    "wind_speed_10m,relative_humidity_2m,precipitation"
                ),
                "timezone": "auto",
            },
        )

        atual = previsao.get("current") or {}
        temp = atual.get("temperature_2m")
        sensacao = atual.get("apparent_temperature")
        codigo = atual.get("weather_code")
        vento = atual.get("wind_speed_10m")
        umidade = atual.get("relative_humidity_2m")
        chuva = atual.get("precipitation")

        if temp is None and codigo is None:
            return f"Dados de clima indisponíveis para '{local_limpo}'."

        nome = lugar.get("name") or local_limpo
        admin1 = lugar.get("admin1") or ""
        pais = lugar.get("country") or ""

        partes_local = [nome]
        if admin1 and admin1.lower() != nome.lower():
            partes_local.append(admin1)
        if pais and pais.lower() not in nome.lower():
            partes_local.append(pais)
        localizacao = ", ".join(partes_local)

        partes_clima = []
        if temp is not None:
            linha = f"{temp}°C"
            if sensacao is not None and abs(sensacao - temp) >= 2:
                linha += f" (sensação: {sensacao}°C)"
            partes_clima.append(linha)
        if codigo is not None:
            partes_clima.append(_DESCRICAO_TEMPO.get(codigo, "condição indisponível"))
        if umidade is not None:
            partes_clima.append(f"umidade {umidade}%")
        if chuva is not None and chuva > 0:
            partes_clima.append(f"chuva {chuva} mm")
        if vento is not None:
            partes_clima.append(f"vento {vento} km/h")

        return f"Em {localizacao}, agora: {', '.join(partes_clima)}."

    except requests.RequestException as e:
        return f"Erro de conexão ao consultar clima: {e}"
    except Exception as e:
        return f"Erro inesperado ao consultar clima: {e}"


# ── EXTRAÇÃO DE LOCAL VIA LLM ─────────────────────────────────────────────────

def extrair_local_com_llm(pergunta: str) -> str | None:
    try:
        from core.llm import criar_llm
        llm = criar_llm()
        prompt = (
            "Extraia APENAS o nome da cidade, região ou país mencionado na pergunta abaixo. "
            "Responda somente com o nome geográfico, sem explicações, sem pontuação extra. "
            "Não extraia palavras como 'também', 'agora', 'hoje', 'lá', 'ali', 'aqui'. "
            "Se não houver cidade/região/país clara, responda exatamente: NENHUM\n\n"
            f"Pergunta: {pergunta}"
        )
        resposta = llm.invoke(prompt)
        texto = (resposta.content or "").strip().strip(".")
        if not texto or texto.upper() == "NENHUM":
            return None
        return texto
    except Exception:
        return None


# ── BUSCA WEB ─────────────────────────────────────────────────────────────────

def _buscar_ddgs(query: str, max_results: int):
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError as e:
            raise RuntimeError("Instale 'ddgs': pip install ddgs") from e

    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


def _pegar_texto_resultado(r: dict) -> str:
    return (
        r.get("body") or r.get("snippet")
        or r.get("content") or r.get("description") or ""
    )


def _formatar_resultados_ddgs(results: list[dict]) -> str:
    return "\n".join(
        f"{r.get('title', 'Sem título')}: {_pegar_texto_resultado(r)[:250]}..."
        for r in results
    )


def _buscar_perplexity(query: str) -> str:
    from core.perplexity_web import buscar_perplexity_web

    return buscar_perplexity_web(query)


def ferramenta_busca(query: str) -> str:
    query_limpa = (query or "").strip()
    if not query_limpa:
        return "Consulta vazia."

    try:
        provider_busca = os.getenv("PEPE_SEARCH_PROVIDER", "perplexity").strip().lower()
        if provider_busca == "perplexity":
            try:
                return _buscar_perplexity(query_limpa)
            except Exception as erro:
                mensagem = str(erro)
                if "não autenticada" in mensagem.lower() or "expirou" in mensagem.lower():
                    return (
                        "Sessão do Perplexity ausente ou expirada. "
                        "Execute `python -m core.perplexity_web login` uma vez e tente novamente."
                    )
                if os.getenv("PEPE_SEARCH_FALLBACK_DDGS", "true").strip().lower() in {"1", "true", "yes", "sim", "on"}:
                    results = _buscar_ddgs(query_limpa, max_results=5)
                    if not results:
                        return f"Perplexity indisponível e nenhum resultado no fallback DDGS: {erro}"
                    return _formatar_resultados_ddgs(results)
                return f"Erro na busca Perplexity: {erro}"

        results = _buscar_ddgs(query_limpa, max_results=5)
        if not results:
            return "Nenhum resultado encontrado."

        return _formatar_resultados_ddgs(results)
    except Exception as e:
        return f"Erro na busca: {e}"
