from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from datetime import datetime
import threading
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import nest_asyncio
import sys
import traceback
import time

# Для работы asyncio в потоке
nest_asyncio.apply()

# Явно устанавливаем политику asyncio
import asyncio
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

# ========== ОТЛАДКА: сразу пишем в логи ==========
print("="*50)
print("🚀🚀🚀 ПРИЛОЖЕНИЕ ЗАПУСКАЕТСЯ 🚀🚀🚀")
print(f"Python версия: {sys.version}")
print("="*50)
sys.stdout.flush()
# =================================================

app = Flask(__name__)
CORS(app)

# ========== ФЛАГ ДЛЯ ЗАПУСКА БОТА ==========
bot_started = False
# ============================================

# ================== НАСТРОЙКИ ==================
SPREADSHEET_ID_MAIN = '1AyoHQmx4GCMYrOx3Px22b4VscLcw02iatWAiYosu8gY'
SPREADSHEET_ID_COMPANY = '1izesBGr1DEaNu-bMrnW9ZQP-2cOPm_LFBkfFzuP_ocA'
SHEET_REESTR_ZAYAVOK = 'Реестр заявок'
SHEET_PERECHEN_MATERIALOV = 'Перечень материалов'
SHEET_OBJECTS = 'Действующие объекты'
SHEET_EMPLOYEES = 'Сотрудники'
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
CHAT_ID_WORK = '-1003893391515'

print(f"📌 TELEGRAM_BOT_TOKEN {'ЗАДАН' if TELEGRAM_BOT_TOKEN else 'НЕ ЗАДАН!'}")
if TELEGRAM_BOT_TOKEN:
    print(f"   Токен (первые 10 символов): {TELEGRAM_BOT_TOKEN[:10]}...")
print(f"📌 CHAT_ID_WORK: {CHAT_ID_WORK}")
print("="*50)
sys.stdout.flush()
# ===============================================

def get_sheets_client():
    """Подключение к Google Sheets"""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    if 'GOOGLE_CREDENTIALS' in os.environ:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        print("✅ Google Sheets: авторизация через переменную окружения")
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        print("📌 Google Sheets: авторизация через локальный файл")
    
    client = gspread.authorize(creds)
    return client

# ================== КОМАНДЫ ДЛЯ TELEGRAM БОТА ==================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"📨 Команда /start от пользователя {user.id}")
    await update.message.reply_text(
        "👋 Привет! Я бот для приёмки материалов.\n\n"
        "Команды:\n"
        "/start - Приветствие\n"
        "/receiving - Открыть приёмку материалов\n"
        "/help - Справка"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"📨 Команда /help от пользователя {user.id}")
    await update.message.reply_text(
        "📋 **Справка по командам**\n\n"
        "/start - Начать работу с ботом\n"
        "/receiving - Открыть приложение для приёмки материалов\n"
        "/help - Показать эту справку"
    )

async def receiving_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"📨 Команда /receiving от пользователя {user.id}")
    await update.message.reply_text(
        "📱 Откройте приложение для приёмки материалов:",
        reply_markup={
            "inline_keyboard": [[{
                "text": "🚀 Открыть приёмку",
                "web_app": {"url": "https://melhipo.github.io/mini-app/"}
            }]]
        }
    )

async def run_bot_simple():
    """Упрощённый запуск бота"""
    print("🚀 Запускаем бота...")
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Токен не найден")
        return
    
    try:
        # Создаём приложение
        app_bot = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Добавляем обработчики
        app_bot.add_handler(CommandHandler("start", start_command))
        app_bot.add_handler(CommandHandler("help", help_command))
        app_bot.add_handler(CommandHandler("receiving", receiving_command))
        
        print("✅ Бот сконфигурирован, запускаем polling...")
        
        # Запускаем бота (это блокирующая операция)
        await app_bot.run_polling(allowed_updates=['message'])
        
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")

def start_bot_in_thread():
    """Запуск бота в отдельном потоке"""
    print("🔄 Запускаем бота в потоке...")
    
    # Создаём новый event loop для потока
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Запускаем бота
    loop.run_until_complete(run_bot_simple())

# ========== ЗАПУСКАЕМ БОТА ПРИ ПЕРВОМ ЗАПРОСЕ ==========
@app.before_request
def start_bot_once():
    global bot_started
    if not bot_started and TELEGRAM_BOT_TOKEN:
        print("🟢 Запускаем бота при первом запросе...")
        bot_thread = threading.Thread(target=start_bot_in_thread, daemon=True)
        bot_thread.start()
        bot_started = True
        time.sleep(2)  # Даём боту время на инициализацию
# =======================================================

# ================== API ЭНДПОИНТЫ ==================
# (все ваши существующие эндпоинты остаются без изменений)
# @app.route('/api/objects', ...)
# @app.route('/api/zayavki', ...)
# @app.route('/api/zayavka/<nomer>', ...)
# @app.route('/api/priemka', ...)
# @app.route('/api/health', ...)

# ================== ЗАПУСК ==================
if __name__ == '__main__':
    print("="*50)
    print("🟢 ЗАПУСК MAIN БЛОКА")
    print("="*50)
    sys.stdout.flush()
    
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Запуск Flask сервера на порту {port}...")
    sys.stdout.flush()
    app.run(host='0.0.0.0', port=port, debug=False)
