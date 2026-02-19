#!/usr/bin/env python3
"""Telegram Bot for Material Receiving - Standalone Version"""

import os
import asyncio
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

print("🚀🚀🚀 TELEGRAM BOT STARTING (STANDALONE) 🚀🚀🚀")
sys.stdout.flush()

# Получаем токен
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print("❌ FATAL: TELEGRAM_BOT_TOKEN environment variable not set!")
    sys.exit(1)

print(f"✅ Bot token found (first 10 chars): {TOKEN[:10]}...")
sys.stdout.flush()

# --- Команды бота ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    print(f"📨 /start from user {user.id} ({user.first_name})")
    await update.message.reply_text(
        "👋 Привет! Я бот для приёмки материалов.\n\n"
        "Команды:\n"
        "/start - Приветствие\n"
        "/receiving - Открыть приёмку материалов\n"
        "/help - Справка"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user = update.effective_user
    print(f"📨 /help from user {user.id}")
    await update.message.reply_text(
        "📋 **Справка по командам**\n\n"
        "/start - Начать работу\n"
        "/receiving - Открыть приёмку\n"
        "/help - Справка\n\n"
        "Для приёмки материалов используйте кнопку меню или команду /receiving"
    )

async def receiving_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /receiving - открывает Mini App"""
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
    """Асинхронная главная функция"""
    print("🔄 Building application...")
    sys.stdout.flush()
    
    # Создаём приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("receiving", receiving_command))
    
    print("✅ Handlers added. Initializing...")
    sys.stdout.flush()
    
    # Инициализируем
    await application.initialize()
    
    print("✅ Bot initialized. Starting...")
    sys.stdout.flush()
    
    # Запускаем
    await application.start()
    
    print("✅ Bot started. Starting polling...")
    sys.stdout.flush()
    
    # Запускаем polling
    await application.updater.start_polling()
    
    print("✅✅✅ BOT IS RUNNING! ✅✅✅")
    print("🤖 Bot is ready! Send /start in Telegram")
    sys.stdout.flush()
    
    # Держим бота запущенным
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping bot...")
    finally:
        # Останавливаем
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        print("👋 Bot shutdown complete")

if __name__ == '__main__':
    # Создаём и устанавливаем цикл событий
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Запускаем асинхронную функцию
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
    finally:
        # Закрываем цикл
        loop.close()
