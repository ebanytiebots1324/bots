import os
import asyncio
import sqlite3
import re
from datetime import datetime, timedelta
from flask import Flask
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

BOT_NAMES = [
    "🎮 CS2 ПРАЙМ",
    "🔫 CS2 СКИНЫ",
    "⭐ РОБУКСЫ",
    "💀 СТЕНДОФФ2",
    "🖼️ ТГ НФТ",
    "✨ ТГ ЗВЁЗДЫ",
    "🎬 КИНОПОИСК",
    "💎 BRAWL STARS",
    "⭐ ТГ ПРЕМИУМ"
]

ADMINS = ['CH4EBYRAHKA', 'Kyrsanik', 'dmitriiiy_22']

CHANNELS = [
    {"name": "ТЕМКИ", "url": "https://t.me/+X6hEJTznwuc4NWIy"},
    {"name": "ТЕЛКИ", "url": "https://t.me/+ZAmRG9tQciU0MTNi"},
    {"name": "ЛЬГОТЫ", "url": "https://t.me/+sqs0iLp5T49iNDEy"}
]

TASKS = [
    {"name": "СБЕРПРАЙМ", "desc": "Оформи подписку СберПрайм за 1 рубль", "url": "https://clck.ru/3Thj5H", "button": "💳 ОФОРМИТЬ"},
    {"name": "ОПРОС", "desc": "Пройди короткий опрос", "url": "https://clck.ru/3ThjD6", "button": "📊 ПРОЙТИ"}
]

flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return 'Боты работают!'

def run_flask():
    port = int(os.environ.get('PORT', 3000))
    flask_app.run(host='0.0.0.0', port=port)

def init_db(db_name):
    conn = sqlite3.connect(db_name)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        step INTEGER DEFAULT 0,
        task1_done INTEGER DEFAULT 0,
        task2_done INTEGER DEFAULT 0,
        subs_done INTEGER DEFAULT 0,
        waiting_screenshot INTEGER DEFAULT 0,
        current_task INTEGER DEFAULT 0,
        last_activity TEXT,
        reminder_sent INTEGER DEFAULT 0,
        player_id TEXT,
        date TEXT
    )''')
    conn.commit()
    conn.close()

def get_user(db_name, user_id):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('SELECT step, task1_done, task2_done, subs_done, waiting_screenshot, current_task, last_activity, reminder_sent, player_id FROM users WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_user(db_name, user_id, username, **kwargs):
    conn = sqlite3.connect(db_name)
    if not get_user(db_name, user_id):
        conn.execute('INSERT INTO users (user_id, username, date, last_activity) VALUES (?, ?, ?, ?)',
                     (user_id, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    for key, val in kwargs.items():
        conn.execute(f'UPDATE users SET {key} = ? WHERE user_id = ?', (val, user_id))
    conn.commit()
    conn.close()

def get_stats(db_name):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM users')
    total = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM users WHERE task1_done=1')
    task1 = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM users WHERE task2_done=1')
    task2 = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM users WHERE step=4')
    completed = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM users WHERE waiting_screenshot=1')
    stuck = cur.fetchone()[0]
    conn.close()
    return total, task1, task2, completed, stuck

def get_all_users(db_name):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('SELECT user_id, username, task1_done, task2_done, subs_done, player_id, step FROM users ORDER BY date DESC')
    rows = cur.fetchall()
    conn.close()
    return rows

def is_admin(username):
    return username and username in ADMINS

def is_player_id(text):
    return bool(re.match(r'^[A-Z0-9]{8,10}$', text.strip().upper().replace('#', '')))

def get_main_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎁 ПОЛУЧИТЬ НАГРАДУ", callback_data="start")]])

def get_subs_keyboard():
    keyboard = [[InlineKeyboardButton(f"📢 {ch['name']}", url=ch['url'])] for ch in CHANNELS]
    keyboard.append([InlineKeyboardButton("✅ ПРОВЕРИТЬ", callback_data="check_subs")])
    keyboard.append([InlineKeyboardButton("❌ ОТМЕНА", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)

def get_task_keyboard(task_num, task_url, task_button):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(task_button, url=task_url)],
        [InlineKeyboardButton("📸 ОТПРАВИТЬ СКРИН", callback_data=f"task_{task_num}_screenshot")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="menu")]
    ])

def get_admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 ВСЕ ПОЛЬЗОВАТЕЛИ", callback_data="admin_users")],
        [InlineKeyboardButton("⏰ ЗАСТРЯВШИЕ", callback_data="admin_stuck")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="menu")]
    ])

async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    db_name = context.bot_data['db_name']
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    now = datetime.now()
    two_hours_ago = (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    cur.execute('SELECT user_id, username, current_task FROM users WHERE waiting_screenshot=1 AND (reminder_sent=0 OR last_activity < ?)', (two_hours_ago,))
    for user_id, username, current_task in cur.fetchall():
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"⏰ НАПОМИНАНИЕ!\n\nТы остановился на задании {current_task}/2\n\n📸 Отправь скриншот!"
            )
            cur.execute('UPDATE users SET reminder_sent=1, last_activity=? WHERE user_id=?', (now.strftime('%Y-%m-%d %H:%M:%S'), user_id))
            conn.commit()
        except:
            pass
    conn.close()

async def start(update, context):
    user = update.effective_user
    db = context.bot_data['db']
    update_user(db, user.id, user.username, step=0)
    text = f"{context.bot_data['name']}\n\nПривет, {user.first_name}!\n\n🔥 Выполни задания и получи награду!"
    if is_admin(user.username):
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 ПОЛУЧИТЬ", callback_data="start")],
            [InlineKeyboardButton("👑 АДМИН", callback_data="admin_panel")]
        ]))
    else:
        await update.message.reply_text(text, reply_markup=get_main_menu())

async def callback(update, context):
    q = update.callback_query
    await q.answer()
    user = q.from_user
    db = context.bot_data['db']
    data = q.data

    if data == "admin_panel" and is_admin(user.username):
        await q.edit_message_text("👑 АДМИН-ПАНЕЛЬ", reply_markup=get_admin_keyboard())
    elif data == "admin_stats" and is_admin(user.username):
        total, t1, t2, done, stuck = get_stats(db)
        await q.edit_message_text(f"📊 СТАТИСТИКА\n\nВсего: {total}\nЗадание 1: {t1}\nЗадание 2: {t2}\nНаграда: {done}\nЗастряли: {stuck}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ НАЗАД", callback_data="admin_panel")]]))
    elif data == "admin_users" and is_admin(user.username):
        users = get_all_users(db)
        text = "👥 ПОЛЬЗОВАТЕЛИ:\n\n"
        for u in users[:20]:
            uid, name, t1, t2, subs, pid, step = u
            text += f"{'✅' if step==4 else '⏳'} @{name or uid} | 1:{t1} 2:{t2}\n"
        await q.edit_message_text(text[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ НАЗАД", callback_data="admin_panel")]]))
    elif data == "admin_stuck" and is_admin(user.username):
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute('SELECT user_id, username, current_task, last_activity FROM users WHERE waiting_screenshot=1')
        stuck = cur.fetchall()
        conn.close()
        text = "⏰ ЗАСТРЯВШИЕ:\n\n" + "\n".join([f"@{u[1] or u[0]} | Задание {u[2]}" for u in stuck]) or "Нет"
        await q.edit_message_text(text[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ НАЗАД", callback_data="admin_panel")]]))
    elif data == "start":
        update_user(db, user.id, user.username, step=1)
        await q.edit_message_text("📢 ПОДПИШИСЬ НА КАНАЛЫ:", reply_markup=get_subs_keyboard())
    elif data == "check_subs":
        update_user(db, user.id, user.username, subs_done=1, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        await q.edit_message_text("✅ ПОДПИСКИ ПОДТВЕРЖДЕНЫ!\n\nЗадание 1/2:", reply_markup=get_task_keyboard(1, TASKS[0]['url'], TASKS[0]['button']))
    elif data == "menu":
        if is_admin(user.username):
            await q.edit_message_text("Меню:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎁 ПОЛУЧИТЬ", callback_data="start")], [InlineKeyboardButton("👑 АДМИН", callback_data="admin_panel")]]))
        else:
            await q.edit_message_text("Меню:", reply_markup=get_main_menu())
    elif data == "cancel":
        update_user(db, user.id, user.username, step=0)
        await q.edit_message_text("❌ Отменено", reply_markup=get_main_menu())
    elif data == "task_1_screenshot":
        update_user(db, user.id, user.username, waiting_screenshot=1, current_task=1, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        await q.edit_message_text("📸 ОТПРАВЬ СКРИНШОТ СБЕРПРАЙМА")
    elif data == "task_2_screenshot":
        udata = get_user(db, user.id)
        if udata and udata[1] == 1:
            update_user(db, user.id, user.username, waiting_screenshot=1, current_task=2, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            await q.edit_message_text("📸 ОТПРАВЬ СКРИНШОТ ОПРОСА")
        else:
            await q.answer("Сначала задание 1!", show_alert=True)
    elif data == "claim_reward":
        udata = get_user(db, user.id)
        if udata and udata[1] == 1 and udata[2] == 1:
            update_user(db, user.id, user.username, step=3)
            await q.edit_message_text("🎁 ОТПРАВЬ СВОЙ ID (пример: 2YU9R0P8C)")

async def photo_handler(update, context):
    user = update.effective_user
    db = context.bot_data['db']
    udata = get_user(db, user.id)
    if not udata or udata[4] != 1:
        await update.message.reply_text("❌ Сейчас не нужно")
        return
    current_task = udata[5]
    msg = await update.message.reply_text("⏳ ПРОВЕРКА...")
    await asyncio.sleep(3)
    await msg.delete()
    if current_task == 1:
        update_user(db, user.id, user.username, task1_done=1, waiting_screenshot=0, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        await update.message.reply_text("✅ ЗАДАНИЕ 1 ВЫПОЛНЕНО!\n\nЗадание 2/2:", reply_markup=get_task_keyboard(2, TASKS[1]['url'], TASKS[1]['button']))
    else:
        update_user(db, user.id, user.username, task2_done=1, waiting_screenshot=0, last_activity=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        await update.message.reply_text("✅ ЗАДАНИЕ 2 ВЫПОЛНЕНО!\n\nПолучи награду!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎁 ПОЛУЧИТЬ", callback_data="claim_reward")]]))

async def text_handler(update, context):
    user = update.effective_user
    db = context.bot_data['db']
    udata = get_user(db, user.id)
    if udata and udata[0] == 3:
        clean = update.message.text.strip().upper().replace('#', '')
        if is_player_id(clean):
            update_user(db, user.id, user.username, player_id=clean, step=4)
            await update.message.reply_text(f"✅ ID ПРИНЯТ: {clean}\n\n🎁 НАГРАДА В ТЕЧЕНИЕ 12 ЧАСОВ!")
        else:
            await update.message.reply_text("❌ НЕВЕРНЫЙ ID\nПример: 2YU9R0P8C")

async def run_bot(token, name, num):
    db = f'users_{num}.db'
    init_db(db)
    app = Application.builder().token(token).build()
    app.bot_data['db'] = db
    app.bot_data['name'] = name
    if app.job_queue:
        app.job_queue.run_repeating(check_reminders, interval=7200, first=10)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print(f"✅ {name} запущен")
    while True:
        await asyncio.sleep(1)

async def main():
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    print("🚀 ЗАПУСК 9 БОТОВ...")
    tasks = []
    for i, (token, name) in enumerate(zip(BOT_TOKENS, BOT_NAMES)):
        tasks.append(asyncio.create_task(run_bot(token, name, i+1)))
        await asyncio.sleep(2)
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())