import logging
import os
import re
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ChatMemberHandler
)

TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

warns = {}
usernames = {}
firstnames = {}

BAD_WORDS = [
    "puta", "mierda", "cabron", "imbecil", "idiota", "perra", "pendejo", "culiao", "jetacas",
    "verga", "coño", "hdp", "joder", "malparido", "chingada", "gilipollas", "pelotudo", "culero",
    "estupido", "zorra", "bitch", "fuck", "shit", "asshole", "dick", "bastard", "motherfucker",
    "cunt", "mierd@", "pajero", "cojudo", "vergon", "vergonazo", "cojudazo", "ptm", "ptmr", "fuckyou",
    "mierdero", "marica", "maricon", "soplapollas", "anormal", "estúpido", "culiadaso", "gonorrea",
    "careverga", "careculo", "carechimba", "culito", "petardo", "inútil", "imbécil", "saco de mierda"
]

def contains_bad_word(text):
    return any(re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE) for word in BAD_WORDS)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎉 Bot activado. Usa /reglas para ver las normas del grupo.")

async def reglas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>Reglas del grupo:</b>\n"
        "1. Respeto mutuo entre todos los miembros.\n"
        "2. No se permite spam, contenido ofensivo o discriminatorio.\n"
        "3. Mantener el enfoque del grupo.\n"
        "4. No compartir información personal.\n"
        "5. Usa /ayuda si necesitas asistencia.",
        parse_mode="HTML"
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    admins = await context.bot.get_chat_administrators(chat.id)
    mensaje = f"🔔 El usuario @{update.effective_user.username or update.effective_user.first_name} ha solicitado ayuda en el grupo {chat.title}."
    for admin in admins:
        try:
            await context.bot.send_message(chat_id=admin.user.id, text=mensaje)
        except:
            pass
    await update.message.reply_text("✅ Hemos notificado a los administradores. Pronto te contactarán.")

async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    admins = await context.bot.get_chat_administrators(chat.id)
    admin_list = "\n".join([
        f"• {admin.user.first_name} (@{admin.user.username})"
        if admin.user.username else f"• {admin.user.first_name}"
        for admin in admins
    ])
    await update.message.reply_text(f"<b>Administradores del grupo:</b>\n{admin_list}", parse_mode="HTML")

async def bienvenida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for nuevo in update.message.new_chat_members:
        await update.message.reply_text(f"🎉 ¡Bienvenido/a {nuevo.mention_html()}!", parse_mode="HTML")

async def filtro_groserias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text and contains_bad_word(update.message.text):
        try:
            await update.message.delete()
        except:
            pass

async def advertencias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user = update.message.from_user
    chat_id = update.message.chat_id
    user_id = user.id
    username = user.username or user.first_name
    if contains_bad_word(update.message.text):
        warns.setdefault(chat_id, {}).setdefault(user_id, 0)
        warns[chat_id][user_id] += 1
        count = warns[chat_id][user_id]
        await update.message.reply_text(f"⚠️ El @{username} tiene {count} advertencia(s).")
        if count % 2 == 0:
            admins = await context.bot.get_chat_administrators(chat_id)
            for admin in admins:
                if not admin.user.is_bot:
                    try:
                        await context.bot.send_message(admin.user.id, f"⚠️ El usuario @{username} ha recibido {count} advertencias.")
                    except Exception as e:
                        logger.warning(str(e))
        if count % 5 == 0:
            until_date = datetime.utcnow() + timedelta(minutes=10)
            await context.bot.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False), until_date=until_date)
            await context.bot.send_message(chat_id, f"🔇 @{username} ha sido silenciado por 10 minutos.")

async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.chat_member.chat.id
    user = update.chat_member.from_user
    if update.chat_member.old_chat_member.status in ["left", "kicked"] and update.chat_member.new_chat_member.status == "member":
        admins = await context.bot.get_chat_administrators(chat_id)
        for admin in admins:
            if not admin.user.is_bot:
                try:
                    await context.bot.send_message(admin.user.id, f"🚪 El usuario @{user.username or user.first_name} ha vuelto al grupo.")
                except Exception as e:
                    logger.warning(str(e))

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reglas", reglas))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("staff", staff))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bienvenida))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filtro_groserias), 0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, advertencias), 1)
    app.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.CHAT_MEMBER))
    app.run_polling()

if __name__ == "__main__":
    main()