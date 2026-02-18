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

# ========== ОТЛАДКА: сразу пишем в логи ==========
print("="*50)
print("🚀🚀🚀 ПРИЛОЖЕНИЕ ЗАПУСКАЕТСЯ 🚀🚀🚀")
print(f"Python версия: {sys.version}")
print("="*50)
sys.stdout.flush()
# =================================================

app = Flask(__name__)
CORS(app)

# ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
bot_started = False
bot_application = None
bot_loop = None
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

async def init_bot():
    """Инициализация бота в главном цикле событий"""
    global bot_application
    
    print("🚀 Инициализация бота в главном цикле...")
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Токен не найден")
        return None
    
    try:
        # Создаём приложение
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("receiving", receiving_command))
        
        print("✅ Бот сконфигурирован")
        
        # Инициализируем
        await application.initialize()
        await application.start()
        
        # Запускаем polling
        await application.updater.start_polling()
        
        print("✅✅✅ Бот успешно запущен и слушает команды!")
        return application
        
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        traceback.print_exc()
        return None

def run_bot_in_thread(loop):
    """Запуск бота в указанном цикле событий"""
    asyncio.set_event_loop(loop)
    loop.run_forever()

# ========== ЗАПУСКАЕМ БОТА В ОТДЕЛЬНОМ ПОТОКЕ ==========
def start_bot():
    global bot_application, bot_loop
    
    # Создаём новый цикл событий для потока
    bot_loop = asyncio.new_event_loop()
    
    # Запускаем бота в этом цикле
    async def _start():
        nonlocal bot_application
        bot_application = await init_bot()
    
    # Выполняем инициализацию в цикле
    bot_loop.run_until_complete(_start())
    
    # Запускаем цикл событий
    bot_loop.run_forever()

@app.before_request
def start_bot_once():
    global bot_started
    if not bot_started and TELEGRAM_BOT_TOKEN:
        print("🟢 Запускаем бота в отдельном потоке...")
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        bot_started = True
        time.sleep(3)  # Даём боту время на инициализацию
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
