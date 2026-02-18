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

# Для работы asyncio в потоке
nest_asyncio.apply()

app = Flask(__name__)
CORS(app)

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
# ===============================================

def get_sheets_client():
    """Подключение к Google Sheets"""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # На Render credentials будут в переменной окружения
    if 'GOOGLE_CREDENTIALS' in os.environ:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # Локально - из файла
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    
    client = gspread.authorize(creds)
    return client

# ================== КОМАНДЫ ДЛЯ TELEGRAM БОТА ==================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я бот для приёмки материалов.\n\n"
        "Команды:\n"
        "/start - Приветствие\n"
        "/receiving - Открыть приёмку материалов\n"
        "/help - Справка"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📋 **Справка по командам**\n\n"
        "/start - Начать работу с ботом\n"
        "/receiving - Открыть приложение для приёмки материалов\n"
        "/help - Показать эту справку\n\n"
        "Для приёмки материалов используйте кнопку меню или команду /receiving"
    )

async def receiving_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /receiving - открывает Mini App"""
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
    token = TELEGRAM_BOT_TOKEN
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return
    
    try:
        # Создаем приложение бота
        application = Application.builder().token(token).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("receiving", receiving_command))
        
        print("✅ Telegram бот запущен и слушает команды...")
        
        # Запускаем бота
        await application.initialize()
        await application.start()
        
        # Запускаем polling (это блокирующая операция)
        await application.updater.start_polling()
        
        # Держим бота запущенным
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

def start_bot_thread():
    """Запуск бота в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

# ================== API ЭНДПОИНТЫ ==================

@app.route('/api/objects', methods=['GET'])
def get_objects():
    """Получить список объектов"""
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
        
        return jsonify({'success': True, 'objects': objects})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/zayavki', methods=['GET'])
def get_zayavki():
    """Получить активные заявки для объекта"""
    object_code = request.args.get('object')
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
        
        return jsonify({'success': True, 'zayavki': zayavki})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/zayavka/<nomer>', methods=['GET'])
def get_zayavka_details(nomer):
    """Получить позиции заявки"""
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
        
        return jsonify({'success': True, 'pozicii': pozicii})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/priemka', methods=['POST'])
def priemka():
    """Принять материал"""
    data = request.json
    
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
                break
        
        if updated:
            # Если брак - уведомление
            if data['kachestvo'] == 'Брак':
                # Отправляем в Telegram
                message = f"""
⚠️ **БРАК НА ОБЪЕКТЕ**

📦 Заявка: {data['nomer_zayavki']}
🧱 Материал: {data['naim_materiala']}
📝 Комментарий: {data.get('kommentariy', '')}
👤 Принял: {data['fio']}
"""
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                try:
                    requests.post(url, json={
                        'chat_id': CHAT_ID_WORK,
                        'text': message,
                        'parse_mode': 'Markdown'
                    })
                except Exception as e:
                    print(f"Ошибка отправки уведомления: {e}")
            
            return jsonify({'success': True, 'message': 'Приемка сохранена'})
        else:
            return jsonify({'success': False, 'error': 'Позиция не найдена'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})

# ================== ЗАПУСК ==================

if __name__ == '__main__':
    # Запускаем Telegram бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
    bot_thread.start()
    print("🚀 Бот запущен в отдельном потоке")
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
