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
import aiohttp
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Словарь для хранения последних данных заявок (чтобы не запрашивать каждый раз)
act_data_cache = {}

def generate_act_pdf(zayavka_data, materials_data, fio):
    """Генерирует PDF акта приёма-передачи"""
    buffer = io.BytesIO()
    
    # Создаем документ
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Заголовок
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        spaceAfter=20
    )
    elements.append(Paragraph("АКТ ПРИЁМА-ПЕРЕДАЧИ МАТЕРИАЛОВ", title_style))
    
    # Информация о заявке
    info_style = styles['Normal']
    elements.append(Paragraph(f"Номер заявки: {zayavka_data['nomer']}", info_style))
    elements.append(Paragraph(f"Дата приёмки: {datetime.now().strftime('%d.%m.%Y')}", info_style))
    elements.append(Paragraph(f"Принял: {fio}", info_style))
    elements.append(Spacer(1, 20))
    
    # Таблица с материалами
    table_data = [['№', 'Наименование', 'Ед. изм.', 'Заказано', 'Принято', 'Качество']]
    
    for i, item in enumerate(materials_data, 1):
        table_data.append([
            str(i),
            item['naim'],
            item['ed_izm'],
            str(item['kolvo_zakaz']),
            str(item['kolvo_fakt']),
            '✓' if item['kachestvo'] == 'OK' else '✗ Брак'
        ])
    
    table = Table(table_data, colWidths=[40, 180, 50, 60, 60, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 30))
    
    # Подписи
    elements.append(Paragraph("Сдал: ___________________ (поставщик)", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Принял: ___________________", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"({fio})", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Обработчик для генерации акта (будет вызываться API)
async def generate_act(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует акт по переданным данным"""
    # Эта функция будет вызываться не из Telegram, а из API
    # Поэтому здесь другой подход
    pass

# Функция для вызова из API (добавим позже)
async def generate_act_from_api(nomer_zayavki, fio):
    """Вызывается API для генерации акта"""
    try:
        # Получаем данные о заявке и материалах через API Render
        async with aiohttp.ClientSession() as session:
            # Получаем информацию о заявке
            url_zayavka = f"https://telegram-bot-pjn4.onrender.com/api/zayavka/{nomer_zayavki}"
            async with session.get(url_zayavka) as resp:
                if resp.status != 200:
                    return None, "Не удалось получить данные заявки"
                data = await resp.json()
                
            if not data.get('success'):
                return None, "Ошибка получения данных"
            
            materials = data.get('pozicii', [])
            # Фильтруем только принятые материалы
            accepted_materials = [m for m in materials if m['status'] in ['Принят', 'Брак']]
            
            if not accepted_materials:
                return None, "Нет принятых материалов"
            
            # Генерируем PDF
            pdf_buffer = generate_act_pdf(
                {'nomer': nomer_zayavki},
                accepted_materials,
                fio
            )
            
            # Отправляем в Telegram
            url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
            
            # В главный чат
            form_data = aiohttp.FormData()
            form_data.add_field('chat_id', CHAT_ID_WORK)
            form_data.add_field('caption', f"📄 Акт приёма-передачи по заявке {nomer_zayavki}")
            form_data.add_field('document', pdf_buffer.getvalue(), 
                              filename=f"act_{nomer_zayavki.replace(' ', '_')}.pdf",
                              content_type='application/pdf')
            
            async with session.post(url, data=form_data) as resp:
                if resp.status == 200:
                    return pdf_buffer, "Акт отправлен"
                else:
                    return None, "Ошибка отправки в Telegram"
                    
    except Exception as e:
        print(f"Ошибка генерации акта: {e}")
        return None, str(e)

# Добавим команду для тестирования (потом удалим)
async def test_act_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда для генерации акта"""
    if not context.args:
        await update.message.reply_text("Укажите номер заявки, например: /testact Библ. № 001")
        return
    
    nomer = ' '.join(context.args)
    await update.message.reply_text(f"Генерирую акт для заявки {nomer}...")
    
    pdf, message = await generate_act_from_api(nomer, "Тестовый пользователь")
    
    if pdf:
        await update.message.reply_text(f"✅ {message}")
    else:
        await update.message.reply_text(f"❌ Ошибка: {message}")

# Добавляем обработчик команды (временно, для теста)
application.add_handler(CommandHandler("testact", test_act_command))
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
