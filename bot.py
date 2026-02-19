#!/usr/bin/env python3
"""Telegram Bot for Material Receiving - Standalone Version"""

import os
import asyncio
import sys
import signal
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

async def post_init(application: Application):
    """Действия после инициализации бота"""
    print("✅ Bot initialized and ready to work!")
    sys.stdout.flush()

async def shutdown(application: Application):
    """Действия при остановке бота"""
    print("🛑 Bot shutting down...")
    sys.stdout.flush()

def main():
    """Главная функция запуска бота"""
    print("🔄 Building application...")
    
    # Создаём приложение
    application = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("receiving", receiving_command))
    
    print("✅ Handlers added. Starting polling...")
    sys.stdout.flush()
    
    # Запускаем бота (это блокирующий вызов)
    try:
        # Используем run_polling, который сам управляет циклом
        application.run_polling(allowed_updates=['message'])
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot crashed with error: {e}")
        raise
    finally:
        print("👋 Bot shutdown complete")

if __name__ == '__main__':
    main()
