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
sys.stdout.flush()  # Принудительно отправляем в логи
# =================================================

app = Flask(__name__)
CORS(app)

# ========== ФЛАГ ДЛЯ ЗАПУСКА БОТА ==========
bot_started = False
# ============================================

# ================== НАСТРОЙКИ ==================
# ID вашей общей таблицы (из ссылки)
SPREADSHEET_ID_MAIN = '1AyoHQmx4GCMYrOx3Px22b4VscLcw02iatWAiYosu8gY'

# ID таблицы с объектами и сотрудниками
SPREADSHEET_ID_COMPANY = '1izesBGr1DEaNu-bMrnW9ZQP-2cOPm_LFBkfFzuP_ocA'

# Названия листов
SHEET_REESTR_ZAYAVOK = 'Реестр заявок'
SHEET_PERECHEN_MATERIALOV = 'Перечень материалов'
SHEET_OBJECTS = 'Действующие объекты'
SHEET_EMPLOYEES = 'Сотрудники'

# Telegram
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
    
    # На Render credentials будут в переменной окружения
    if 'GOOGLE_CREDENTIALS' in os.environ:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        print("✅ Google Sheets: авторизация через переменную окружения")
    else:
        # Локально - из файла
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        print("📌 Google Sheets: авторизация через локальный файл")
    
    client = gspread.authorize(creds)
    return client

# ================== КОМАНДЫ ДЛЯ TELEGRAM БОТА ==================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    print(f"📨 Команда /start от пользователя {user.id} ({user.first_name})")
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
    print(f"📨 Команда /help от пользователя {user.id}")
    await update.message.reply_text(
        "📋 **Справка по командам**\n\n"
        "/start - Начать работу с ботом\n"
        "/receiving - Открыть приложение для приёмки материалов\n"
        "/help - Показать эту справку\n\n"
        "Для приёмки материалов используйте кнопку меню или команду /receiving"
    )

async def receiving_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /receiving - открывает Mini App"""
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

async def run_bot():
    """Запуск Telegram бота"""
    print("🔥 run_bot() вызвана!")
    sys.stdout.flush()
    
    token = TELEGRAM_BOT_TOKEN
    print(f"🔑 Токен: {'НАЙДЕН' if token else 'НЕ НАЙДЕН!'}")
    if token:
        print(f"   Длина токена: {len(token)} символов")
        print(f"   Первые 10 символов: {token[:10]}...")
    sys.stdout.flush()
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        sys.stdout.flush()
        return
    
    try:
        print("🔄 Создаем приложение бота...")
        sys.stdout.flush()
        application = Application.builder().token(token).build()
        
        print("➕ Добавляем обработчики команд...")
        sys.stdout.flush()
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("receiving", receiving_command))
        
        print("✅ Обработчики добавлены")
        sys.stdout.flush()
        
        print("🔄 Инициализация бота...")
        sys.stdout.flush()
        await application.initialize()
        
        print("▶️ Запуск бота...")
        sys.stdout.flush()
        await application.start()
        
        print("📡 Запуск polling (прослушивание команд)...")
        sys.stdout.flush()
        await application.updater.start_polling()
        print("✅ Polling запущен")
        sys.stdout.flush()
        
        print("✅✅✅ Telegram бот УСПЕШНО запущен и слушает команды! ✅✅✅")
        print("🤖 Бот готов к работе! Отправьте /start в Telegram")
        sys.stdout.flush()
        
        # Держим бота запущенным
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌❌❌ ОШИБКА запуска бота: {e}")
        print("📋 Детали ошибки:")
        traceback.print_exc()
        sys.stdout.flush()

def start_bot_thread():
    """Запуск бота в отдельном потоке"""
    print("🔄 Создаем новый event loop для бота...")
    sys.stdout.flush()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("✅ Event loop создан, запускаем run_bot()")
    sys.stdout.flush()
    loop.run_until_complete(run_bot())

# ========== ЗАПУСКАЕМ БОТА ПРИ ПЕРВОМ ЗАПРОСЕ ==========
@app.before_request
def start_bot_once():
    global bot_started
    if not bot_started and TELEGRAM_BOT_TOKEN:
        print("🟢 Запускаем бота при первом запросе...")
        bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
        bot_thread.start()
        bot_started = True
        # Даем боту секунду на инициализацию
        time.sleep(1)
# =======================================================

# ================== API ЭНДПОИНТЫ ==================

@app.route('/api/objects', methods=['GET'])
def get_objects():
    """Получить список объектов"""
    print("📡 GET /api/objects")
    try:
        client = get_sheets_client()
        sheet = client.open_by_key(SPREADSHEET_ID_COMPANY).worksheet(SHEET_OBJECTS)
        data = sheet.get_all_values()[1:]  # пропускаем заголовки
        
        objects = []
        for row in data:
            if row and row[0].strip():
                objects.append({
                    'code': row[0].strip(),
                    'name': row[1].strip() if len(row) > 1 else ''
                })
        
        print(f"✅ Найдено объектов: {len(objects)}")
        return jsonify({'success': True, 'objects': objects})
    except Exception as e:
        print(f"❌ Ошибка в /api/objects: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/zayavki', methods=['GET'])
def get_zayavki():
    """Получить активные заявки для объекта"""
    object_code = request.args.get('object')
    print(f"📡 GET /api/zayavki?object={object_code}")
    
    if not object_code:
        return jsonify({'success': False, 'error': 'Не указан объект'}), 400
    
    try:
        client = get_sheets_client()
        sheet = client.open_by_key(SPREADSHEET_ID_MAIN).worksheet(SHEET_REESTR_ZAYAVOK)
        data = sheet.get_all_values()[1:]
        
        zayavki = []
        for row in data:
            if len(row) >= 4:
                nomer = row[1] if len(row) > 1 else ''
                status = row[3] if len(row) > 3 else ''
                
                if object_code in nomer and status in ['В обработке', 'Частичная доставка', 'Полная доставка']:
                    zayavki.append({
                        'date': row[0] if len(row) > 0 else '',
                        'nomer': nomer,
                        'responsible': row[2] if len(row) > 2 else '',
                        'status': status
                    })
        
        print(f"✅ Найдено заявок: {len(zayavki)}")
        return jsonify({'success': True, 'zayavki': zayavki})
    except Exception as e:
        print(f"❌ Ошибка в /api/zayavki: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/zayavka/<nomer>', methods=['GET'])
def get_zayavka_details(nomer):
    """Получить позиции заявки"""
    print(f"📡 GET /api/zayavka/{nomer}")
    try:
        client = get_sheets_client()
        sheet = client.open_by_key(SPREADSHEET_ID_MAIN).worksheet(SHEET_PERECHEN_MATERIALOV)
        data = sheet.get_all_values()[1:]
        
        pozicii = []
        for row in data:
            if len(row) >= 11 and row[0] == nomer:
                pozicii.append({
                    'nomer_zayavki': row[0],
                    'naim': row[1] if len(row) > 1 else '',
                    'ed_izm': row[2] if len(row) > 2 else '',
                    'kolvo_zakaz': row[3] if len(row) > 3 else '',
                    'postavshchik': row[4] if len(row) > 4 else '',
                    'data_postavki_plan': row[5] if len(row) > 5 else '',
                    'kolvo_fakt': row[6] if len(row) > 6 else '',
                    'data_postavki_fakt': row[7] if len(row) > 7 else '',
                    'status': row[8] if len(row) > 8 else '',
                    'kachestvo': row[9] if len(row) > 9 else '',
                    'kommentariy': row[10] if len(row) > 10 else ''
                })
        
        print(f"✅ Найдено позиций: {len(pozicii)}")
        return jsonify({'success': True, 'pozicii': pozicii})
    except Exception as e:
        print(f"❌ Ошибка в /api/zayavka/{nomer}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/priemka', methods=['POST'])
def priemka():
    """Принять материал"""
    data = request.json
    print(f"📡 POST /api/priemka: {data.get('nomer_zayavki')} - {data.get('naim_materiala')}")
    
    required = ['nomer_zayavki', 'naim_materiala', 'kolvo_fakt', 'kachestvo', 'fio']
    for field in required:
        if field not in data:
            return jsonify({'success': False, 'error': f'Нет поля {field}'}), 400
    
    try:
        client = get_sheets_client()
        sheet = client.open_by_key(SPREADSHEET_ID_MAIN).worksheet(SHEET_PERECHEN_MATERIALOV)
        
        all_data = sheet.get_all_values()
        today = datetime.now().strftime('%d.%m.%Y')
        
        updated = False
        for i, row in enumerate(all_data):
            if i == 0:
                continue
            if len(row) >= 2 and row[0] == data['nomer_zayavki'] and row[1] == data['naim_materiala']:
                row_num = i + 1
                sheet.update(f'G{row_num}', data['kolvo_fakt'])
                sheet.update(f'H{row_num}', today)
                sheet.update(f'I{row_num}', 'Принят' if data['kachestvo'] == 'OK' else 'Брак')
                sheet.update(f'J{row_num}', data['kachestvo'])
                
                komment = f"Принял: {data['fio']}. {data.get('kommentariy', '')}"
                sheet.update(f'K{row_num}', komment)
                updated = True
                print(f"✅ Позиция обновлена (строка {row_num})")
                break
        
        if updated:
            # Если брак - уведомление
            if data['kachestvo'] == 'Брак':
                print("⚠️ Обнаружен брак, отправляем уведомление")
                message = f"""
⚠️ **БРАК НА ОБЪЕКТЕ**

📦 Заявка: {data['nomer_zayavki']}
🧱 Материал: {data['naim_materiala']}
📝 Комментарий: {data.get('kommentariy', '')}
👤 Принял: {data['fio']}
"""
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                try:
                    response = requests.post(url, json={
                        'chat_id': CHAT_ID_WORK,
                        'text': message,
                        'parse_mode': 'Markdown'
                    })
                    if response.status_code == 200:
                        print("✅ Уведомление о браке отправлено")
                    else:
                        print(f"❌ Ошибка отправки уведомления: {response.status_code}")
                except Exception as e:
                    print(f"❌ Ошибка отправки уведомления: {e}")
            
            return jsonify({'success': True, 'message': 'Приемка сохранена'})
        else:
            print(f"❌ Позиция не найдена: {data['nomer_zayavki']} - {data['naim_materiala']}")
            return jsonify({'success': False, 'error': 'Позиция не найдена'}), 404
            
    except Exception as e:
        print(f"❌ Ошибка в /api/priemka: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    print("📡 GET /api/health")
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})

# ================== ЗАПУСК ==================

if __name__ == '__main__':
    print("="*50)
    print("🟢 ЗАПУСК MAIN БЛОКА")
    print("="*50)
    sys.stdout.flush()
    
    # Бот запустится при первом запросе через @app.before_request
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Запуск Flask сервера на порту {port}...")
    sys.stdout.flush()
    app.run(host='0.0.0.0', port=port, debug=False)
