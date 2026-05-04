import re

# Matches numbers with Argentine thousand separators (27.540) or plain integers
_AMOUNT_RE = re.compile(r"\b(\d{1,3}(?:[.,]\d{3})+|\d+)\b")

_PREFIX_RE = re.compile(
    r"^(pagu[eé]\s+(en\s+)?|compr[eé]\s+(en\s+)?|gast[eé]\s+(en\s+)?)",
    re.IGNORECASE,
)

# Known abbreviations and common names → display name
_NORMALIZE = {
    "mc": "McDonald's",
    "mcd": "McDonald's",
    "mcdonalds": "McDonald's",
    "mcdonald's": "McDonald's",
    "bk": "Burger King",
    "carrefour": "Carrefour",
    "disco": "Disco",
    "coto": "Coto",
    "dia": "Día",
    "verdu": "Verdulería",
    "verduleria": "Verdulería",
    "verdueria": "Verdulería",
    "verdulería": "Verdulería",
    "farmacity": "Farmacity",
    "farmacia": "Farmacia",
    "rappi": "Rappi",
    "netflix": "Netflix",
    "spotify": "Spotify",
    "disney": "Disney+",
    "disney+": "Disney+",
    "hbo": "HBO Max",
    "amazon": "Amazon",
    "uala": "Ualá",
    "barrio chino": "Barrio Chino",
    "pedidos ya": "PedidosYa",
    "mercado libre": "MercadoLibre",
    "kiosco": "Kiosco",
    "kiosko": "Kiosco",
    "panaderia": "Panadería",
    "panadería": "Panadería",
}


def _to_int(s: str) -> int:
    return int(s.replace(".", "").replace(",", ""))


def parse_expense(text: str) -> dict:
    # Detect payer
    pagador = "Luca"
    if re.search(r"\bmorita\b", text, re.IGNORECASE):
        pagador = "Morita"

    # Find all number candidates and pick the largest (most likely the price)
    matches = _AMOUNT_RE.findall(text)
    if not matches:
        return {"concepto": text.strip().title(), "monto": None, "pagador": pagador}

    best = max(matches, key=lambda m: _to_int(m))
    monto = _to_int(best)

    # Build concept: remove amount, payer, $ signs, and verbal prefixes
    concept = re.sub(re.escape(best), "", text, count=1)
    concept = re.sub(r"\bmorita\b", "", concept, flags=re.IGNORECASE)
    concept = concept.replace("$", "")
    concept = _PREFIX_RE.sub("", concept.strip())
    concept = re.sub(r"\s+", " ", concept).strip()

    # Normalize known names, otherwise title-case
    concept_key = concept.lower().strip()
    if concept_key in _NORMALIZE:
        concept = _NORMALIZE[concept_key]
    elif concept:
        concept = concept.title()
    else:
        concept = "Gasto"

    return {"concepto": concept, "monto": monto, "pagador": pagador}
