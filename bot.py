import os
import csv
import asyncio
import logging
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# =========================
# SOZLAMALAR
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8760253406:AAFn7DlQEUhKF4LlcAvwI0mjK4Dp_DMdsTE") 
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@botuchun10") 
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "5298063089")
ADMIN_IDS = [
    int(x.strip()) for x in ADMIN_IDS_RAW.split(",")
    if x.strip().isdigit()
]

FACEBOOK_URL = "https://www.facebook.com/share/1App2cfB8c/"
INSTAGRAM_URL = "https://www.instagram.com/pedagogikmahorat"

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, "votes.db")
EXPORT_FILE = os.path.join(DATA_DIR, "votes_export.csv")

SUBJECTS = {
    "ingliz_tili": {
        "name": "🇬🇧 Ingliz tili",
        "teachers": {
            "ingliz_1": "Yo'ldoshev Bekmirza",
            "ingliz_2": "Meyliyeva Lobar",
            "ingliz_3": "Nazarov Asliddin",
            "ingliz_4": "Norov O",
            "ingliz_5": "Oqboyeva Z",
            "ingliz_6": "Azimova N",
            "ingliz_7": "Abduxoliqov A",
            "ingliz_8": "D.Shaniyazova",
            "ingliz_9": "B.Mamatov",
        },
    },
    "ona_tili": {
        "name": "📖 Ona tili",
        "teachers": {
            "ona_1": "Irisova Sayyora",
            "ona_2": "D.Shaniyazova",
            "ona_3": "Meyliyeva Lobar",
            "ona_4": "Nazarov Asliddin",
            "ona_5": "Norov O",
            "ona_6": "Abadov D",
            "ona_7": "Xidirova F",
            "ona_8": "Jalilova K",
            "ona_9": "B.Mamatov",
        },
    },
    "rus_tili": {
        "name": "🇷🇺 Rus tili",
        "teachers": {
            "rus_1": "Batashov Inatilla",
            "rus_2": "B.Mamatov",
            "rus_3": "D.Shaniyazova",
            "rus_4": "H.Yaratov",
            "rus_5": "Meyliyeva Lobar",
            "rus_6": "Norov O",
            "rus_7": "Ergasheva D",
            "rus_8": "Sevastyanova N",
        },
    },
    "matematika": {
        "name": "➗ Matematika",
        "teachers": {
            "mat_1": "Nurmatov Samandar",
            "mat_2": "F.Jabborov",
            "mat_3": "SH.Yusupova",
            "mat_4": "Qo'ldosheva M",
            "mat_5": "Umarov I",
            "mat_6": "D.Bekmuradova",
            "mat_7": "O.Ochilov",
            "mat_8": "Nazarov Asliddin",
        },
    },
    "informatika": {
        "name": "💻 Informatika",
        "teachers": {
            "info_1": "Nurmatov Samandar",
            "info_2": "F.Jabborov",
            "info_3": "B.Mamatov",
            "info_4": "SH.Eshmurodov",
            "info_5": "Z.Suyarov",
            "info_6": "H.Mallayev",
            "info_7": "D.Bekmuradova",
            "info_8": "O.Ochilov",
            "info_9": "Meyliyeva Lobar",
        },
    },
    "boshlangich_fanlar": {
        "name": "🧒 Boshlang'ich fanlar",
        "teachers": {
            "bosh_1": "Shamsiyev J",
            "bosh_2": "Z.Suyarov",
            "bosh_3": "Umarov Lutfillo",
            "bosh_4": "N.Baratova",
            "bosh_5": "O.Ochilov",
            "bosh_6": "Irisova Sayyora",
            "bosh_7": "Zaripova Muslima",
            "bosh_8": "Azizova Dilnoz",
            "bosh_9": "Rajabova Xurshida",
            "bosh_10": "G'oyemov U",
            "bosh_11": "Qosimova G",
            "bosh_12": "Qarshiyeva G",
            "bosh_13": "Qurbonova H",
        },
    },
}

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# =========================
# BAZA
# =========================
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
    conn.commit()

    cursor.execute("PRAGMA table_info(votes)")
    columns = [row[1] for row in cursor.fetchall()]

    if "subject_key" not in columns:
        cursor.execute("ALTER TABLE votes ADD COLUMN subject_key TEXT")
        conn.commit()

    if "voted_at" not in columns:
        cursor.execute("ALTER TABLE votes ADD COLUMN voted_at TEXT")
        conn.commit()

    if get_setting("voting_open", "") == "":
        set_setting("voting_open", "1")


# =========================
# YORDAMCHI
# =========================
def get_setting(key: str, default: str = "") -> str:
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else default


def set_setting(key: str, value: str):
    cursor.execute("""
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def is_voting_open() -> bool:
    return get_setting("voting_open", "1") == "1"


def open_voting():
    set_setting("voting_open", "1")


def close_voting():
    set_setting("voting_open", "0")


def has_voted(user_id: int) -> bool:
    cursor.execute("SELECT 1 FROM votes WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None


def save_vote(user_id: int, full_name: str, username: str, subject_key: str, teacher_key: str):
    cursor.execute("""
        INSERT INTO votes (user_id, full_name, username, subject_key, teacher_key, voted_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        full_name,
        username,
        subject_key,
        teacher_key,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
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
    result = []
    for subject_key, subject_data in SUBJECTS.items():
        for teacher_key, teacher_name in subject_data["teachers"].items():
            result.append((subject_key, teacher_key, teacher_name))
    return result


def get_general_results_text() -> str:
    total_votes = get_total_votes()
    lines = ["📊 <b>Umumiy natijalar</b>\n"]

    for subject_key, teacher_key, teacher_name in get_all_teachers_flat():
        cursor.execute("""
            SELECT COUNT(*)
            FROM votes
            WHERE subject_key = ? AND teacher_key = ?
        """, (subject_key, teacher_key))
        count = cursor.fetchone()[0]
        percent = (count / total_votes * 100) if total_votes > 0 else 0
        bar = build_progress_bar(percent)

        lines.append(
            f"<b>{teacher_name}</b> — {get_subject_name(subject_key)}\n"
            f"<code>{bar}</code>  <b>{percent:.1f}%</b>  •  {count} ta\n"
        )

    lines.append(f"🗳 <b>Jami ovozlar:</b> {total_votes}")
    lines.append(f"{'🟢' if is_voting_open() else '🔴'} <b>Holat:</b> {'Ochiq' if is_voting_open() else 'Yopiq'}")

    text = "\n".join(lines)
    return text[:4000] + "\n\n... qisqartirildi" if len(text) > 4000 else text


def get_subject_results_text(subject_key: str) -> str:
    total_votes = get_total_votes()

    if subject_key not in SUBJECTS:
        return "Noto‘g‘ri fan."

    lines = [f"📊 <b>{get_subject_name(subject_key)} bo‘yicha natijalar</b>\n"]

    for teacher_key, teacher_name in SUBJECTS[subject_key]["teachers"].items():
        cursor.execute("""
            SELECT COUNT(*)
            FROM votes
            WHERE subject_key = ? AND teacher_key = ?
        """, (subject_key, teacher_key))
        count = cursor.fetchone()[0]
        percent = (count / total_votes * 100) if total_votes > 0 else 0
        bar = build_progress_bar(percent)

        lines.append(
            f"<b>{teacher_name}</b>\n"
            f"<code>{bar}</code>  <b>{percent:.1f}%</b>  •  {count} ta\n"
        )

    lines.append(f"🗳 <b>Jami ovozlar:</b> {total_votes}")
    lines.append(f"{'🟢' if is_voting_open() else '🔴'} <b>Holat:</b> {'Ochiq' if is_voting_open() else 'Yopiq'}")

    text = "\n".join(lines)
    return text[:4000] + "\n\n... qisqartirildi" if len(text) > 4000 else text


def get_users_text() -> str:
    cursor.execute("""
        SELECT user_id, full_name, username, subject_key, teacher_key, voted_at
        FROM votes
        ORDER BY voted_at DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        return "👥 Hali hech kim ovoz bermagan."

    lines = [f"👥 <b>Kim kimga ovoz berdi</b>\n\nJami: {len(rows)} ta foydalanuvchi\n"]

    for i, (user_id, full_name, username, subject_key, teacher_key, voted_at) in enumerate(rows, start=1):
        line = f"{i}. <b>{full_name or 'Noma’lum'}</b>"
        if username:
            line += f" (@{username})"
        line += f"\n   → Fan: {get_subject_name(subject_key)}"
        line += f"\n   → O‘qituvchi: {get_teacher_name(subject_key, teacher_key)}"
        line += f"\n   → ID: <code>{user_id}</code>"
        if voted_at:
            line += f"\n   → {voted_at}"
        lines.append(line)

    text = "\n\n".join(lines)
    return text[:4000] + "\n\n... qisqartirildi" if len(text) > 4000 else text


def export_votes_to_csv() -> str:
    cursor.execute("""
        SELECT user_id, full_name, username, subject_key, teacher_key, voted_at
        FROM votes
        ORDER BY voted_at DESC
    """)
    rows = cursor.fetchall()

    with open(EXPORT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["User ID", "Full Name", "Username", "Subject", "Teacher", "Voted At"])

        for user_id, full_name, username, subject_key, teacher_key, voted_at in rows:
            writer.writerow([
                user_id,
                full_name or "",
                username or "",
                get_subject_name(subject_key),
                get_teacher_name(subject_key, teacher_key),
                voted_at or ""
            ])

    return EXPORT_FILE


async def check_user_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in {
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        }
    except Exception as e:
        logging.error(f"Obunani tekshirishda xatolik: {e}")
        return False


async def safe_edit_message(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None
):
    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    except TelegramBadRequest as e:
        error_text = str(e).lower()

        if "message is not modified" in error_text:
            return

        if "there is no text in the message to edit" in error_text:
            return

        try:
            await callback.message.answer(
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        except Exception:
            return
    except Exception:
        return


# =========================
# KLAVIATURALAR
# =========================
def subscription_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(
            text="📢 Telegram kanal",
            url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
        )
    )
    kb.row(
        InlineKeyboardButton(
            text="📘 Facebook sahifa",
            url=FACEBOOK_URL
        )
    )
    kb.row(
        InlineKeyboardButton(
            text="📸 Instagram sahifa",
            url=INSTAGRAM_URL
        )
    )
    kb.row(
        InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription"),
        InlineKeyboardButton(text="📊 Natijalar", callback_data="show_results_menu_user")
    )

    return kb.as_markup()


def home_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🗳 Ovoz berish", callback_data="go_vote_panel"),
        InlineKeyboardButton(text="📊 Natijalar", callback_data="show_results_menu_user")
    )
    kb.row(
        InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help_info")
    )
    return kb.as_markup()


def subjects_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for subject_key, subject_data in SUBJECTS.items():
        kb.row(
            InlineKeyboardButton(
                text=subject_data["name"],
                callback_data=f"subject:{subject_key}"
            )
        )
    kb.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_home"))
    return kb.as_markup()


def teachers_keyboard(subject_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    teachers = list(SUBJECTS[subject_key]["teachers"].items())

    for i in range(0, len(teachers), 2):
        row = []
        for teacher_key, teacher_name in teachers[i:i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=teacher_name,
                    callback_data=f"vote:{subject_key}:{teacher_key}"
                )
            )
        kb.row(*row)

    kb.row(InlineKeyboardButton(text="⬅️ Fanlarga qaytish", callback_data="go_vote_panel"))
    kb.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_home"))
    return kb.as_markup()


def results_menu_keyboard_user() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📊 Umumiy", callback_data="show_results_user:general"))
    for subject_key, subject_data in SUBJECTS.items():
        kb.row(
            InlineKeyboardButton(
                text=subject_data["name"],
                callback_data=f"show_results_user:{subject_key}"
            )
        )
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="go_home"))
    return kb.as_markup()


def results_menu_keyboard_admin() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📊 Umumiy", callback_data="show_results_admin:general"))
    for subject_key, subject_data in SUBJECTS.items():
        kb.row(
            InlineKeyboardButton(
                text=subject_data["name"],
                callback_data=f"show_results_admin:{subject_key}"
            )
        )
    kb.row(InlineKeyboardButton(text="⬅️ Admin panel", callback_data="back_admin_panel"))
    return kb.as_markup()


def results_keyboard_user(scope: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"refresh_results_user:{scope}"),
        InlineKeyboardButton(text="📂 Bo‘limlar", callback_data="show_results_menu_user")
    )
    kb.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_home"))
    return kb.as_markup()


def results_keyboard_admin(scope: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"refresh_results_admin:{scope}"),
        InlineKeyboardButton(text="📂 Bo‘limlar", callback_data="admin_results")
    )
    kb.row(InlineKeyboardButton(text="⬅️ Admin panel", callback_data="back_admin_panel"))
    return kb.as_markup()


def after_vote_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="📊 Natijalar", callback_data="show_results_menu_user"),
        InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_home")
    )
    return kb.as_markup()


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="📊 Results", callback_data="admin_results"),
        InlineKeyboardButton(text="👥 Users", callback_data="admin_users")
    )
    kb.row(
        InlineKeyboardButton(text="📁 Export", callback_data="admin_export"),
        InlineKeyboardButton(text="♻ Reset", callback_data="admin_reset_confirm")
    )
    kb.row(
        InlineKeyboardButton(text="🔓 Open", callback_data="admin_open"),
        InlineKeyboardButton(text="🔒 Close", callback_data="admin_close")
    )
    return kb.as_markup()


def reset_confirm_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_reset"),
        InlineKeyboardButton(text="✅ Ha, o‘chirish", callback_data="admin_reset")
    )
    kb.row(InlineKeyboardButton(text="⬅️ Admin panel", callback_data="back_admin_panel"))
    return kb.as_markup()


def users_keyboard_admin() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_admin_users"),
        InlineKeyboardButton(text="⬅️ Admin panel", callback_data="back_admin_panel")
    )
    return kb.as_markup()


# =========================
# MATNLAR
# =========================
def get_welcome_text() -> str:
    return (
        "🚀 <b>Botdan foydalanish uchun quyidagilarni bajaring:</b>\n\n"
        "1️⃣ 📢 Telegram kanalga obuna bo‘ling\n"
        "2️⃣ 📘 Facebook sahifani kuzating\n"
        "3️⃣ 📸 Instagram sahifani kuzating\n\n"
        "👇 Barchasini bajargach, <b>Tekshirish</b> tugmasini bosing"
    )


def get_home_text() -> str:
    return "🏠 <b>Bosh menyu</b>\n\nKerakli bo‘limni tanlang:"


def get_help_text() -> str:
    return (
        "ℹ️ <b>Yordam</b>\n\n"
        "• Avval Telegram kanalga obuna bo‘ling\n"
        "• Facebook va Instagram sahifalarga ham o‘ting\n"
        "• Ovoz berish uchun fan tanlanadi\n"
        "• Keyin o‘qituvchi tanlanadi\n"
        "• Har bir foydalanuvchi faqat 1 marta ovoz bera oladi\n"
        "• Natijalarni istalgan payt ko‘rishingiz mumkin"
    )


def get_already_voted_text() -> str:
    return (
        "✅ <b>Siz allaqachon ovoz berib bo‘lgansiz</b>\n\n"
        "Qayta ovoz berish mumkin emas.\n"
        "📊 Natijalarni ko‘rishingiz mumkin."
    )


def get_closed_text() -> str:
    return (
        "🔒 <b>Ovoz berish hozircha yopilgan</b>\n\n"
        "Admin tomonidan ovoz berish vaqtincha to‘xtatilgan."
    )


def get_subject_select_text() -> str:
    return "🗂 <b>Fanni tanlang</b>\n\nQuyidagi fanlardan birini tanlang:"


def get_teacher_select_text(subject_key: str) -> str:
    return f"{SUBJECTS[subject_key]['name']}\n\n<b>O‘qituvchini tanlang:</b>"


def get_results_menu_text(is_admin_view: bool = False) -> str:
    title = "Admin natijalar bo‘limi" if is_admin_view else "Natijalar bo‘limi"
    return (
        f"📊 <b>{title}</b>\n\n"
        f"Kerakli bo‘limni tanlang:\n"
        f"• Umumiy natijalar\n"
        f"• Fanlar bo‘yicha natijalar"
    )


def get_admin_panel_text() -> str:
    status_text = "🟢 Ochiq" if is_voting_open() else "🔴 Yopiq"
    return (
        f"🎛 <b>Admin panel</b>\n\n"
        f"Voting holati: {status_text}\n"
        f"Jami ovozlar: {get_total_votes()}"
    )


# =========================
# START
# =========================
@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id

    if not await check_user_subscription(user_id):
        await message.answer(
            get_welcome_text(),
            parse_mode="HTML",
            reply_markup=subscription_keyboard()
        )
        return

    await message.answer(
        get_home_text(),
        parse_mode="HTML",
        reply_markup=home_keyboard()
    )


# =========================
# USER CALLBACKLAR
# =========================
@dp.callback_query(F.data == "go_home")
async def go_home_handler(callback: CallbackQuery):
    await safe_edit_message(callback, get_home_text(), home_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "help_info")
async def help_info_handler(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="go_home"))
    await safe_edit_message(callback, get_help_text(), kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "go_vote_panel")
async def go_vote_panel_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await check_user_subscription(user_id):
        await safe_edit_message(callback, get_welcome_text(), subscription_keyboard())
        await callback.answer()
        return

    if has_voted(user_id):
        await safe_edit_message(callback, get_already_voted_text(), home_keyboard())
        await callback.answer()
        return

    if not is_voting_open():
        await safe_edit_message(callback, get_closed_text(), home_keyboard())
        await callback.answer()
        return

    await safe_edit_message(callback, get_subject_select_text(), subjects_keyboard())
    await callback.answer()


@dp.callback_query(F.data.startswith("subject:"))
async def subject_select_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await check_user_subscription(user_id):
        await safe_edit_message(callback, get_welcome_text(), subscription_keyboard())
        await callback.answer()
        return

    if has_voted(user_id):
        await safe_edit_message(callback, get_already_voted_text(), home_keyboard())
        await callback.answer()
        return

    if not is_voting_open():
        await safe_edit_message(callback, get_closed_text(), home_keyboard())
        await callback.answer()
        return

    subject_key = callback.data.split(":")[1]

    if subject_key not in SUBJECTS:
        await callback.answer("Noto‘g‘ri fan tanlandi.", show_alert=True)
        return

    await safe_edit_message(
        callback,
        get_teacher_select_text(subject_key),
        teachers_keyboard(subject_key)
    )
    await callback.answer()


@dp.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await check_user_subscription(user_id):
        await callback.answer("Avval Telegram kanalga obuna bo‘ling.", show_alert=True)
        return

    await safe_edit_message(
        callback,
        "✅ <b>Tekshiruv muvaffaqiyatli o‘tdi</b>\n\nEndi bosh menyudan kerakli bo‘limni tanlang:",
        home_keyboard()
    )
    await callback.answer("Tasdiqlandi")


@dp.callback_query(F.data.startswith("vote:"))
async def vote_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await check_user_subscription(user_id):
        await callback.answer("Avval Telegram kanalga obuna bo‘ling.", show_alert=True)
        return

    if not is_voting_open():
        await callback.answer("Hozir ovoz berish yopilgan.", show_alert=True)
        return

    if has_voted(user_id):
        await callback.answer("Siz faqat 1 marta ovoz bera olasiz.", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Noto‘g‘ri tanlov.", show_alert=True)
        return

    _, subject_key, teacher_key = parts

    if subject_key not in SUBJECTS:
        await callback.answer("Noto‘g‘ri fan.", show_alert=True)
        return

    if teacher_key not in SUBJECTS[subject_key]["teachers"]:
        await callback.answer("Noto‘g‘ri o‘qituvchi.", show_alert=True)
        return

    save_vote(
        user_id=user_id,
        full_name=callback.from_user.full_name or "Noma’lum",
        username=callback.from_user.username or "",
        subject_key=subject_key,
        teacher_key=teacher_key,
    )

    await safe_edit_message(
        callback,
        f"✅ <b>Ovoz muvaffaqiyatli qabul qilindi</b>\n\n"
        f"<b>Fan:</b> {SUBJECTS[subject_key]['name']}\n"
        f"<b>Tanlovingiz:</b> {SUBJECTS[subject_key]['teachers'][teacher_key]}\n\n"
        f"Rahmat, sizning ovozingiz saqlandi.",
        after_vote_keyboard()
    )
    await callback.answer("Ovozingiz qabul qilindi!")


# =========================
# RESULTS - USER
# =========================
@dp.callback_query(F.data == "show_results_menu_user")
async def show_results_menu_user(callback: CallbackQuery):
    await safe_edit_message(
        callback,
        get_results_menu_text(False),
        results_menu_keyboard_user()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("show_results_user:"))
async def show_results_user(callback: CallbackQuery):
    scope = callback.data.split(":", 1)[1]
    text = get_general_results_text() if scope == "general" else get_subject_results_text(scope)
    await safe_edit_message(callback, text, results_keyboard_user(scope))
    await callback.answer()


@dp.callback_query(F.data.startswith("refresh_results_user:"))
async def refresh_results_user(callback: CallbackQuery):
    scope = callback.data.split(":", 1)[1]
    text = get_general_results_text() if scope == "general" else get_subject_results_text(scope)
    await safe_edit_message(callback, text, results_keyboard_user(scope))
    await callback.answer("Yangilandi")


@dp.message(Command("results"))
async def results_handler(message: Message):
    await message.answer(
        get_results_menu_text(False),
        parse_mode="HTML",
        reply_markup=results_menu_keyboard_user()
    )


# =========================
# ADMIN BUYRUQLAR
# =========================
@dp.message(Command("admin"))
async def admin_panel_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    await message.answer(
        get_admin_panel_text(),
        parse_mode="HTML",
        reply_markup=admin_panel_keyboard()
    )


@dp.message(Command("users"))
async def admin_users_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    await message.answer(
        get_users_text(),
        parse_mode="HTML",
        reply_markup=users_keyboard_admin()
    )


@dp.message(Command("export"))
async def admin_export_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    filename = export_votes_to_csv()
    await message.answer_document(
        FSInputFile(filename),
        caption="📁 Ovozlar CSV fayl ko‘rinishida."
    )


@dp.message(Command("open"))
async def admin_open_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    open_voting()
    await message.answer("🟢 Ovoz berish ochildi.")


@dp.message(Command("close"))
async def admin_close_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    close_voting()
    await message.answer("🔴 Ovoz berish yopildi.")


@dp.message(Command("reset_votes"))
async def admin_reset_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    await message.answer(
        "⚠️ <b>Diqqat!</b>\n\nBarcha ovozlar o‘chiriladi.\nDavom etasizmi?",
        parse_mode="HTML",
        reply_markup=reset_confirm_keyboard()
    )


# =========================
# ADMIN CALLBACKLAR
# =========================
@dp.callback_query(F.data == "back_admin_panel")
async def back_admin_panel_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    await safe_edit_message(callback, get_admin_panel_text(), admin_panel_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "admin_results")
async def admin_results_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    await safe_edit_message(
        callback,
        get_results_menu_text(True),
        results_menu_keyboard_admin()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("show_results_admin:"))
async def show_results_admin(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    scope = callback.data.split(":", 1)[1]
    text = get_general_results_text() if scope == "general" else get_subject_results_text(scope)
    await safe_edit_message(callback, text, results_keyboard_admin(scope))
    await callback.answer()


@dp.callback_query(F.data.startswith("refresh_results_admin:"))
async def refresh_results_admin_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    scope = callback.data.split(":", 1)[1]
    text = get_general_results_text() if scope == "general" else get_subject_results_text(scope)
    await safe_edit_message(callback, text, results_keyboard_admin(scope))
    await callback.answer("Yangilandi")


@dp.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    await safe_edit_message(callback, get_users_text(), users_keyboard_admin())
    await callback.answer()


@dp.callback_query(F.data == "refresh_admin_users")
async def refresh_admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    await safe_edit_message(callback, get_users_text(), users_keyboard_admin())
    await callback.answer("Yangilandi")


@dp.callback_query(F.data == "admin_export")
async def admin_export_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    filename = export_votes_to_csv()
    await callback.message.answer_document(
        FSInputFile(filename),
        caption="📁 Ovozlar CSV fayl ko‘rinishida."
    )
    await callback.answer()


@dp.callback_query(F.data == "admin_open")
async def admin_open_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    open_voting()
    await safe_edit_message(callback, get_admin_panel_text(), admin_panel_keyboard())
    await callback.answer("Voting ochildi!")


@dp.callback_query(F.data == "admin_close")
async def admin_close_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    close_voting()
    await safe_edit_message(callback, get_admin_panel_text(), admin_panel_keyboard())
    await callback.answer("Voting yopildi!")


@dp.callback_query(F.data == "admin_reset_confirm")
async def admin_reset_confirm_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    await safe_edit_message(
        callback,
        "⚠️ <b>Diqqat!</b>\n\nBarcha ovozlar o‘chiriladi.\nDavom etasizmi?",
        reset_confirm_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "cancel_reset")
async def cancel_reset_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    await safe_edit_message(callback, get_admin_panel_text(), admin_panel_keyboard())
    await callback.answer("Bekor qilindi")


@dp.callback_query(F.data == "admin_reset")
async def admin_reset_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    reset_votes()
    await safe_edit_message(callback, get_admin_panel_text(), admin_panel_keyboard())
    await callback.answer("Reset qilindi!")


# =========================
# TEXT HANDLER
# =========================
@dp.message(F.text.lower() == "results")
async def text_results_handler(message: Message):
    await message.answer(
        get_results_menu_text(False),
        parse_mode="HTML",
        reply_markup=results_menu_keyboard_user()
    )


# =========================
# MAIN
# =========================
async def main():
    init_db()
    logging.info(f"Bot ishga tushdi. Baza: {DB_NAME}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
