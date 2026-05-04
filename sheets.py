import json
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_CREDENTIALS_JSON, GOOGLE_SHEET_ID

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
_TAB_NAME = "Gastos"


def _get_worksheet():
    creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=_SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_ID).worksheet(_TAB_NAME)


def _parse_amount(value: str) -> float:
    s = str(value).strip().replace("$", "").replace(" ", "")
    # Argentine format: dots = thousands separator, comma = decimal
    # Remove thousands separators and normalize
    s = s.replace(".", "").replace(",", "")
    return float(s) if s else 0.0


def append_expense(concepto: str, monto: int, pagador: str, fecha) -> None:
    ws = _get_worksheet()
    fecha_str = fecha.strftime("%d/%m/%Y")
    col_a = ws.col_values(1)
    next_row = len(col_a) + 1
    ws.update(f"A{next_row}:D{next_row}", [[fecha_str, concepto, monto, pagador]])


def delete_last_expense(pagador: str) -> tuple[bool, str]:
    ws = _get_worksheet()
    rows = ws.get_all_values()
    # Iterate backward, skip header at index 0
    for i in range(len(rows) - 1, 0, -1):
        row = rows[i]
        if len(row) >= 4 and row[3].strip().lower() == pagador.lower():
            description = f"{row[1]} — ${row[2]} ({row[3]})"
            ws.delete_rows(i + 1)  # gspread rows are 1-indexed
            return True, description
    return False, ""


def get_balance() -> dict[str, float]:
    ws = _get_worksheet()
    rows = ws.get_all_values()[1:]  # skip header
    totals: dict[str, float] = {}
    for row in rows:
        if len(row) < 4 or not row[2].strip():
            continue
        try:
            amount = _parse_amount(row[2])
            payer = row[3].strip()
            if payer:
                totals[payer] = totals.get(payer, 0.0) + amount
        except (ValueError, IndexError):
            continue
    return totals


def get_monthly_summary() -> dict[str, float]:
    ws = _get_worksheet()
    rows = ws.get_all_values()[1:]  # skip header
    current_month = datetime.now().strftime("%m/%Y")
    totals: dict[str, float] = {}
    for row in rows:
        if len(row) < 4 or not row[0].strip() or not row[2].strip():
            continue
        try:
            parts = row[0].strip().split("/")
            if len(parts) != 3:
                continue
            row_month = f"{parts[1]}/{parts[2]}"
            if row_month != current_month:
                continue
            amount = _parse_amount(row[2])
            payer = row[3].strip()
            if payer:
                totals[payer] = totals.get(payer, 0.0) + amount
        except (ValueError, IndexError):
            continue
    return totals
