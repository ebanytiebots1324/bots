import asyncio
import sqlite3
import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== ТОКЕНЫ 9 БОТОВ ==========
BOT_TOKENS = [
    "8633809924:AAGLwVQSfBDzQUNU3GKhceMUV_pzNtpcAHA",
    "8315119156:AAE6dIIYMsE80f7TVAyby_qMxKtqdzm5EOo",
    "8583713671:AAEeKGKmZBzQ0rqsiDShGXjOnijN6G-32-w",
    "8445466695:AAGORyjHM8ghSs2jhKblwwrO0-aJNp6Zuq8",
    "8408906854:AAH1o9LAf9kKKMh6mmZj0BGAlsE670DjslA",
    "8622662261:AAFfT6Ye6tB8O01QhjYRYinHrxpr9ZykvOw",
    "8562359492:AAFWc3XXKAtCkCh_Y8uznLcY6lFZFdI7gn0",
    "8644384412:AAFi1bGQdE9dm9rLnCi51lvpLaXphdUyx0s",
    "8784577185:AAEsqS036U2aWV4ElydYvBAM-bSiHwWhFGI",
]

# ========== ДИЗАЙН БОТОВ ==========
BOT_DESIGN = [
    {
        "name": "🎮 CS2 ПРАЙМ",
        "emoji": "🎮",
        "color": "🔫",
        "reward": "Прайм статус в CS2 НАВСЕГДА!",
        "short_reward": "Прайм статус"
    },
    {
        "name": "🔫 CS2 СКИНЫ",
        "emoji": "🔫",
        "color": "⚡",
        "reward": "5 крутых скинов + кейсы + нож в подарок!",
        "short_reward": "5 скинов"
    },
    {
        "name": "⭐ РОБУКСЫ",
        "emoji": "⭐",
        "color": "💰",
        "reward": "1000 ROBUX на аккаунт!",
        "short_reward": "1000 ROBUX"
    },
    {
        "name": "💀 СТЕНДОФФ2",
        "emoji": "💀",
        "color": "🔥",
        "reward": "10.000 ГОЛДЫ + легендарные скины!",
        "short_reward": "10.000 голды"
    },
    {
        "name": "🖼️ ТГ НФТ",
        "emoji": "🖼️",
        "color": "🎨",
        "reward": "Уникальная NFT карточка Telegram!",
        "short_reward": "NFT карта"
    },
    {
        "name": "✨ ТГ ЗВЁЗДЫ",
        "emoji": "✨",
        "color": "🌟",
        "reward": "1000 Telegram Stars!",
        "short_reward": "1000 Stars"
    },
    {
        "name": "🎬 КИНОПОИСК",
        "emoji": "🎬",
        "color": "📽️",
        "reward": "Подписка Кинопоиск/Premier на 1 МЕСЯЦ!",
        "short_reward": "Подписка"
    },
    {
        "name": "💎 BRAWL STARS",
        "emoji": "💎",
        "color": "⚔️",
        "reward": "1000 ГЕМОВ в Brawl Stars!",
        "short_reward": "1000 гемов"
    },
    {
        "name": "⭐ ТГ ПРЕМИУМ",
        "emoji": "⭐",
        "color": "💎",
        "reward": "Telegram Premium на 1 МЕСЯЦ!",
        "short_reward": "TG Premium"
    }
]

ADMINS = ['CH4EBYRAHKA', 'Kyrsanik', 'dmitriiiy_22']

CHANNELS = [
    {"name": "🎮 ТЕМКИ", "url": "https://t.me/+X6hEJTznwuc4NWIy"},
    {"name": "👾 ТЕЛКИ", "url": "https://t.me/+ZAmRG9tQciU0MTNi"},
    {"name": "🎁 ЛЬГОТЫ", "url": "https://t.me/+sqs0iLp5T49iNDEy"}
]

TASKS = [
    {"name": "💳 СБЕРПРАЙМ", "url": "https://clck.ru/3Thj5H", "button": "💳 ОФОРМИТЬ ЗА 1₽"},
    {"name": "📊 ОПРОС", "url": "https://clck.ru/3ThjD6", "button": "📊 ПРОЙТИ ОПРОС"}
]

# ========== ГЕНЕРАТОР ПРОМОКОДОВ ==========
def generate_promo(user_id, bot_name):
    clean_name = ''.join(c for c in bot_name if c.isalnum() or c == ' ').strip().replace(' ', '')[:4].upper()
    user_part = str(user_id)[-4:]
    date_part = datetime.now().strftime('%d%m')
    random_letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    random_numbers = ''.join(random.choices(string.digits, k=3))
    
    formats = [
        f"{clean_name}-{user_part}-{random_letters}",
        f"{random_letters}{user_part}{date_part}",
        f"{clean_name}{random_numbers}{user_part[-2:]}",
        f"{date_part}-{random_letters}-{user_part}",
        f"{random_letters}-{random_numbers}-{user_part}"
    ]
    return random.choice(formats)

# ========== БАЗА ДАННЫХ ==========
def init_db(db_name):
    conn = sqlite3.connect(db_name)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        promo_code TEXT,
        step INTEGER DEFAULT 0,
        task1 INTEGER DEFAULT 0,
        task2 INTEGER DEFAULT 0,
        subs INTEGER DEFAULT 0,
        waiting INTEGER DEFAULT 0,
        current_task INTEGER DEFAULT 0,
        last_activity TEXT,
        reminder INTEGER DEFAULT 0,
        date TEXT
    )''')
    conn.commit()
    conn.close()

def get_user(db_name, user_id):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('SELECT step, task1, task2, subs, waiting, current_task, promo_code FROM users WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_user(db_name, user_id, username, first_name, **kwargs):
    conn = sqlite3.connect(db_name)
    if not get_user(db_name, user_id):
        conn.execute('INSERT INTO users (user_id, username, first_name, date, last_activity) VALUES (?, ?, ?, ?, ?)',
                     (user_id, username, first_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    for key, val in kwargs.items():
        conn.execute(f'UPDATE users SET {key} = ? WHERE user_id = ?', (val, user_id))
    conn.commit()
    conn.close()

def get_stats(db_name):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM users')
    total = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM users WHERE task1=1')
    t1 = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM users WHERE task2=1')
    t2 = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM users WHERE step=3')
    done = cur.fetchone()[0]
    conn.close()
    return total, t1, t2, done

def get_all_users(db_name):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('SELECT user_id, username, first_name, task1, task2, step, promo_code, date FROM users ORDER BY date DESC LIMIT 30')
    rows = cur.fetchall()
    conn.close()
    return rows

def is_admin(username):
    return username and username in ADMINS

# ========== ДИЗАЙН КЛАВИАТУР ==========
def main_menu(is_admin_user=False):
    btn = [
        [InlineKeyboardButton("🎁 ПОЛУЧИТЬ НАГРАДУ 🎁", callback_data="start")]
    ]
    if is_admin_user:
        btn.append([InlineKeyboardButton("👑 АДМИН-ПАНЕЛЬ 👑", callback_data="admin")])
    return InlineKeyboardMarkup(btn)

def subs_menu():
    kb = []
    for ch in CHANNELS:
        kb.append([InlineKeyboardButton(f"🔗 {ch['name']} | ПОДПИСАТЬСЯ", url=ch['url'])])
    kb.append([InlineKeyboardButton("✅ ПРОВЕРИТЬ ПОДПИСКИ ✅", callback_data="check")])
    kb.append([InlineKeyboardButton("❌ ОТМЕНИТЬ ❌", callback_data="cancel")])
    return InlineKeyboardMarkup(kb)

def task_menu(num, url, btn):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔗 {btn} 🔗", url=url)],
        [InlineKeyboardButton("📸 ОТПРАВИТЬ СКРИНШОТ 📸", callback_data=f"scr_{num}")],
        [InlineKeyboardButton("◀️ НАЗАД В МЕНЮ ◀️", callback_data="menu")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="stats")],
        [InlineKeyboardButton("👥 СПИСОК ПОЛЬЗОВАТЕЛЕЙ", callback_data="users")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="menu")]
    ])

# ========== НАПОМИНАНИЯ ==========
async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    now = datetime.now()
    two_hours_ago = (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    cur.execute('SELECT user_id, current_task FROM users WHERE waiting=1 AND (reminder=0 OR last_activity < ?)', (two_hours_ago,))
    for uid, task in cur.fetchall():
        try:
            await context.bot.send_message(uid, 
                f"⏰ ═══════════════════ ⏰\n\n"
                f"🔔 НАПОМИНАНИЕ!\n\n"
                f"📋 Ты остановился на задании {task}/2\n\n"
                f"📸 Отправь скриншот, чтобы продолжить!\n\n"
                f"⏰ ═══════════════════ ⏰")
            cur.execute('UPDATE users SET reminder=1, last_activity=? WHERE user_id=?', (now.strftime('%Y-%m-%d %H:%M:%S'), uid))
            conn.commit()
        except:
            pass
    conn.close()

# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========
async def start(update, context):
    user = update.effective_user
    db = context.bot_data['db']
    bot_idx = context.bot_data['bot_idx']
    design = BOT_DESIGN[bot_idx]
    
    update_user(db, user.id, user.username, user.first_name, step=0)
    
    text = f"""
{design['emoji']} ═══════════════════════════ {design['emoji']}
         {design['name']}
{design['emoji']} ═══════════════════════════ {design['emoji']}

✨ ПРИВЕТ, {user.first_name}! ✨

{design['color']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{design['color']}

📋 ЧТО НУЖНО СДЕЛАТЬ:

   1️⃣ ПОДПИСАТЬСЯ на каналы
   2️⃣ ОФОРМИТЬ СберПрайм за 1₽
   3️⃣ ПРОЙТИ короткий опрос

{design['color']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{design['color']}

🎁 ЧТО ТЫ ПОЛУЧИШЬ:

   ✅ {design['reward']}

{design['color']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{design['color']}

⏱ ВЕСЬ ПРОЦЕСС ЗАНИМАЕТ 2 МИНУТЫ!

{design['emoji']} ═══════════════════════════ {design['emoji']}

👇 НАЖМИ НА КНОПКУ 👇
"""
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=main_menu(is_admin(user.username)))

async def callback(update, context):
    q = update.callback_query
    await q.answer()
    user = q.from_user
    db = context.bot_data['db']
    bot_idx = context.bot_data['bot_idx']
    design = BOT_DESIGN[bot_idx]
    data = q.data

    # АДМИНКА
    if data == "admin" and is_admin(user.username):
        await q.edit_message_text("👑 АДМИН-ПАНЕЛЬ", reply_markup=admin_menu())
    elif data == "stats" and is_admin(user.username):
        total, t1, t2, done = get_stats(db)
        text = f"""
📊 ═══════════════════ 📊
      СТАТИСТИКА
📊 ═══════════════════ 📊

👥 ВСЕГО ПОЛЬЗОВАТЕЛЕЙ: {total}
✅ ВЫПОЛНИЛИ ЗАДАНИЕ 1: {t1}
✅ ВЫПОЛНИЛИ ЗАДАНИЕ 2: {t2}
🎁 ПОЛУЧИЛИ ПРОМОКОД: {done}

📊 ═══════════════════ 📊
"""
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ НАЗАД", callback_data="admin")]]))
    elif data == "users" and is_admin(user.username):
        users = get_all_users(db)
        text = "👥 ПОЛЬЗОВАТЕЛИ:\n\n"
        for uid, username, first_name, t1, t2, step, promo, date in users:
            status = "✅" if step == 3 else "⏳"
            name = first_name or username or str(uid)
            text += f"{status} {name} | 1:{t1} 2:{t2}\n"
            if promo:
                text += f"   🔑 {promo}\n"
        await q.edit_message_text(text[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ НАЗАД", callback_data="admin")]]))

    # ОСНОВНОЙ ФЛОУ
    elif data == "start":
        update_user(db, user.id, user.username, user.first_name, step=1)
        text = f"""
📢 ═══════════════════ 📢
    ПОДПИШИСЬ НА КАНАЛЫ
📢 ═══════════════════ 📢

🔔 ЧТОБЫ ПОЛУЧИТЬ {design['short_reward']}, 
   ПОДПИШИСЬ НА КАНАЛЫ НИЖЕ!

👇 ПОСЛЕ ПОДПИСКИ НАЖМИ ПРОВЕРИТЬ 👇
"""
        await q.edit_message_text(text, reply_markup=subs_menu())
    
    elif data == "check":
        update_user(db, user.id, user.username, user.first_name, subs=1, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder=0)
        text = f"""
✅ ═══════════════════ ✅
    ПОДПИСКИ ПОДТВЕРЖДЕНЫ!
✅ ═══════════════════ ✅

📋 ЗАДАНИЕ 1/2: СБЕРПРАЙМ

🔹 ОФОРМИ ПОДПИСКУ СБЕРПРАЙМ ЗА 1₽
🔹 СДЕЛАЙ СКРИНШОТ ПОДТВЕРЖДЕНИЯ
🔹 ОТПРАВЬ СКРИНШОТ СЮДА

👇 НАЖМИ НА КНОПКУ, ОФОРМИ И ОТПРАВЬ СКРИН 👇
"""
        await q.edit_message_text(text, reply_markup=task_menu(1, TASKS[0]['url'], TASKS[0]['button']))
    
    elif data == "menu":
        text = f"""
{design['emoji']} ═══════════════════════════ {design['emoji']}
         {design['name']}
{design['emoji']} ═══════════════════════════ {design['emoji']}

📋 ЧТО НУЖНО СДЕЛАТЬ:

   1️⃣ ПОДПИСАТЬСЯ на каналы
   2️⃣ ОФОРМИТЬ СберПрайм за 1₽
   3️⃣ ПРОЙТИ короткий опрос

🎁 ЧТО ТЫ ПОЛУЧИШЬ:

   ✅ {design['reward']}

{design['emoji']} ═══════════════════════════ {design['emoji']}
"""
        await q.edit_message_text(text, parse_mode='HTML', reply_markup=main_menu(is_admin(user.username)))
    
    elif data == "cancel":
        update_user(db, user.id, user.username, user.first_name, step=0, waiting=0)
        await q.edit_message_text("❌ ОТМЕНЕНО", reply_markup=main_menu(is_admin(user.username)))
    
    elif data == "scr_1":
        update_user(db, user.id, user.username, user.first_name, waiting=1, current_task=1, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder=0)
        text = f"""
📸 ═══════════════════ 📸
    ОТПРАВЬ СКРИНШОТ
📸 ═══════════════════ 📸

ЧТО ДОЛЖНО БЫТЬ НА СКРИНЕ:
   ✅ ПОДТВЕРЖДЕНИЕ ОФОРМЛЕНИЯ
      СБЕРПРАЙМА ЗА 1₽

⏱ ПРОВЕРКА ЗАЙМЕТ 3 СЕКУНДЫ

📸 ═══════════════════ 📸
"""
        await q.edit_message_text(text)
    
    elif data == "scr_2":
        udata = get_user(db, user.id)
        if udata and udata[1] == 1:
            update_user(db, user.id, user.username, user.first_name, waiting=1, current_task=2, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder=0)
            text = f"""
📸 ═══════════════════ 📸
    ОТПРАВЬ СКРИНШОТ
📸 ═══════════════════ 📸

ЧТО ДОЛЖНО БЫТЬ НА СКРИНЕ:
   ✅ ПОДТВЕРЖДЕНИЕ ПРОХОЖДЕНИЯ
      ОПРОСА

⏱ ПРОВЕРКА ЗАЙМЕТ 3 СЕКУНДЫ

📸 ═══════════════════ 📸
"""
            await q.edit_message_text(text)
        else:
            await q.answer("Сначала выполни задание 1!", show_alert=True)

async def photo(update, context):
    user = update.effective_user
    db = context.bot_data['db']
    bot_idx = context.bot_data['bot_idx']
    design = BOT_DESIGN[bot_idx]
    
    udata = get_user(db, user.id)
    if not udata or udata[4] != 1:
        await update.message.reply_text("❌ Сейчас не нужно отправлять скриншот")
        return
    task = udata[5]
    msg = await update.message.reply_text("⏳ ПРОВЕРКА СКРИНШОТА...")
    await asyncio.sleep(3)
    await msg.delete()
    
    if task == 1:
        update_user(db, user.id, user.username, user.first_name, task1=1, waiting=0, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder=0)
        text = f"""
✅ ═══════════════════ ✅
    ЗАДАНИЕ 1 ВЫПОЛНЕНО!
✅ ═══════════════════ ✅

📋 ЗАДАНИЕ 2/2: ОПРОС

🔹 ПРОЙДИ КОРОТКИЙ ОПРОС
🔹 СДЕЛАЙ СКРИНШОТ
🔹 ОТПРАВЬ СКРИНШОТ СЮДА

👇 НАЖМИ НА КНОПКУ, ПРОЙДИ И ОТПРАВЬ СКРИН 👇
"""
        await update.message.reply_text(text, reply_markup=task_menu(2, TASKS[1]['url'], TASKS[1]['button']))
    else:
        promo_code = generate_promo(user.id, design['name'])
        update_user(db, user.id, user.username, user.first_name, task2=1, waiting=0, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder=0, step=3, promo_code=promo_code)
        
        text = f"""
{design['emoji']} ═══════════════════════════ {design['emoji']}
         🎉 ПОЗДРАВЛЯЮ! 🎉
{design['emoji']} ═══════════════════════════ {design['emoji']}

✅ ВСЕ ЗАДАНИЯ ВЫПОЛНЕНЫ!

{design['color']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{design['color']}

🎁 ТВОЯ НАГРАДА:
   {design['reward']}

🔑 ТВОЙ УНИКАЛЬНЫЙ ПРОМОКОД:

   ╔══════════════════════╗
   ║  <code>{promo_code}</code>  ║
   ╚══════════════════════╝

{design['color']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{design['color']}

📝 ИНСТРУКЦИЯ:
   1️⃣ Скопируй промокод (нажми на него)
   2️⃣ Введи в игре/приложении
   3️⃣ Получи награду СРАЗУ!

⚠️ ПРОМОКОД ДЕЙСТВИТЕЛЕН 24 ЧАСА!

{design['emoji']} ═══════════════════════════ {design['emoji']}
         СПАСИБО ЗА УЧАСТИЕ! 🎮
{design['emoji']} ═══════════════════════════ {design['emoji']}
"""
        await update.message.reply_text(text, parse_mode='HTML')

# ========== ЗАПУСК БОТА ==========
async def run_bot(token, idx):
    db = f'users_{idx+1}.db'
    init_db(db)
    
    app = Application.builder().token(token).build()
    app.bot_data['db'] = db
    app.bot_data['bot_idx'] = idx
    
    if app.job_queue:
        app.job_queue.run_repeating(check_reminders, interval=7200, first=10)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.PHOTO, photo))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print(f"✅ {BOT_DESIGN[idx]['name']} запущен")
    
    while True:
        await asyncio.sleep(1)

# ========== ЗАПУСК ВСЕХ ==========
async def main():
    print("🚀 ЗАПУСК 9 БОТОВ...")
    print(f"👑 Админы: {', '.join(ADMINS)}")
    print("🎨 ПРЕМИУМ ДИЗАЙН АКТИВИРОВАН!")
    
    tasks = []
    for i, token in enumerate(BOT_TOKENS):
        tasks.append(asyncio.create_task(run_bot(token, i)))
        await asyncio.sleep(2)
    
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
