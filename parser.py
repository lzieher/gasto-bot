import re
import json
import anthropic
from config import ANTHROPIC_API_KEY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM = """Sos un extractor de gastos. Dado un mensaje, devolvé SOLO este JSON sin texto extra:
{"concepto": "nombre capitalizado", "monto": numero_entero, "pagador": "nombre"}
Si no hay monto claro, usa null. Ejemplos:
"mc 5000" -> {"concepto": "McDonald's", "monto": 5000, "pagador": "Luca"}
"carrefour 20189" -> {"concepto": "Carrefour", "monto": 20189, "pagador": "Luca"}"""

_NORMALIZE = {
    "mc": "McDonald's", "mcd": "McDonald's", "mcdonalds": "McDonald's",
    "bk": "Burger King", "carrefour": "Carrefour",
    "disco": "Disco", "coto": "Coto", "dia": "Dia",
    "verdu": "Verduleria", "verduleria": "Verduleria", "verdueria": "Verduleria",
    "farmacity": "Farmacity", "rappi": "Rappi",
    "netflix": "Netflix", "spotify": "Spotify",
    "disney": "Disney+", "amazon": "Amazon",
    "barrio chino": "Barrio Chino", "pedidos ya": "PedidosYa",
}

def _regex_parse(text, sender_name):
    pagador = sender_name
    regex = r"\b(\d{1,3}(?:[.,]\d{3})+|\d+)\b"
    matches = re.findall(regex, text)
    if not matches:
        return {"concepto": text.strip().title(), "monto": None, "pagador": pagador}
    best = max(matches, key=lambda m: int(m.replace(".", "").replace(",", "")))
    monto = int(best.replace(".", "").replace(",", ""))
    concept = re.sub(re.escape(best), "", text).replace("$", "").strip()
    concept = re.sub(r"\s+", " ", concept).strip()
    concept = _NORMALIZE.get(concept.lower(), concept.title()) or "Gasto"
    return {"concepto": concept, "monto": monto, "pagador": pagador}

def parse_expense(text: str, sender_name: str = "Luca") -> dict:
    system = _SYSTEM.replace('"pagador": "nombre"', f'"pagador": "{sender_name}"')
    try:
        response = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": text}],
        )
        raw = response.content[0].text.strip()
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return _regex_parse(text, sender_name)