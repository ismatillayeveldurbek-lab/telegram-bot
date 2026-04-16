import os
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

BOT_TOKEN = os.getenv("8760253406:AAFn7DlQEUhKF4LlcAvwI0mjK4Dp_DMdsTE")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======================
# DATABASE
# ======================
conn = sqlite3.connect("votes.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    voted INTEGER DEFAULT 0,
    script TEXT DEFAULT 'latin'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    teacher TEXT,
    count INTEGER DEFAULT 0
)
""")

conn.commit()

# ======================
# DATA
# ======================
teachers = [
    "Nurmatov Samandar",
    "F.Jabborov",
    "SH.Yusupova"
]

# ======================
# FUNKSIONAL
# ======================
def get_script(user_id):
    cursor.execute("SELECT script FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else "latin"

def set_script(user_id, script):
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    cursor.execute("UPDATE users SET script=? WHERE user_id=?", (script, user_id))
    conn.commit()

def has_voted(user_id):
    cursor.execute("SELECT voted FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row and row[0] == 1

def set_voted(user_id):
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    cursor.execute("UPDATE users SET voted=1 WHERE user_id=?", (user_id,))
    conn.commit()

def add_vote(teacher):
    cursor.execute("SELECT count FROM votes WHERE teacher=?", (teacher,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE votes SET count=count+1 WHERE teacher=?", (teacher,))
    else:
        cursor.execute("INSERT INTO votes VALUES(?,1)", (teacher,))
    conn.commit()

def get_results():
    cursor.execute("SELECT teacher, count FROM votes")
    return cursor.fetchall()

# ======================
# KEYBOARD
# ======================
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗳 Ovoz berish", callback_data="vote")],
        [InlineKeyboardButton(text="📊 Natijalar", callback_data="results")],
        [InlineKeyboardButton(text="🌐 Yozuv", callback_data="script")]
    ])

def script_kb(user_id):
    s = get_script(user_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=("✅ Lotin" if s=="latin" else "Lotin"), callback_data="set_latin"),
            InlineKeyboardButton(text=("✅ Kiril" if s=="cyrillic" else "Kiril"), callback_data="set_cyrillic"),
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back")]
    ])

def teachers_kb():
    kb = []
    for t in teachers:
        kb.append([InlineKeyboardButton(text=t, callback_data=f"t:{t}")])
    kb.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ======================
# START
# ======================
@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer("Bosh menyu", reply_markup=main_kb())

# ======================
# CALLBACKS
# ======================
@dp.callback_query(F.data == "back")
async def back(cb: CallbackQuery):
    await cb.message.edit_text("Bosh menyu", reply_markup=main_kb())

@dp.callback_query(F.data == "script")
async def script(cb: CallbackQuery):
    await cb.message.edit_text("Yozuv tanlang", reply_markup=script_kb(cb.from_user.id))

@dp.callback_query(F.data == "set_latin")
async def set_latin(cb: CallbackQuery):
    set_script(cb.from_user.id, "latin")
    await cb.message.edit_text("Lotin tanlandi", reply_markup=script_kb(cb.from_user.id))

@dp.callback_query(F.data == "set_cyrillic")
async def set_cyrillic(cb: CallbackQuery):
    set_script(cb.from_user.id, "cyrillic")
    await cb.message.edit_text("Kiril tanlandi", reply_markup=script_kb(cb.from_user.id))

@dp.callback_query(F.data == "vote")
async def vote(cb: CallbackQuery):
    if has_voted(cb.from_user.id):
        await cb.answer("Siz ovoz bergansiz", show_alert=True)
        return
    await cb.message.edit_text("O‘qituvchini tanlang", reply_markup=teachers_kb())

@dp.callback_query(F.data.startswith("t:"))
async def vote_teacher(cb: CallbackQuery):
    teacher = cb.data.split(":")[1]

    if has_voted(cb.from_user.id):
        await cb.answer("Siz ovoz bergansiz", show_alert=True)
        return

    add_vote(teacher)
    set_voted(cb.from_user.id)

    await cb.message.edit_text("Ovoz qabul qilindi", reply_markup=main_kb())

@dp.callback_query(F.data == "results")
async def results(cb: CallbackQuery):
    data = get_results()

    text = "Natijalar:\n\n"
    for t, c in data:
        text += f"{t} — {c}\n"

    await cb.message.edit_text(text, reply_markup=main_kb())

# ======================
# MAIN
# ======================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
