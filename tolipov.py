import logging
import re
import random
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬТЕ_ТОКЕН_В_ПЕРЕМЕННУЮ_ОКРУЖЕНИЯ")


BOT_NAMES = ["толипов", "tolipov"]

PATTERNS = [
    (r"кто не знает ([а-яА-Яa-zA-Z0-9\s]+)", "не знает"),
    (r"кто не умеет ([а-яА-Яa-zA-Z0-9\s]+)", "не умеет"),
    (r"кто не понимает ([а-яА-Яa-zA-Z0-9\s]+)", "не понимает"),
    (r"кто не может ([а-яА-Яa-zA-Z0-9\s]+)", "не может"),
    (r"кто не любит ([а-яА-Яa-zA-Z0-9\s]+)", "не любит"),
    (r"кто плохо знает ([а-яА-Яa-zA-Z0-9\s]+)", "плохо знает"),
    (r"кто знает ([а-яА-Яa-zA-Z0-9\s]+)", "знает"),
    (r"кто умеет ([а-яА-Яa-zA-Z0-9\s]+)", "умеет"),
    (r"кто понимает ([а-яА-Яa-zA-Z0-9\s]+)", "понимает"),
    (r"кто может ([а-яА-Яa-zA-Z0-9\s]+)", "може"),
    (r"кто любит ([а-яА-Яa-zA-Z0-9\s]+)", "любит"),
    (r"кто хочет ([а-яА-Яa-zA-Z0-9\s]+)", "хочет"),
    (r"кто самый ([а-яА-Яa-zA-Z0-9\s]+)", "самый"),
    (r"кто лучший ([а-яА-Яa-zA-Z0-9\s]+)", "лучший"),
     (r"кто лучше ([а-яА-Яa-zA-Z0-9\s]+)", "лучше"),
    (r"кто главный ([а-яА-Яa-zA-Z0-9\s]+)", "главный"),
    (r"у кого есть ([а-яА-Яa-zA-Z0-9\s]+)", "есть"),
    (r"у кого нет ([а-яА-Яa-zA-Z0-9\s]+)", "нет"),
     (r"у кого ([а-яА-Яa-zA-Z0-9\s]+)", "нет"),
     (r"кто худше([а-яА-Яa-zA-Z0-9\s]+)", "худше"),
      (r"кто смотрит ([а-яА-Яa-zA-Z0-9\s]+)", "смотрит"),
       (r"кто ([а-яА-Яa-zA-Z0-9\s]+)", ""),
]

# Кэш участников (хранится в памяти)
members_cache = {}
# Простое хранилище активных участников (кто писал сообщения)
active_members = {}

def check_bot_mentioned(text):
    """Проверяет, упомянут ли бот"""
    text_lower = text.lower()
    for bot_name in BOT_NAMES:
        if bot_name in text_lower:
            return True
    return False

async def load_admins_once(chat_id, context):
    """Загружает администраторов ОДИН РАЗ при старте"""
    try:
        print(f"🔄 Загружаю администраторов группы...")
        administrators = await context.bot.get_chat_administrators(chat_id)
        
        admins_list = []
        for admin in administrators:
            user = admin.user
            if user.is_bot:
                continue
            
            admins_list.append({
                'id': user.id,
                'first_name': user.first_name,
            })
        
        members_cache[chat_id] = admins_list
        print(f"✅ Загружено {len(admins_list)} администраторов")
        
        return admins_list
    except Exception as e:
        logger.error(f"Ошибка загрузки админов: {e}")
        return []

def get_random_member_fast(chat_id):
    """БЫСТРЫЙ выбор участника из кэша"""
    # Объединяем админов и активных участников
    all_members = []
    
    # Добавляем админов из кэша
    if chat_id in members_cache:
        all_members.extend(members_cache[chat_id])
    
    # Добавляем активных участников
    if chat_id in active_members:
        all_members.extend(active_members[chat_id])
    
    # Убираем дубликаты по ID
    unique_members = []
    seen_ids = set()
    for member in all_members:
        if member['id'] not in seen_ids:
            unique_members.append(member)
            seen_ids.add(member['id'])
    
    if unique_members:
        return random.choice(unique_members)
    else:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Привет! Меня зовут tolipov! 👋\n\n"
        f"Упомяните меня:\n"
        f"• tolipov, кто не знает программирование?\n"
        f"• толипов, кто хочет поесть?\n\n"
        f"⚠️ Сделайте меня администратором!"
    )

async def refresh_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновить список участников"""
    chat_id = update.message.chat.id

    if update.message.chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Только для групп!")
        return
    
    await update.message.reply_text("🔄 Обновляю...")
    
    admins = await load_admins_once(chat_id, context)
    active_count = len(active_members.get(chat_id, []))
    
    await update.message.reply_text(
        f"✅ Готово!\n"
        f"👥 Админов: {len(admins)}\n"
        f"💬 Активных: {active_count}"
    )

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    if message.chat.type not in ['group', 'supergroup']:
        return
    
    if not message.text:
        return
    
    chat_id = message.chat.id
    
    # Сохраняем активного участника (кто написал)
    if chat_id not in active_members:
        active_members[chat_id] = []
    
    user_info = {
        'id': message.from_user.id,
        'first_name': message.from_user.first_name,
    }
    
    # Добавляем только если его нет
    existing_ids = [u['id'] for u in active_members[chat_id]]
    if user_info['id'] not in existing_ids:
        active_members[chat_id].append(user_info)
    
    # Загружаем админов при первом сообщении
    if chat_id not in members_cache:
        await load_admins_once(chat_id, context)
    
    # Проверяем упоминание
    if not check_bot_mentioned(message.text):
        return
    
    text = message.text.lower()
    
    # Проверяем паттерны
    for pattern, action in PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            topic = match.group(1).strip()
            
            # БЫСТРЫЙ выбор из кэша
            random_member = get_random_member_fast(chat_id)
            
            if random_member:
                user_name = random_member['first_name']
            else:
                user_name = message.from_user.first_name
            
            # Формируем ответ
            if action in ["самый", "лучший", "главный"]:
                response = f"🤔 Я думаю, что {user_name} {action} {topic}"
            elif action == "есть":
                response = f"🤔 Я думаю, что у {user_name} есть {topic}"
            elif action == "нет":
                response = f"🤔 Я думаю, что у {user_name} нет {topic}"
            else:
                response = f"🤔 Я думаю, что {user_name} {action} {topic}"
            
            # Отвечаем МГНОВЕННО
            await message.reply_text(response)
            break

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")

def main():
    if "ВСТАВЬТЕ_ТОКЕН" in BOT_TOKEN:
        print("❌ Вставьте токен!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("refresh", refresh_members))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_message))
    application.add_error_handler(error_handler)
    
    print("✅ tolipov запущен!")
    print("⚡ БЫСТРАЯ версия (использует кэш)")
    print("💬 Напишите '/refresh' в группе для загрузки участников")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()