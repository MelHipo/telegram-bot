# bot.py
import os
import asyncio
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

print("🚀🚀🚀 TELEGRAM BOT STARTING (STANDALONE) 🚀🚀🚀")
sys.stdout.flush()

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print("❌ FATAL: TELEGRAM_BOT_TOKEN environment variable not set!")
    sys.exit(1)

print(f"✅ Bot token found (first 10 chars): {TOKEN[:10]}...")
sys.stdout.flush()

# --- Команды бота (скопируйте их из app.py) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"📨 /start from user {user.id}")
    await update.message.reply_text(
        "👋 Привет! Я бот для приёмки материалов.\n\n"
        "Команды:\n"
        "/start - Приветствие\n"
        "/receiving - Открыть приёмку материалов\n"
        "/help - Справка"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"📨 /help from user {user.id}")
    await update.message.reply_text(
        "📋 **Справка по командам**\n\n"
        "/start - Начать работу\n"
        "/receiving - Открыть приёмку\n"
        "/help - Справка"
    )

async def receiving_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"📨 /receiving from user {user.id}")
    await update.message.reply_text(
        "📱 Откройте приложение для приёмки материалов:",
        reply_markup={
            "inline_keyboard": [[{
                "text": "🚀 Открыть приёмку",
                "web_app": {"url": "https://melhipo.github.io/mini-app/"}
            }]]
        }
    )
# --- Конец команд ---

async def main():
    """Главная функция для запуска бота."""
    print("🔄 Building application...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("receiving", receiving_command))

    print("✅ Handlers added. Starting polling...")
    sys.stdout.flush()

    # Используем run_polling, который сам управляет циклом событий
    await application.run_polling(allowed_updates=['message'])

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
        sys.exit(1)
