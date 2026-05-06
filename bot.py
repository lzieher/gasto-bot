import logging
import os
import threading

from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    ContextTypes, MessageHandler, filters,
)

import config
from parser import parse_expense
from sheets import append_expense, delete_last_expense, get_balance, get_monthly_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bot")


def _fmt(amount: float) -> str:
    return f"{int(amount):,}".replace(",", ".")


def _get_payer(update: Update):
    return config.ALLOWED_USER_IDS.get(update.effective_user.id)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payer = _get_payer(update)
    if not payer:
        return
    text = update.message.text.strip()
    status_msg = await update.message.reply_text("Procesando...")
    try:
        parsed = parse_expense(text, sender_name=payer)
    except Exception as e:
        logger.error("Parse error: %s", e)
        await status_msg.edit_text("No pude entender el mensaje.\nProba: Verduleria 5900")
        return
    concepto = parsed.get("concepto", "").strip()
    monto = parsed.get("monto")
    pagador = parsed.get("pagador", payer).strip() or payer
    if not monto:
        keyboard = [[InlineKeyboardButton("Escribir de nuevo", callback_data="redo")]]
        await status_msg.edit_text(
            f"No detecte el monto en: {text}\n\nProba: {concepto} [monto]",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
    try:
        append_expense(concepto, int(monto), pagador, update.message.date)
        await status_msg.edit_text(f"OK: {concepto} -- ${_fmt(monto)} ({pagador}) guardado.")
    except Exception as e:
        logger.error("Sheets error: %s", e)
        await status_msg.edit_text("Error al guardar en el Sheet.")


async def cmd_undo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payer = _get_payer(update)
    if not payer:
        return
    success, description = delete_last_expense(payer)
    if success:
        await update.message.reply_text(f"Borrado: {description}")
    else:
        await update.message.reply_text(f"No encontre ningun gasto de {payer} para borrar.")


async def cmd_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _get_payer(update):
        return
    totals = get_balance()
    if not totals:
        await update.message.reply_text("No hay gastos cargados aun.")
        return
    lines = ["Balance total\n"]
    for p, t in sorted(totals.items()):
        lines.append(f"  {p}: ${_fmt(t)}")
    luca = totals.get("Luca", 0.0)
    morita = totals.get("Morita", 0.0)
    diff = luca - morita
    if diff > 0:
        lines.append(f"\nMorita le debe a Luca ${_fmt(diff)}")
    elif diff < 0:
        lines.append(f"\nLuca le debe a Morita ${_fmt(abs(diff))}")
    else:
        lines.append("\nEstan al dia")
    await update.message.reply_text("\n".join(lines))


async def cmd_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _get_payer(update):
        return
    from datetime import datetime
    mes = datetime.now().strftime("%B %Y").capitalize()
    totals = get_monthly_summary()
    if not totals:
        await update.message.reply_text(f"No hay gastos este mes ({mes}).")
        return
    lines = [f"Resumen {mes}\n"]
    total_general = 0.0
    for p, t in sorted(totals.items()):
        lines.append(f"  {p}: ${_fmt(t)}")
        total_general += t
    lines.append(f"\n  Total: ${_fmt(total_general)}")
    await update.message.reply_text("\n".join(lines))


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _get_payer(update):
        return
    await update.message.reply_text(
        "Como cargar gastos:\n\n"
        "- Verduleria 5900\n- McDonalds 27540\n- Carrefour 20189\n\n"
        "Comandos:\n/undo /saldo /resumen /ayuda"
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "redo":
        await query.edit_message_text("Escribi de nuevo el gasto con el monto incluido.")


def main() -> None:
    flask_app = Flask("health")

    @flask_app.route("/health")
    def health():
        return "ok"

    threading.Thread(
        target=lambda: flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000))),
        daemon=True
    ).start()

    app = Application.builder().token(config.TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_ayuda))
    app.add_handler(CommandHandler("ayuda", cmd_ayuda))
    app.add_handler(CommandHandler("undo", cmd_undo))
    app.add_handler(CommandHandler("saldo", cmd_saldo))
    app.add_handler(CommandHandler("resumen", cmd_resumen))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()


main()