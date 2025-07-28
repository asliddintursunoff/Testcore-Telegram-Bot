

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests, random
import datetime
from telegram import BotCommand, BotCommandScopeChat
import os

otp_store = {}  
OTP_VALIDITY_SECONDS = 120

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = 'https://apiv1.testcore.uz/api/telegram-login/'


async def set_commands(chat_id: int, stage: str, context: ContextTypes.DEFAULT_TYPE):
    if stage == "initial":
        commands = [BotCommand("start", "Botni ishga tushurish")]
    elif stage == "after_start":
        commands = [BotCommand("login", "Kirish uchun kod olish")]

    await context.bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id))




user_map = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = KeyboardButton("Telefon raqamingizni ulashish☎️", request_contact=True)
    markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    user = update.effective_user
    username = user.username or f"{user.first_name} {user.last_name or ''}".strip()
    await update.message.reply_text(f"""
        🇺🇿Salom {username}👋
TestCore.uz'ning rasmiy botiga xush kelibsiz

⬇ Kontaktingizni tugmani bosib yuboring 

🇺🇸
Hi {username} 👋
Welcome to TestCore.uz's official bot

⬇ Send your contact by clicking button""", reply_markup=markup)

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number
    telegram_id = update.message.from_user.id
    user_map[telegram_id] = phone
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name or ""


    # Generate OTP
    code = str(random.randint(10000, 99999))
    otp_store[telegram_id] = (code, datetime.datetime.now())

    # Send OTP to your backend
    try:
        requests.post(BACKEND_URL, json={
            "telegram_id": telegram_id,
            "phone_number": phone,
            "telegram_name":f"{first_name} {last_name}",
            "code": code
        })
        await update.message.reply_text(f"🔑 Sizning kirish kodingiz: \n```{code}```" ,parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Kod serverga yuborilmadi.")

    # Send /login instruction
    await update.message.reply_text(
        "🇺🇿\n🔑 Yangi kod olish uchun /login ni bosing\n\n🇺🇸🔑\nTo get a new code click /login"
    )
    await set_commands(update.effective_chat.id, "after_start", context)


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name or ""

    phone = user_map.get(telegram_id)

    if not phone:
        await update.message.reply_text("⚠️ Avval /start orqali raqamingizni yuboring.")
        return

    # Check existing OTP
    existing = otp_store.get(telegram_id)
    now = datetime.datetime.now()

    if existing:
        code, created_at = existing
        age = (now - created_at).total_seconds()
        if age <= OTP_VALIDITY_SECONDS:
            await update.message.reply_text(f"👆🏻Eski kodingiz hali ham yaroqli: `\n``{code}```",parse_mode="Markdown")
            return

    # Otherwise, generate a new OTP
    new_code = str(random.randint(10000, 99999))
    otp_store[telegram_id] = (new_code, now)

    try:
        requests.post(BACKEND_URL, json={
            "telegram_id": telegram_id,
            "phone_number": phone,
            "telegram_name":f"{first_name} {last_name}",
            "code": new_code
        })
        await update.message.reply_text(f"🔁 Yangi kod: \n```{new_code}```",parse_mode="Markdown")
        await update.message.reply_text(
        "🇺🇿\n🔑 Yana yangi kod olish uchun /login ni bosing\n\n🇺🇸🔑\nTo get a new code click /login"
    )
    except:
        await update.message.reply_text("❌ Kod serverga yuborilmadi.")


app = ApplicationBuilder().token(TOKEN).build()

async def setup_global_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Botni ishga tushurish")
    ])
app.post_init = setup_global_commands


app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.CONTACT, contact))
app.add_handler(CommandHandler("login", login))
app.run_polling()