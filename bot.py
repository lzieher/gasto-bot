import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
from parser import parse_expense
from sheets import append_expense, delete_last_expense, get_balance, get_monthly_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _fmt(amount: float) -> str:
    return f"{int(amount):,}".replace(",", ".")


def _is_authorized(update: Update) -> bool:
    return update.effective_user.id == config.ALLOWED_USER_ID


# ── handlers ──────────────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return

    text = update.message.text.strip()
    status_msg = await update.message.reply_text("⏳ Procesando...")

    try:
        parsed = parse_expense(text)
    except Exception as e:
        logger.error("Parse error: %s", e)
        await status_msg.edit_text(
            "❌ No pude entender el mensaje.\nProbá: `Verdulería 5900`",
            parse_mode="Markdown",
        )
        return

    concepto = parsed.get("concepto", "").strip()
    monto = parsed.get("monto")
    pagador = parsed.get("pagador", "Luca").strip() or "Luca"

    if not monto:
        keyboard = [[InlineKeyboardButton("✏️ Escribir de nuevo", callback_data="redo")]]
        await status_msg.edit_text(
            f"No detecté el monto en: _{text}_\n\nProbá: `{concepto} [monto]`",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    try:
        fecha = update.message.date
        append_expense(concepto, int(monto), pagador, fecha)
        await status_msg.edit_text(
            f"✅ *{concepto}* — ${_fmt(monto)} ({pagador}) guardado.",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error("Sheets error: %s", e)
        await status_msg.edit_text("❌ Error al guardar en el Sheet. Revisá los logs.")


async def cmd_undo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    success, description = delete_last_expense("Luca")
    if success:
        await update.message.reply_text(f"↩️ Borrado: {description}")
    else:
        await update.message.reply_text("No encontré ningún gasto de Luca para borrar.")


async def cmd_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return

    totals = get_balance()
    if not totals:
        await update.message.reply_text("No hay gastos cargados aún.")
        return

    lines = ["📊 *Balance total*\n"]
    for payer, total in sorted(totals.items()):
        lines.append(f"  {payer}: ${_fmt(total)}")

    luca = totals.get("Luca", 0.0)
    morita = totals.get("Morita", 0.0)
    diff = luca - morita
    if diff > 0:
        lines.append(f"\n→ Morita le debe a Luca *${_fmt(diff)}*")
    elif diff < 0:
        lines.append(f"\n→ Luca le debe a Morita *${_fmt(abs(diff))}*")
    else:
        lines.append("\n→ Están al día ✅")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return

    from datetime import datetime
    mes = datetime.now().strftime("%B %Y").capitalize()
    totals = get_monthly_summary()

    if not totals:
        await update.message.reply_text(f"No hay gastos este mes ({mes}).")
        return

    lines = [f"📅 *Resumen {mes}*\n"]
    total_general = 0.0
    for payer, total in sorted(totals.items()):
        lines.append(f"  {payer}: ${_fmt(total)}")
        total_general += total
    lines.append(f"\n  *Total: ${_fmt(total_general)}*")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    await update.message.reply_text(
        "📝 *Cómo cargar gastos:*\n\n"
        "Mandá el concepto y el monto:\n"
        "• `Verdulería 5900`\n"
        "• `Pague en McDonald's 27540`\n"
        "• `Carrefour 20189`\n"
        "• `Disney+ 18399`\n\n"
        "*Comandos:*\n"
        "/undo — borra el último gasto tuyo\n"
        "/saldo — balance total entre Luca y Morita\n"
        "/resumen — totales del mes\n"
        "/ayuda — este mensaje",
        parse_mode="Markdown",
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "redo":
        await query.edit_message_text("Escribí de nuevo el gasto con el monto incluido.")


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_ayuda))
    app.add_handler(CommandHandler("ayuda", cmd_ayuda))
    app.add_handler(CommandHandler("undo", cmd_undo))
    app.add_handler(CommandHandler("saldo", cmd_saldo))
    app.add_handler(CommandHandler("resumen", cmd_resumen))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))

    if config.WEBHOOK_URL:
        logger.info("Starting webhook on port %d", config.PORT)
        app.run_webhook(
            listen="0.0.0.0",
            port=config.PORT,
            url_path=config.TELEGRAM_TOKEN,
            webhook_url=f"{config.WEBHOOK_URL}/{config.TELEGRAM_TOKEN}",
        )
    else:
        logger.info("Starting polling (dev mode)")
        app.run_polling()


if __name__ == "__main__":
    main()
