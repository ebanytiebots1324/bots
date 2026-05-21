import asyncio
import sqlite3
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

# ========== ИНФО О БОТАХ (ВСЕ С ПРОМОКОДАМИ) ==========
BOT_INFO = [
    {"name": "🎮 CS2 ПРАЙМ", "reward": "Прайм статус в CS2 НАВСЕГДА!", "promo": "CS2PRIME2026"},
    {"name": "🔫 CS2 СКИНЫ", "reward": "5 крутых скинов + кейсы!", "promo": "CS2SKINS2026"},
    {"name": "⭐ РОБУКСЫ", "reward": "1000 ROBUX на аккаунт!", "promo": "ROBUX2026"},
    {"name": "💀 СТЕНДОФФ2", "reward": "10.000 ГОЛДЫ + легендарные скины!", "promo": "STANDOFF2026"},
    {"name": "🖼️ ТГ НФТ", "reward": "Уникальная NFT карточка Telegram!", "promo": "TGNFT2026"},
    {"name": "✨ ТГ ЗВЁЗДЫ", "reward": "1000 Telegram Stars!", "promo": "TGSTARS2026"},
    {"name": "🎬 КИНОПОИСК", "reward": "Подписка Кинопоиск/Premier на 1 МЕСЯЦ!", "promo": "KINOPOISK2026"},
    {"name": "💎 BRAWL STARS", "reward": "1000 ГЕМОВ в Brawl Stars!", "promo": "BRAWL2026"},
    {"name": "⭐ ТГ ПРЕМИУМ", "reward": "Telegram Premium на 1 МЕСЯЦ!", "promo": "TGPREMIUM2026"}
]

ADMINS = ['CH4EBYRAHKA', 'Kyrsanik', 'dmitriiiy_22']

CHANNELS = [
    {"name": "ТЕМКИ", "url": "https://t.me/+X6hEJTznwuc4NWIy"},
    {"name": "ТЕЛКИ", "url": "https://t.me/+ZAmRG9tQciU0MTNi"},
    {"name": "ЛЬГОТЫ", "url": "https://t.me/+sqs0iLp5T49iNDEy"}
]

TASKS = [
    {"name": "СБЕРПРАЙМ", "url": "https://clck.ru/3Thj5H", "button": "💳 ОФОРМИТЬ ЗА 1₽"},
    {"name": "ОПРОС", "url": "https://clck.ru/3ThjD6", "button": "📊 ПРОЙТИ ОПРОС"}
]

# ========== БАЗА ДАННЫХ ==========
def init_db(db_name):
    conn = sqlite3.connect(db_name)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
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
    cur.execute('SELECT step, task1, task2, subs, waiting, current_task FROM users WHERE user_id = ?', (user_id,))
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
    cur.execute('SELECT user_id, username, first_name, task1, task2, step, date FROM users ORDER BY date DESC LIMIT 30')
    rows = cur.fetchall()
    conn.close()
    return rows

def is_admin(username):
    return username and username in ADMINS

# ========== КЛАВИАТУРЫ ==========
def main_menu(is_admin_user=False):
    btn = [[InlineKeyboardButton("🎁 ПОЛУЧИТЬ НАГРАДУ", callback_data="start")]]
    if is_admin_user:
        btn.append([InlineKeyboardButton("👑 АДМИН", callback_data="admin")])
    return InlineKeyboardMarkup(btn)

def subs_menu():
    kb = [[InlineKeyboardButton(f"📢 {ch['name']}", url=ch['url'])] for ch in CHANNELS]
    kb.append([InlineKeyboardButton("✅ ПРОВЕРИТЬ", callback_data="check")])
    kb.append([InlineKeyboardButton("❌ ОТМЕНА", callback_data="cancel")])
    return InlineKeyboardMarkup(kb)

def task_menu(num, url, btn):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(btn, url=url)],
        [InlineKeyboardButton("📸 ОТПРАВИТЬ СКРИНШОТ", callback_data=f"scr_{num}")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="menu")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="stats")],
        [InlineKeyboardButton("👥 ПОЛЬЗОВАТЕЛИ", callback_data="users")],
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
            await context.bot.send_message(uid, f"⏰ НАПОМИНАНИЕ!\n\nТы остановился на задании {task}/2\n\n📸 Отправь скриншот!")
            cur.execute('UPDATE users SET reminder=1, last_activity=? WHERE user_id=?', (now.strftime('%Y-%m-%d %H:%M:%S'), uid))
            conn.commit()
        except:
            pass
    conn.close()

# ========== ОБРАБОТЧИКИ ==========
async def start(update, context):
    user = update.effective_user
    db = context.bot_data['db']
    bot_idx = context.bot_data['bot_idx']
    info = BOT_INFO[bot_idx]
    
    update_user(db, user.id, user.username, user.first_name, step=0)
    
    text = f"""
<b>{info['name']}</b>

━━━━━━━━━━━━━━━━━━━━━━
Привет, {user.first_name}! 👋
━━━━━━━━━━━━━━━━━━━━━━

<b>📋 ЧТО НУЖНО СДЕЛАТЬ:</b>
• Подписаться на каналы
• Оформить СберПрайм за 1₽
• Пройти опрос

<b>🎁 ЧТО ТЫ ПОЛУЧИШЬ:</b>
✅ {info['reward']}

━━━━━━━━━━━━━━━━━━━━━━
<b>⏱ Весь процесс занимает 2 минуты!</b>
━━━━━━━━━━━━━━━━━━━━━━

👇 <b>Нажми на кнопку:</b>
"""
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=main_menu(is_admin(user.username)))

async def callback(update, context):
    q = update.callback_query
    await q.answer()
    user = q.from_user
    db = context.bot_data['db']
    bot_idx = context.bot_data['bot_idx']
    info = BOT_INFO[bot_idx]
    data = q.data

    # АДМИНКА
    if data == "admin" and is_admin(user.username):
        await q.edit_message_text("👑 АДМИН-ПАНЕЛЬ", reply_markup=admin_menu())
    elif data == "stats" and is_admin(user.username):
        total, t1, t2, done = get_stats(db)
        await q.edit_message_text(f"📊 СТАТИСТИКА\n\n👥 Всего: {total}\n✅ Задание 1: {t1}\n✅ Задание 2: {t2}\n🎁 Получили промокод: {done}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ НАЗАД", callback_data="admin")]]))
    elif data == "users" and is_admin(user.username):
        users = get_all_users(db)
        text = "👥 ПОЛЬЗОВАТЕЛИ:\n\n"
        for uid, username, first_name, t1, t2, step, date in users:
            status = "✅" if step == 3 else "⏳"
            name = first_name or username or uid
            text += f"{status} {name} | 1:{t1} 2:{t2}\n"
        await q.edit_message_text(text[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ НАЗАД", callback_data="admin")]]))

    # ОСНОВНОЙ ФЛОУ
    elif data == "start":
        update_user(db, user.id, user.username, user.first_name, step=1)
        await q.edit_message_text(f"📢 ПОДПИШИСЬ НА КАНАЛЫ:", reply_markup=subs_menu())
    
    elif data == "check":
        update_user(db, user.id, user.username, user.first_name, subs=1, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder=0)
        await q.edit_message_text(f"✅ ПОДПИСКИ ПОДТВЕРЖДЕНЫ!\n\n📌 ЗАДАНИЕ 1/2:\nОформи СберПрайм за 1₽\n\n🔗 Нажми на кнопку, оформи и отправь скриншот:",
                                  reply_markup=task_menu(1, TASKS[0]['url'], TASKS[0]['button']))
    
    elif data == "menu":
        text = f"""
<b>{info['name']}</b>

━━━━━━━━━━━━━━━━━━━━━━
<b>📋 ЧТО НУЖНО СДЕЛАТЬ:</b>
• Подписаться на каналы
• Оформить СберПрайм за 1₽
• Пройти опрос

<b>🎁 ЧТО ТЫ ПОЛУЧИШЬ:</b>
✅ {info['reward']}
━━━━━━━━━━━━━━━━━━━━━━
"""
        await q.edit_message_text(text, parse_mode='HTML', reply_markup=main_menu(is_admin(user.username)))
    
    elif data == "cancel":
        update_user(db, user.id, user.username, user.first_name, step=0, waiting=0)
        await q.edit_message_text("❌ ОТМЕНЕНО", reply_markup=main_menu(is_admin(user.username)))
    
    elif data == "scr_1":
        update_user(db, user.id, user.username, user.first_name, waiting=1, current_task=1, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder=0)
        await q.edit_message_text(f"📸 ОТПРАВЬ СКРИНШОТ ПОДТВЕРЖДЕНИЯ ОФОРМЛЕНИЯ СБЕРПРАЙМА\n\n⏱ Проверка займет 3 секунды...")
    
    elif data == "scr_2":
        udata = get_user(db, user.id)
        if udata and udata[1] == 1:
            update_user(db, user.id, user.username, user.first_name, waiting=1, current_task=2, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder=0)
            await q.edit_message_text(f"📸 ОТПРАВЬ СКРИНШОТ ПОДТВЕРЖДЕНИЯ ПРОХОЖДЕНИЯ ОПРОСА\n\n⏱ Проверка займет 3 секунды...")
        else:
            await q.answer("Сначала выполни задание 1!", show_alert=True)

async def photo(update, context):
    user = update.effective_user
    db = context.bot_data['db']
    bot_idx = context.bot_data['bot_idx']
    info = BOT_INFO[bot_idx]
    
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
        await update.message.reply_text(f"✅ ЗАДАНИЕ 1 ВЫПОЛНЕНО!\n\n📌 ЗАДАНИЕ 2/2: ПРОЙДИ ОПРОС\n\n🔗 Нажми на кнопку, пройди и отправь скриншот:",
                                        reply_markup=task_menu(2, TASKS[1]['url'], TASKS[1]['button']))
    else:
        update_user(db, user.id, user.username, user.first_name, task2=1, waiting=0, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reminder=0, step=3)
        
        await update.message.reply_text(f"""
✅ ВСЕ ЗАДАНИЯ ВЫПОЛНЕНЫ!

━━━━━━━━━━━━━━━━━━━━━━
🎁 ТВОЯ НАГРАДА:
{info['reward']}

🔑 АКТИВИРУЙ ПРОМОКОД:
<code>{info['promo']}</code>

━━━━━━━━━━━━━━━━━━━━━━
📝 Инструкция по активации:
1. Скопируй промокод
2. Введи в игре/приложении
3. Получи награду сразу!

Спасибо за участие! 🎮
━━━━━━━━━━━━━━━━━━━━━━
""", parse_mode='HTML')

# ========== ЗАПУСК ОДНОГО БОТА ==========
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
    print(f"✅ {BOT_INFO[idx]['name']} запущен")
    
    while True:
        await asyncio.sleep(1)

# ========== ЗАПУСК ВСЕХ ==========
async def main():
    print("🚀 ЗАПУСК 9 БОТОВ...")
    print(f"👑 Админы: {', '.join(ADMINS)}")
    
    tasks = []
    for i, token in enumerate(BOT_TOKENS):
        tasks.append(asyncio.create_task(run_bot(token, i)))
        await asyncio.sleep(2)
    
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
