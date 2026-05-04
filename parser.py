import json
import anthropic
from config import ANTHROPIC_API_KEY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM = """Sos un extractor de gastos domésticos en pesos argentinos.
Dado un mensaje en español, extraé exactamente 3 campos y devolvé SOLO un JSON válido, sin texto extra:

{
  "concepto": "nombre del lugar o servicio, capitalizado correctamente",
  "monto": número entero limpio (sin puntos ni comas),
  "pagador": el nombre que se pase como default
}

Si no podés identificar el monto con certeza, devolvé "monto": null.

Reglas para el concepto:
- Corregí la ortografía (ej: "verdueria" → "Verdulería")
- Usá nombres reconocibles (ej: "mc" → "McDonald's")
- Primera letra mayúscula

Reglas para el monto:
- Eliminá separadores de miles (ej: "27.540" → 27540)
- Si hay decimales, redondea al entero

Ejemplos:
"Pague en verdueria 5900" → {"concepto": "Verdulería", "monto": 5900, "pagador": "Luca"}
"mc 27.540" → {"concepto": "McDonald's", "monto": 27540, "pagador": "Luca"}
"disney+ 18399" → {"concepto": "Disney+", "monto": 18399, "pagador": "Luca"}
"""


def parse_expense(text: str, sender_name: str = "Luca") -> dict:
    system = _SYSTEM.replace('"pagador": el nombre que se pase como default',
                              f'"pagador": "{sender_name}"')
    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=system,
        messages=[{"role": "user", "content": text}],
    )
    raw = response.content[0].text.strip()
    return json.loads(raw)