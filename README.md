# gasto-bot

Bot de Telegram que registra gastos en un Google Sheet compartido.

---

## Setup completo (~15 minutos)

### Paso 1 — Crear el bot de Telegram

1. Abrí Telegram y buscá `@BotFather`
2. Mandá `/newbot`
3. Elegí un nombre (ej: "Bot Gastos") y un username (ej: `mis_gastos_bot`)
4. Copiá el **token** que te devuelve (ej: `7123456789:AAFxxx...`) → `TELEGRAM_TOKEN`

5. Para obtener tu Telegram user ID:
   - Buscá `@userinfobot` en Telegram
   - Mandá cualquier mensaje
   - Copiá el número de "Id" → `ALLOWED_USER_ID`

---

### Paso 2 — Google Cloud (Service Account)

1. Entrá a https://console.cloud.google.com
2. Creá un proyecto nuevo (ej: "gasto-bot")
3. En el menú: **APIs & Services → Library** → buscá "Google Sheets API" → habilitala
4. En el menú: **IAM & Admin → Service Accounts** → **Create Service Account**
   - Nombre: `gasto-bot`
   - Rol: no hace falta asignar rol aquí → continuar
5. Hacé click en la service account recién creada → pestaña **Keys** → **Add Key → Create new key → JSON**
6. Se descarga un archivo JSON. Abrilo con un editor de texto y copiá todo el contenido → `GOOGLE_CREDENTIALS_JSON`
7. Guardá también el email de la service account (ej: `gasto-bot@gasto-bot-123.iam.gserviceaccount.com`) — lo vas a necesitar en el Paso 3

---

### Paso 3 — Compartir el Google Sheet

1. Abrí tu Google Sheet
2. Hacé click en **Compartir** (arriba a la derecha)
3. Pegá el email de la service account del Paso 2
4. Asignale rol **Editor** → Enviar
5. Copiá el ID del sheet desde la URL:
   `https://docs.google.com/spreadsheets/d/**[ESTE-ES-EL-ID]**/edit`
   → `GOOGLE_SHEET_ID`

> El tab del sheet tiene que llamarse exactamente **Gastos** (como aparece en la pestaña de abajo).

---

### Paso 4 — Anthropic API Key

1. Entrá a https://console.anthropic.com
2. **API Keys → Create Key**
3. Copiá la key → `ANTHROPIC_API_KEY`

---

### Paso 5 — Subir el código a GitHub

```bash
cd C:\Users\LZIEHER\gasto-bot
git init
git add .
git commit -m "init gasto-bot"
```

Creá un repo nuevo en https://github.com/new (puede ser privado) y seguí las instrucciones para hacer push.

---

### Paso 6 — Deploy en Railway

1. Entrá a https://railway.app → **New Project → Deploy from GitHub repo**
2. Seleccioná el repo `gasto-bot`
3. Railway va a detectar el `Procfile` automáticamente
4. Antes de que corra, configurá las variables de entorno:
   - **Settings → Variables** → agregá cada una:

| Variable | Valor |
|---|---|
| `TELEGRAM_TOKEN` | token del Paso 1 |
| `ANTHROPIC_API_KEY` | key del Paso 4 |
| `GOOGLE_SHEET_ID` | ID del Paso 3 |
| `GOOGLE_CREDENTIALS_JSON` | JSON completo del Paso 2 (en una sola línea) |
| `ALLOWED_USER_ID` | tu user ID del Paso 1 |
| `WEBHOOK_URL` | lo completás después de obtener la URL de Railway (ver abajo) |

5. Hacé deploy. Railway te asigna una URL pública tipo `https://gasto-bot-production.up.railway.app`
6. Copiá esa URL y agregala como `WEBHOOK_URL` en las variables
7. Redeploy (Railway lo detecta automáticamente al guardar la variable)

---

## Uso

| Mensaje / Comando | Resultado |
|---|---|
| `Verdulería 5900` | Agrega fila al Sheet |
| `Pague en McDonald's 27540` | Agrega fila al Sheet |
| `mc 27540` | Agrega fila con concepto "McDonald's" |
| `/undo` | Borra el último gasto cargado por Luca |
| `/saldo` | Muestra balance total y quién le debe a quién |
| `/resumen` | Totales del mes actual por persona |
| `/ayuda` | Muestra ejemplos |

---

## Desarrollo local (sin Railway)

Instalá dependencias:
```bash
pip install -r requirements.txt
```

Creá un archivo `.env` copiando `.env.example` y completando los valores reales.
Cargá las variables y corré en modo polling (sin webhook):

```bash
# Windows PowerShell
$env:TELEGRAM_TOKEN="tu_token"
$env:ANTHROPIC_API_KEY="tu_key"
$env:GOOGLE_SHEET_ID="tu_sheet_id"
$env:GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
$env:ALLOWED_USER_ID="tu_user_id"
python bot.py
```

Sin `WEBHOOK_URL` seteada, el bot arranca en modo polling automáticamente.
