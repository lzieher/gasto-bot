import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDENTIALS_JSON = os.environ["GOOGLE_CREDENTIALS_JSON"]
ALLOWED_USER_ID = int(os.environ["ALLOWED_USER_ID"])
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 8443))
