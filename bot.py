import os
import csv
import re
import asyncio
import logging
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
    FSInputFile,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# =========================
# SOZLAMALAR
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8760253406:AAFn7DlQEUhKF4LlcAvwI0mjK4Dp_DMdsTE")
CHANNEL_USERNAME = "@QASHQADARYOPMMrasmiy"

ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "5298063089,7361393654")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]

FACEBOOK_URL = "https://www.facebook.com/share/1E4ZVePTh4/"
INSTAGRAM_URL = "https://www.instagram.com/pedagogikmahorat"

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, "votes.db")
EXPORT_FILE = os.path.join(DATA_DIR, "votes_export.csv")

SUBJECTS = {
    "tillarni_oqitish_metodikasi": {
        "name": "Tillarni o‘qitish metodikasi",
        "teachers": {
            "tom_1": "Norov Otajon Shomurodovich",
            "tom_2": "Abdixolikov Abdulazizxon Abduvohob o‘g‘li",
            "tom_3": "Azimova Nigora Anvar qizi",
            "tom_4": "Abatov Doston Ro‘zimurod o‘g‘li",
            "tom_5": "Jalilova Komila Abdullayevna",
            "tom_6": "Oqboyeva Zulfiya Bobonazarovna",
            "tom_7": "Sevastyanova Nadejda Aleksandrovna",
            "tom_8": "Xidirova Feruza To‘rayevna",
            "tom_9": "Ergasheva Dilorom Muradilloyevna",
        },
    },
    "pedagogika_psixologiya_va_talim_menejmenti": {
        "name": "Pedagogika, psixologiya va ta’lim menejmenti",
        "teachers": {
            "pptm_1": "Umarov Lutfillo Murodilloyevich",
            "pptm_2": "Baratova Nasiba Turobovna",
            "pptm_3": "Bekmurodova Dilnoza Pirimovna",
            "pptm_4": "Meyliyev Jobar Nurmatovna",
            "pptm_5": "Ochilov Og‘abek Narzullayevich",
            "pptm_6": "Shoniyozova Dilafruz Sabirovna",
            "pptm_7": "Yaratov Xamidjon Muxtorovich",
            "pptm_8": "Nazarov Asliddin Faxriddin o‘g‘li",
            "pptm_9": "Ergasheva Dilafruz Ergamqulovna",
            "pptm_10": "Soatov Asadulloh Jabborovich",
        },
    },
    "aniq_va_tabiiy_fanlar": {
        "name": "Aniq va tabiiy fanlar",
        "teachers": {
            "atf_1": "Jobborov Farhod Bo‘rinevich",
            "atf_2": "Karimova Habiba Abduraxmonovna",
            "atf_3": "Quldoshova Maftuna Jumanzar qizi",
            "atf_4": "Mallaev Xamro Ro‘ziboyevich",
            "atf_5": "Mamatov Bekzod Farxotovich",
            "atf_6": "Pardaeva Muqaddas Zafar qizi",
            "atf_7": "Parmanov Jahongir Rayhonovich",
            "atf_8": "Rahmatullayev Erkin Shokirovich",
            "atf_9": "Suyarov Zoir Shojmardonovich",
            "atf_10": "Tursunova Maftuna Sulton qizi",
            "atf_11": "Umarov Ibrohimxon Norxuja o‘g‘li",
            "atf_12": "Chariev Rashid Ravshanovich",
            "atf_13": "Elmurodov Sherdil Ergashyevich",
            "atf_14": "Eshmonov Laziz Norxo‘rja o‘g‘li",
            "atf_15": "Karaeva Dilfuzaxon Mamasharipovna",
            "atf_16": "Salomova Madina Sodiq qizi",
        },
    },
    "amaliy_va_ijtimoiy_fanlar": {
        "name": "Amaliy va ijtimoiy fanlar",
        "teachers": {
            "aif_1": "Yo‘ldashev Bekmirza Elmurodovich",
            "aif_2": "Jabboborov Laziz Hamza o‘g‘li",
            "aif_3": "Nurmatov Samandar Fayratovich",
            "aif_4": "Batoshov Inatillo Kungirovich",
            "aif_5": "Rajabov Ruslan Bozorovich",
            "aif_6": "Sanaev Azamat Alponovich",
            "aif_7": "Shamsiev Jahongir Qulmurod o‘g‘li",
            "aif_8": "Xudoyberdiev Axrorboy Nabi o‘g‘li",
            "aif_9": "Xasanova Gulnora Qorshanbiyevna",
            "aif_10": "Eshnazarova Maziya Allanazarovna",
        },
    },
    "maktabgacha_boshlangich_va_maxsus_talim": {
        "name": "Maktabgacha, boshlang‘ich va maxsus ta’lim",
        "teachers": {
            "mbmt_1": "Irisova Sayyora Rajabovna",
            "mbmt_2": "Azizova Dilnoz Yo‘ldoshevna",
            "mbmt_3": "G‘oyimov Umar Eshmurodovich",
            "mbmt_4": "Ziyoyeva Madina Mansur qizi",
            "mbmt_5": "Karimova Umida Sharopovna",
            "mbmt_6": "Qorliyeva Guzal Alimardonovna",
            "mbmt_7": "Qurbanova Xusnora Xudoyberdi qizi",
            "mbmt_8": "Rajabova Xurshida Hakimovna",
            "mbmt_9": "Razzaqova Dilnoza Akramovna",
            "mbmt_10": "Sadinova Marjona Akmal qizi",
            "mbmt_11": "Shaxmurodova Dilxaxon Almardanovna",
            "mbmt_12": "Ergasheva Xusniya Mirzoxid qizi",
            "mbmt_13": "Zaripova Muslima Qurbonovna",
        },
    },
}

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            subject_key TEXT NOT NULL,
            teacher_key TEXT NOT NULL,
            voted_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_prefs (
            user_id INTEGER PRIMARY KEY,
            script TEXT DEFAULT 'latin',
            access_granted INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    if get_setting("voting_open", "") == "":
        set_setting("voting_open", "1")

init_db()

# =========================
# DB FUNCTIONS (to'liq)
# =========================
def get_setting(key: str, default: str = "") -> str:
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else default

def set_setting(key: str, value: str):
    cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
    conn.commit()

def ensure_user(user_id: int):
    cursor.execute("INSERT INTO user_prefs (user_id, script, access_granted) VALUES (?, 'latin', 0) ON CONFLICT(user_id) DO NOTHING", (user_id,))
    conn.commit()

def get_user_script(user_id: int) -> str:
    ensure_user(user_id)
    cursor.execute("SELECT script FROM user_prefs WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else "latin"

def set_user_script(user_id: int, script: str):
    ensure_user(user_id)
    cursor.execute("UPDATE user_prefs SET script = ? WHERE user_id = ?", (script, user_id))
    conn.commit()

def has_access(user_id: int) -> bool:
    ensure_user(user_id)
    cursor.execute("SELECT access_granted FROM user_prefs WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return bool(row[0]) if row else False

def grant_access(user_id: int):
    ensure_user(user_id)
    cursor.execute("UPDATE user_prefs SET access_granted = 1 WHERE user_id = ?", (user_id,))
    conn.commit()

def reset_access(user_id: int):
    ensure_user(user_id)
    cursor.execute("UPDATE user_prefs SET access_granted = 0 WHERE user_id = ?", (user_id,))
    conn.commit()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def is_voting_open() -> bool:
    return get_setting("voting_open", "1") == "1"

def open_voting(): set_setting("voting_open", "1")
def close_voting(): set_setting("voting_open", "0")

def has_voted(user_id: int) -> bool:
    cursor.execute("SELECT 1 FROM votes WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def save_vote(user_id: int, full_name: str, username: str, subject_key: str, teacher_key: str):
    cursor.execute("INSERT INTO votes (user_id, full_name, username, subject_key, teacher_key, voted_at) VALUES (?, ?, ?, ?, ?, ?)",
                   (user_id, full_name, username, subject_key, teacher_key, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_total_votes() -> int:
    cursor.execute("SELECT COUNT(*) FROM votes")
    return cursor.fetchone()[0]

def reset_votes():
    cursor.execute("DELETE FROM votes")
    conn.commit()

def get_subject_name(subject_key: str) -> str:
    return SUBJECTS.get(subject_key, {}).get("name", subject_key)

def get_teacher_name(subject_key: str, teacher_key: str) -> str:
    return SUBJECTS.get(subject_key, {}).get("teachers", {}).get(teacher_key, teacher_key)

def build_progress_bar(percent: float, length: int = 14) -> str:
    filled = round((percent / 100) * length)
    filled = max(0, min(filled, length))
    empty = length - filled
    return "▓" * filled + "░" * empty

def get_all_teachers_flat():
    items = []
    for subject_key, subject_data in SUBJECTS.items():
        for teacher_key, teacher_name in subject_data["teachers"].items():
            items.append((subject_key, teacher_key, teacher_name))
    return items

def get_subscription_required_alert(user_id: int) -> str:
    return "Avval Telegram kanal, Instagram va Facebook sahifalarga obuna bo'ling."

def get_general_results_text(user_id: int) -> str:
    total_votes = get_total_votes()
    lines = ["📊 <b>Umumiy natijalar</b>\n"]
    for subject_key, teacher_key, teacher_name in get_all_teachers_flat():
        cursor.execute("SELECT COUNT(*) FROM votes WHERE subject_key = ? AND teacher_key = ?", (subject_key, teacher_key))
        count = cursor.fetchone()[0]
        percent = (count / total_votes * 100) if total_votes > 0 else 0
        bar = build_progress_bar(percent)
        lines.append(f"<b>{teacher_name}</b> — {get_subject_name(subject_key)}\n<code>{bar}</code>  <b>{percent:.1f}%</b>  •  {count} ta\n")
    lines.append(f"🗳 <b>Jami ovozlar:</b> {total_votes}")
    lines.append(f"{'🟢' if is_voting_open() else '🔴'} <b>Holat:</b> {'Ochiq' if is_voting_open() else 'Yopiq'}")
    text = "\n".join(lines)
    return text if len(text) <= 4000 else text[:4000] + "\n\n... qisqartirildi"

def get_subject_results_text(user_id: int, subject_key: str) -> str:
    if subject_key not in SUBJECTS: return "Noto'g'ri fan."
    total_votes = get_total_votes()
    lines = [f"📊 <b>{get_subject_name(subject_key)} bo'yicha natijalar</b>\n"]
    for teacher_key, teacher_name in SUBJECTS[subject_key]["teachers"].items():
        cursor.execute("SELECT COUNT(*) FROM votes WHERE subject_key = ? AND teacher_key = ?", (subject_key, teacher_key))
        count = cursor.fetchone()[0]
        percent = (count / total_votes * 100) if total_votes > 0 else 0
        bar = build_progress_bar(percent)
        lines.append(f"<b>{teacher_name}</b>\n<code>{bar}</code>  <b>{percent:.1f}%</b>  •  {count} ta\n")
    lines.append(f"🗳 <b>Jami ovozlar:</b> {total_votes}")
    lines.append(f"{'🟢' if is_voting_open() else '🔴'} <b>Holat:</b> {'Ochiq' if is_voting_open() else 'Yopiq'}")
    text = "\n".join(lines)
    return text if len(text) <= 4000 else text[:4000] + "\n\n... qisqartirildi"

def get_users_text(user_id: int) -> str:
    cursor.execute("SELECT user_id, full_name, username, subject_key, teacher_key, voted_at FROM votes ORDER BY voted_at DESC")
    rows = cursor.fetchall()
    if not rows: return "👥 Hali hech kim ovoz bermagan."
    lines = [f"👥 <b>Kim kimga ovoz berdi</b>\n\nJami: {len(rows)} ta foydalanuvchi\n"]
    for i, (uid, full_name, username, subject_key, teacher_key, voted_at) in enumerate(rows, start=1):
        safe_name = full_name or "Noma'lum"
        line = f"{i}. <b>{safe_name}</b>"
        if username: line += f" (@{username})"
        line += f"\n   → Fan: {get_subject_name(subject_key)}"
        line += f"\n   → O'qituvchi: {get_teacher_name(subject_key, teacher_key)}"
        line += f"\n   → ID: <code>{uid}</code>"
        if voted_at: line += f"\n   → {voted_at}"
        lines.append(line)
    text = "\n\n".join(lines)
    return text if len(text) <= 4000 else text[:4000] + "\n\n... qisqartirildi"

def export_votes_to_csv() -> str:
    cursor.execute("SELECT user_id, full_name, username, subject_key, teacher_key, voted_at FROM votes ORDER BY voted_at DESC")
    rows = cursor.fetchall()
    with open(EXPORT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["User ID", "Full Name", "Username", "Subject", "Teacher", "Voted At"])
        for user_id, full_name, username, subject_key, teacher_key, voted_at in rows:
            writer.writerow([user_id, full_name or "", username or "", get_subject_name(subject_key), get_teacher_name(subject_key, teacher_key), voted_at or ""])
    return EXPORT_FILE

async def check_user_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in {ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED}
    except:
        return False

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None):
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=reply_markup)
    except:
        pass

# =========================
# BOT PANELI (Pastdan chiqadigan tugmalar)
# =========================
def get_bot_panel():
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="🗳 Ovoz berish"))
    kb.row(KeyboardButton(text="📊 Natijalar"))
    kb.row(KeyboardButton(text="ℹ️ Yordam"))
    kb.row(KeyboardButton(text="🏠 Bosh menyu"))
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=False)

# =========================
# HANDLERLAR
# =========================
@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)
    await message.answer(
        "🚀 Xush kelibsiz!\n\n"
        "Botdan foydalanish uchun pastdagi tugmalardan foydalaning yoki quyidagi buyruqlarni bosing:\n"
        "• /start - Boshlash\n"
        "• /results - Natijalarni ko‘rish\n"
        "• /admin - Admin paneli",
        reply_markup=get_bot_panel()
    )

@dp.message(F.text == "🗳 Ovoz berish")
async def vote_button(message: Message):
    user_id = message.from_user.id
    if not has_access(user_id):
        await message.answer("Avval obunani tekshiring!", reply_markup=get_bot_panel())
        return
    if has_voted(user_id):
        await message.answer("Siz allaqachon ovoz bergansiz!", reply_markup=get_bot_panel())
        return
    await message.answer("Ovoz berish uchun kafedrani tanlang (tez orada to‘liq qo‘shiladi):", reply_markup=get_bot_panel())

@dp.message(F.text == "📊 Natijalar")
async def results_button(message: Message):
    await message.answer("📊 Natijalar tez orada qo‘shiladi...", reply_markup=get_bot_panel())

@dp.message(F.text == "ℹ️ Yordam")
async def help_button(message: Message):
    await message.answer(
        "ℹ️ Yordam:\n\n"
        "• Ovoz berish uchun '🗳 Ovoz berish' tugmasini bosing\n"
        "• Natijalarni ko‘rish uchun '📊 Natijalar' tugmasini bosing\n"
        "• Har bir foydalanuvchi faqat 1 marta ovoz bera oladi",
        reply_markup=get_bot_panel()
    )

@dp.message(F.text == "🏠 Bosh menyu")
async def home_button(message: Message):
    await message.answer("🏠 Bosh menyu", reply_markup=get_bot_panel())

@dp.message(Command("results"))
async def results_command(message: Message):
    await message.answer("📊 Natijalar tez orada qo‘shiladi...", reply_markup=get_bot_panel())

@dp.message(Command("admin"))
async def admin_command(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Siz admin emassiz!")
        return
    await message.answer("🎛 Admin paneli (tez orada to‘liq qo‘shiladi)", reply_markup=get_bot_panel())

async def main():
    logging.info("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
