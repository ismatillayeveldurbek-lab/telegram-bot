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
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@qashqadaryoPMM")

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

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# =========================
# TRANSLIT
# =========================
def latin_to_cyrillic_text(text: str) -> str:
    pairs = [
        ("O‘", "Ў"), ("o‘", "ў"),
        ("G‘", "Ғ"), ("g‘", "ғ"),
        ("O'", "Ў"), ("o'", "ў"),
        ("G'", "Ғ"), ("g'", "ғ"),
        ("Sh", "Ш"), ("sh", "ш"),
        ("Ch", "Ч"), ("ch", "ч"),
        ("Ya", "Я"), ("ya", "я"),
        ("Yo", "Ё"), ("yo", "ё"),
        ("Yu", "Ю"), ("yu", "ю"),
        ("Ts", "Ц"), ("ts", "ц"),
    ]
    for old, new in pairs:
        text = text.replace(old, new)

    table = str.maketrans({
        "A": "А", "a": "а",
        "B": "Б", "b": "б",
        "D": "Д", "d": "д",
        "E": "Е", "e": "е",
        "F": "Ф", "f": "ф",
        "G": "Г", "g": "г",
        "H": "Ҳ", "h": "ҳ",
        "I": "И", "i": "и",
        "J": "Ж", "j": "ж",
        "K": "К", "k": "к",
        "L": "Л", "l": "л",
        "M": "М", "m": "м",
        "N": "Н", "n": "н",
        "O": "О", "o": "о",
        "P": "П", "p": "п",
        "Q": "Қ", "q": "қ",
        "R": "Р", "r": "р",
        "S": "С", "s": "с",
        "T": "Т", "t": "т",
        "U": "У", "u": "у",
        "V": "В", "v": "в",
        "X": "Х", "x": "х",
        "Y": "Й", "y": "й",
        "Z": "З", "z": "з",
        "`": "ъ", "’": "ъ", "'": "ъ",
    })
    return text.translate(table)


def cyrillic_to_latin_text(text: str) -> str:
    pairs = [
        ("Ў", "O'"), ("ў", "o'"),
        ("Ғ", "G'"), ("ғ", "g'"),
        ("Ш", "Sh"), ("ш", "sh"),
        ("Ч", "Ch"), ("ч", "ch"),
        ("Я", "Ya"), ("я", "ya"),
        ("Ё", "Yo"), ("ё", "yo"),
        ("Ю", "Yu"), ("ю", "yu"),
        ("Ц", "Ts"), ("ц", "ts"),
    ]
    for old, new in pairs:
        text = text.replace(old, new)

    table = str.maketrans({
        "А": "A", "а": "a",
        "Б": "B", "б": "b",
        "Д": "D", "д": "d",
        "Е": "E", "е": "e",
        "Ф": "F", "ф": "f",
        "Г": "G", "г": "g",
        "Ҳ": "H", "ҳ": "h",
        "И": "I", "и": "i",
        "Ж": "J", "ж": "j",
        "К": "K", "к": "k",
        "Л": "L", "л": "l",
        "М": "M", "м": "m",
        "Н": "N", "н": "n",
        "О": "O", "о": "o",
        "П": "P", "п": "p",
        "Қ": "Q", "қ": "q",
        "Р": "R", "р": "r",
        "С": "S", "с": "s",
        "Т": "T", "т": "t",
        "У": "U", "у": "u",
        "В": "V", "в": "v",
        "Х": "X", "х": "x",
        "Й": "Y", "й": "y",
        "З": "Z", "з": "z",
        "Ъ": "'", "ъ": "'",
        "Ь": "", "ь": "",
    })
    return text.translate(table)


def translit_html_safe(text: str, script: str) -> str:
    parts = re.split(r"(<[^>]+>)", text)
    result = []
    for part in parts:
        if part.startswith("<") and part.endswith(">"):
            result.append(part)
        else:
            if script == "cyrillic":
                result.append(latin_to_cyrillic_text(part))
            else:
                result.append(cyrillic_to_latin_text(part))
    return "".join(result)

# =========================
# DB
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


def ensure_user(user_id: int):
    cursor.execute("""
        INSERT INTO user_prefs (user_id, script, access_granted)
        VALUES (?, 'latin', 0)
        ON CONFLICT(user_id) DO NOTHING
    """, (user_id,))
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


def tr(user_id: int, text: str) -> str:
    return translit_html_safe(text, get_user_script(user_id))


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
    items = []
    for subject_key, subject_data in SUBJECTS.items():
        for teacher_key, teacher_name in subject_data["teachers"].items():
            items.append((subject_key, teacher_key, teacher_name))
    return items


def get_subscription_required_alert(user_id: int) -> str:
    return tr(
        user_id,
        "Avval Telegram kanal, Instagram va Facebook sahifalarga obuna bo'ling."
    )


def get_general_results_text(user_id: int) -> str:
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
    if len(text) > 4000:
        text = text[:4000] + "\n\n... qisqartirildi"
    return tr(user_id, text)


def get_subject_results_text(user_id: int, subject_key: str) -> str:
    if subject_key not in SUBJECTS:
        return tr(user_id, "Noto'g'ri fan.")

    total_votes = get_total_votes()
    lines = [f"📊 <b>{get_subject_name(subject_key)} bo'yicha natijalar</b>\n"]

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
    if len(text) > 4000:
        text = text[:4000] + "\n\n... qisqartirildi"
    return tr(user_id, text)


def get_users_text(user_id: int) -> str:
    cursor.execute("""
        SELECT user_id, full_name, username, subject_key, teacher_key, voted_at
        FROM votes
        ORDER BY voted_at DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        return tr(user_id, "👥 Hali hech kim ovoz bermagan.")

    lines = [f"👥 <b>Kim kimga ovoz berdi</b>\n\nJami: {len(rows)} ta foydalanuvchi\n"]

    for i, (uid, full_name, username, subject_key, teacher_key, voted_at) in enumerate(rows, start=1):
        safe_name = full_name or "Noma'lum"
        line = f"{i}. <b>{safe_name}</b>"
        if username:
            line += f" (@{username})"
        line += f"\n   → Fan: {get_subject_name(subject_key)}"
        line += f"\n   → O'qituvchi: {get_teacher_name(subject_key, teacher_key)}"
        line += f"\n   → ID: <code>{uid}</code>"
        if voted_at:
            line += f"\n   → {voted_at}"
        lines.append(line)

    text = "\n\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n\n... qisqartirildi"
    return tr(user_id, text)


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
            ChatMemberStatus.RESTRICTED,
        }
    except Exception as e:
        logging.error(f"Obunani tekshirishda xatolik: {e}")
        return False


async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup | None = None):
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
# MATNLAR
# =========================
def get_welcome_text(user_id: int) -> str:
    return tr(
        user_id,
        "🚀 <b>Botdan foydalanish uchun quyidagilarni bajaring:</b>\n\n"
        "1️⃣ 📢 Telegram kanalga obuna bo'ling\n"
        "2️⃣ 📘 Facebook sahifaga obuna bo'ling\n"
        "3️⃣ 📸 Instagram sahifaga obuna bo'ling\n\n"
        "👇 Barchasini bajargach, <b>Tekshirish</b> tugmasini bosing"
    )


def get_home_text(user_id: int) -> str:
    return tr(user_id, "🏠 <b>Bosh menyu</b>\n\nKerakli bo'limni tanlang:")


def get_help_text(user_id: int) -> str:
    return tr(
        user_id,
        "ℹ️ <b>Yordam</b>\n\n"
        "• Facebook sahifaga obuna bo'ling\n"
        "• Instagram sahifaga obuna bo'ling\n"
        "• Avval Telegram kanalga obuna bo'ling\n"
        "• So'ng Tekshirish tugmasini bosing\n"
        "• Ovoz berish uchun kafedra tanlanadi\n"
        "• Keyin o'qituvchi tanlanadi\n"
        "• Har bir foydalanuvchi faqat 1 marta ovoz bera oladi\n"
        "• Natijalarni istalgan payt ko'rishingiz mumkin"
    )


def get_already_voted_text(user_id: int) -> str:
    return tr(
        user_id,
        "✅ <b>Siz allaqachon ovoz berib bo'lgansiz</b>\n\n"
        "Qayta ovoz berish mumkin emas.\n"
        "📊 Natijalarni ko'rishingiz mumkin."
    )


def get_closed_text(user_id: int) -> str:
    return tr(
        user_id,
        "🔒 <b>Ovoz berish hozircha yopilgan</b>\n\n"
        "Admin tomonidan ovoz berish vaqtincha to'xtatilgan."
    )


def get_subject_select_text(user_id: int) -> str:
    return tr(user_id, "🗂 <b>Kafedrani tanlang</b>\n\nQuyidagi bo'limlardan birini tanlang:")


def get_teacher_select_text(user_id: int, subject_key: str) -> str:
    return tr(user_id, f"{SUBJECTS[subject_key]['name']}\n\n<b>O'qituvchini tanlang:</b>")


def get_results_menu_text(user_id: int, is_admin_view: bool = False) -> str:
    title = "Admin natijalar bo'limi" if is_admin_view else "Natijalar bo'limi"
    return tr(
        user_id,
        f"📊 <b>{title}</b>\n\n"
        f"Kerakli bo'limni tanlang:\n"
        f"• Umumiy natijalar\n"
        f"• Kafedralar bo'yicha natijalar"
    )


def get_admin_panel_text(user_id: int) -> str:
    status_text = "🟢 Ochiq" if is_voting_open() else "🔴 Yopiq"
    return tr(
        user_id,
        f"🎛 <b>Admin panel</b>\n\n"
        f"Voting holati: {status_text}\n"
        f"Jami ovozlar: {get_total_votes()}"
    )

# =========================
# KLAVIATURALAR
# =========================
def script_switch_button(user_id: int, page: str = "home") -> InlineKeyboardButton:
    if get_user_script(user_id) == "latin":
        return InlineKeyboardButton(
            text="🔤 Krill",
            callback_data=f"set_script:cyrillic:{page}"
        )
    return InlineKeyboardButton(
        text="🔤 Lotin",
        callback_data=f"set_script:latin:{page}"
    )


def subscription_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text=tr(user_id, "📢 Telegram kanal"),
            url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
        )
    )
    kb.row(
        InlineKeyboardButton(
            text=tr(user_id, "📘 Facebook sahifa"),
            url=FACEBOOK_URL
        )
    )
    kb.row(
        InlineKeyboardButton(
            text=tr(user_id, "📸 Instagram sahifa"),
            url=INSTAGRAM_URL
        )
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "✅ Tekshirish"), callback_data="check_subscription"),
        InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user")
    )
    kb.row(script_switch_button(user_id, "subscription"))
    return kb.as_markup()


def home_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    if has_access(user_id):
        kb.row(
            InlineKeyboardButton(text=tr(user_id, "🗳 Ovoz berish"), callback_data="go_vote_panel"),
            InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user")
        )
    else:
        kb.row(
            InlineKeyboardButton(text=tr(user_id, "✅ Obunani tekshirish"), callback_data="check_subscription"),
            InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user")
        )

    kb.row(
        InlineKeyboardButton(text=tr(user_id, "ℹ️ Yordam"), callback_data="help_info"),
        script_switch_button(user_id, "home")
    )
    return kb.as_markup()


def subjects_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for subject_key, subject_data in SUBJECTS.items():
        kb.row(
            InlineKeyboardButton(
                text=tr(user_id, subject_data["name"]),
                callback_data=f"subject:{subject_key}"
            )
        )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"),
        script_switch_button(user_id, "subjects")
    )
    return kb.as_markup()


def teachers_keyboard(user_id: int, subject_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    teachers = list(SUBJECTS[subject_key]["teachers"].items())

    for i in range(0, len(teachers), 2):
        row = []
        for teacher_key, teacher_name in teachers[i:i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=tr(user_id, teacher_name),
                    callback_data=f"vote:{subject_key}:{teacher_key}"
                )
            )
        kb.row(*row)

    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Kafedralarga qaytish"), callback_data="go_vote_panel"))
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"),
        script_switch_button(user_id, f"teachers_{subject_key}")
    )
    return kb.as_markup()


def results_menu_keyboard_user(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "📊 Umumiy"), callback_data="show_results_user:general"))
    for subject_key, subject_data in SUBJECTS.items():
        kb.row(
            InlineKeyboardButton(
                text=tr(user_id, subject_data["name"]),
                callback_data=f"show_results_user:{subject_key}"
            )
        )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "⬅️ Orqaga"), callback_data="go_home"),
        script_switch_button(user_id, "user_results_menu")
    )
    return kb.as_markup()


def results_menu_keyboard_admin(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "📊 Umumiy"), callback_data="show_results_admin:general"))
    for subject_key, subject_data in SUBJECTS.items():
        kb.row(
            InlineKeyboardButton(
                text=tr(user_id, subject_data["name"]),
                callback_data=f"show_results_admin:{subject_key}"
            )
        )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel"),
        script_switch_button(user_id, "admin_results_menu")
    )
    return kb.as_markup()


def results_keyboard_user(user_id: int, scope: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🔄 Yangilash"), callback_data=f"refresh_results_user:{scope}"),
        InlineKeyboardButton(text=tr(user_id, "📂 Bo'limlar"), callback_data="show_results_menu_user")
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"),
        script_switch_button(user_id, f"user_result_{scope}")
    )
    return kb.as_markup()


def results_keyboard_admin(user_id: int, scope: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🔄 Yangilash"), callback_data=f"refresh_results_admin:{scope}"),
        InlineKeyboardButton(text=tr(user_id, "📂 Bo'limlar"), callback_data="admin_results")
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel"),
        script_switch_button(user_id, f"admin_result_{scope}")
    )
    return kb.as_markup()


def after_vote_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user"),
        InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home")
    )
    kb.row(script_switch_button(user_id, "after_vote"))
    return kb.as_markup()


def admin_panel_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "📊 Results"), callback_data="admin_results"),
        InlineKeyboardButton(text=tr(user_id, "👥 Users"), callback_data="admin_users")
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "📁 Export"), callback_data="admin_export"),
        InlineKeyboardButton(text=tr(user_id, "♻ Reset"), callback_data="admin_reset_confirm")
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🔓 Open"), callback_data="admin_open"),
        InlineKeyboardButton(text=tr(user_id, "🔒 Close"), callback_data="admin_close")
    )
    kb.row(script_switch_button(user_id, "admin_panel"))
    return kb.as_markup()


def reset_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "❌ Bekor qilish"), callback_data="cancel_reset"),
        InlineKeyboardButton(text=tr(user_id, "✅ Ha, o'chirish"), callback_data="admin_reset")
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel"),
        script_switch_button(user_id, "admin_reset_confirm")
    )
    return kb.as_markup()


def users_keyboard_admin(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🔄 Yangilash"), callback_data="refresh_admin_users"),
        InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel")
    )
    kb.row(script_switch_button(user_id, "admin_users"))
    return kb.as_markup()

# =========================
# START
# =========================
@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    if not await check_user_subscription(user_id):
        reset_access(user_id)
        await message.answer(
            get_welcome_text(user_id),
            parse_mode="HTML",
            reply_markup=subscription_keyboard(user_id)
        )
        return

    if has_access(user_id):
        await message.answer(
            get_home_text(user_id),
            parse_mode="HTML",
            reply_markup=home_keyboard(user_id)
        )
    else:
        await message.answer(
            get_welcome_text(user_id),
            parse_mode="HTML",
            reply_markup=subscription_keyboard(user_id)
        )

# =========================
# SCRIPT
# =========================
@dp.callback_query(F.data.startswith("set_script:"))
async def set_script_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    parts = callback.data.split(":", 2)

    if len(parts) < 2:
        await callback.answer("Xato", show_alert=True)
        return

    script = parts[1]
    page = parts[2] if len(parts) > 2 else "home"

    if script not in ("latin", "cyrillic"):
        await callback.answer("Xato", show_alert=True)
        return

    set_user_script(user_id, script)

    if page == "subscription":
        await safe_edit_message(
            callback,
            get_welcome_text(user_id),
            subscription_keyboard(user_id)
        )

    elif page == "admin_panel":
        await safe_edit_message(
            callback,
            get_admin_panel_text(user_id),
            admin_panel_keyboard(user_id)
        )

    elif page == "admin_results_menu":
        await safe_edit_message(
            callback,
            get_results_menu_text(user_id, True),
            results_menu_keyboard_admin(user_id)
        )

    elif page.startswith("admin_result_"):
        scope = page.replace("admin_result_", "", 1)
        text = get_general_results_text(user_id) if scope == "general" else get_subject_results_text(user_id, scope)
        await safe_edit_message(
            callback,
            text,
            results_keyboard_admin(user_id, scope)
        )

    elif page == "admin_users":
        await safe_edit_message(
            callback,
            get_users_text(user_id),
            users_keyboard_admin(user_id)
        )

    elif page == "admin_reset_confirm":
        await safe_edit_message(
            callback,
            tr(user_id, "⚠️ <b>Diqqat!</b>\n\nBarcha ovozlar o'chiriladi.\nDavom etasizmi?"),
            reset_confirm_keyboard(user_id)
        )

    elif page == "user_results_menu":
        await safe_edit_message(
            callback,
            get_results_menu_text(user_id, False),
            results_menu_keyboard_user(user_id)
        )

    elif page.startswith("user_result_"):
        scope = page.replace("user_result_", "", 1)
        text = get_general_results_text(user_id) if scope == "general" else get_subject_results_text(user_id, scope)
        await safe_edit_message(
            callback,
            text,
            results_keyboard_user(user_id, scope)
        )

    elif page == "subjects":
        await safe_edit_message(
            callback,
            get_subject_select_text(user_id),
            subjects_keyboard(user_id)
        )

    elif page.startswith("teachers_"):
        subject_key = page.replace("teachers_", "", 1)
        if subject_key in SUBJECTS:
            await safe_edit_message(
                callback,
                get_teacher_select_text(user_id, subject_key),
                teachers_keyboard(user_id, subject_key)
            )
        else:
            await safe_edit_message(
                callback,
                get_home_text(user_id),
                home_keyboard(user_id)
            )

    elif page == "after_vote":
        await safe_edit_message(
            callback,
            get_already_voted_text(user_id),
            home_keyboard(user_id)
        )

    else:
        if has_access(user_id):
            await safe_edit_message(
                callback,
                get_home_text(user_id),
                home_keyboard(user_id)
            )
        else:
            await safe_edit_message(
                callback,
                get_welcome_text(user_id),
                subscription_keyboard(user_id)
            )

    await callback.answer(tr(user_id, "Til yozuvi o'zgartirildi"))

# =========================
# USER CALLBACKS
# =========================
@dp.callback_query(F.data == "go_home")
async def go_home_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if has_access(user_id):
        await safe_edit_message(callback, get_home_text(user_id), home_keyboard(user_id))
    else:
        await safe_edit_message(callback, get_welcome_text(user_id), subscription_keyboard(user_id))
    await callback.answer()


@dp.callback_query(F.data == "help_info")
async def help_info_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Orqaga"), callback_data="go_home"))
    kb.row(script_switch_button(user_id, "help"))
    await safe_edit_message(callback, get_help_text(user_id), kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await check_user_subscription(user_id):
        reset_access(user_id)
        await callback.answer(get_subscription_required_alert(user_id), show_alert=True)
        return

    grant_access(user_id)
    await safe_edit_message(
        callback,
        tr(user_id, "✅ <b>Tekshiruv muvaffaqiyatli o'tdi</b>\n\nEndi bosh menyudan kerakli bo'limni tanlang:"),
        home_keyboard(user_id)
    )
    await callback.answer(tr(user_id, "Tasdiqlandi"))


@dp.callback_query(F.data == "go_vote_panel")
async def go_vote_panel_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not has_access(user_id):
        await safe_edit_message(callback, get_welcome_text(user_id), subscription_keyboard(user_id))
        await callback.answer(get_subscription_required_alert(user_id), show_alert=True)
        return

    if not await check_user_subscription(user_id):
        reset_access(user_id)
        await safe_edit_message(callback, get_welcome_text(user_id), subscription_keyboard(user_id))
        await callback.answer(get_subscription_required_alert(user_id), show_alert=True)
        return

    if has_voted(user_id):
        await safe_edit_message(callback, get_already_voted_text(user_id), home_keyboard(user_id))
        await callback.answer()
        return

    if not is_voting_open():
        await safe_edit_message(callback, get_closed_text(user_id), home_keyboard(user_id))
        await callback.answer()
        return

    await safe_edit_message(callback, get_subject_select_text(user_id), subjects_keyboard(user_id))
    await callback.answer()


@dp.callback_query(F.data.startswith("subject:"))
async def subject_select_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not has_access(user_id):
        await safe_edit_message(callback, get_welcome_text(user_id), subscription_keyboard(user_id))
        await callback.answer(get_subscription_required_alert(user_id), show_alert=True)
        return

    if not await check_user_subscription(user_id):
        reset_access(user_id)
        await safe_edit_message(callback, get_welcome_text(user_id), subscription_keyboard(user_id))
        await callback.answer(get_subscription_required_alert(user_id), show_alert=True)
        return

    if has_voted(user_id):
        await safe_edit_message(callback, get_already_voted_text(user_id), home_keyboard(user_id))
        await callback.answer()
        return

    if not is_voting_open():
        await safe_edit_message(callback, get_closed_text(user_id), home_keyboard(user_id))
        await callback.answer()
        return

    subject_key = callback.data.split(":")[1]

    if subject_key not in SUBJECTS:
        await callback.answer(tr(user_id, "Noto'g'ri bo'lim tanlandi."), show_alert=True)
        return

    await safe_edit_message(
        callback,
        get_teacher_select_text(user_id, subject_key),
        teachers_keyboard(user_id, subject_key)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("vote:"))
async def vote_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not has_access(user_id):
        await callback.answer(get_subscription_required_alert(user_id), show_alert=True)
        return

    if not await check_user_subscription(user_id):
        reset_access(user_id)
        await callback.answer(get_subscription_required_alert(user_id), show_alert=True)
        return

    if not is_voting_open():
        await callback.answer(tr(user_id, "Hozir ovoz berish yopilgan."), show_alert=True)
        return

    if has_voted(user_id):
        await callback.answer(tr(user_id, "Siz faqat 1 marta ovoz bera olasiz."), show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer(tr(user_id, "Noto'g'ri tanlov."), show_alert=True)
        return

    _, subject_key, teacher_key = parts

    if subject_key not in SUBJECTS:
        await callback.answer(tr(user_id, "Noto'g'ri bo'lim."), show_alert=True)
        return

    if teacher_key not in SUBJECTS[subject_key]["teachers"]:
        await callback.answer(tr(user_id, "Noto'g'ri o'qituvchi."), show_alert=True)
        return

    save_vote(
        user_id=user_id,
        full_name=callback.from_user.full_name or "Noma'lum",
        username=callback.from_user.username or "",
        subject_key=subject_key,
        teacher_key=teacher_key,
    )

    text = (
        f"✅ <b>Ovoz muvaffaqiyatli qabul qilindi</b>\n\n"
        f"<b>Bo'lim:</b> {SUBJECTS[subject_key]['name']}\n"
        f"<b>Tanlovingiz:</b> {SUBJECTS[subject_key]['teachers'][teacher_key]}\n\n"
        f"Rahmat, sizning ovozingiz saqlandi."
    )

    await safe_edit_message(callback, tr(user_id, text), after_vote_keyboard(user_id))
    await callback.answer(tr(user_id, "Ovozingiz qabul qilindi!"))

# =========================
# USER RESULTS
# =========================
@dp.callback_query(F.data == "show_results_menu_user")
async def show_results_menu_user(callback: CallbackQuery):
    user_id = callback.from_user.id
    await safe_edit_message(
        callback,
        get_results_menu_text(user_id, False),
        results_menu_keyboard_user(user_id)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("show_results_user:"))
async def show_results_user(callback: CallbackQuery):
    user_id = callback.from_user.id
    scope = callback.data.split(":", 1)[1]
    text = get_general_results_text(user_id) if scope == "general" else get_subject_results_text(user_id, scope)
    await safe_edit_message(callback, text, results_keyboard_user(user_id, scope))
    await callback.answer()


@dp.callback_query(F.data.startswith("refresh_results_user:"))
async def refresh_results_user(callback: CallbackQuery):
    user_id = callback.from_user.id
    scope = callback.data.split(":", 1)[1]
    text = get_general_results_text(user_id) if scope == "general" else get_subject_results_text(user_id, scope)
    await safe_edit_message(callback, text, results_keyboard_user(user_id, scope))
    await callback.answer(tr(user_id, "Yangilandi"))


@dp.message(Command("results"))
async def results_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)
    await message.answer(
        get_results_menu_text(user_id, False),
        parse_mode="HTML",
        reply_markup=results_menu_keyboard_user(user_id)
    )

# =========================
# ADMIN
# =========================
@dp.message(Command("admin"))
async def admin_panel_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    if not is_admin(user_id):
        await message.answer(tr(user_id, "Siz admin emassiz."))
        return

    await message.answer(
        get_admin_panel_text(user_id),
        parse_mode="HTML",
        reply_markup=admin_panel_keyboard(user_id)
    )


@dp.message(Command("users"))
async def admin_users_handler(message: Message):
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer(tr(user_id, "Siz admin emassiz."))
        return

    await message.answer(
        get_users_text(user_id),
        parse_mode="HTML",
        reply_markup=users_keyboard_admin(user_id)
    )


@dp.message(Command("export"))
async def admin_export_handler(message: Message):
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer(tr(user_id, "Siz admin emassiz."))
        return

    filename = export_votes_to_csv()
    await message.answer_document(
        FSInputFile(filename),
        caption=tr(user_id, "📁 Ovozlar CSV fayl ko'rinishida.")
    )


@dp.message(Command("open"))
async def admin_open_handler(message: Message):
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer(tr(user_id, "Siz admin emassiz."))
        return

    open_voting()
    await message.answer(tr(user_id, "🟢 Ovoz berish ochildi."))


@dp.message(Command("close"))
async def admin_close_handler(message: Message):
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer(tr(user_id, "Siz admin emassiz."))
        return

    close_voting()
    await message.answer(tr(user_id, "🔴 Ovoz berish yopildi."))


@dp.message(Command("reset_votes"))
async def admin_reset_handler(message: Message):
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer(tr(user_id, "Siz admin emassiz."))
        return

    await message.answer(
        tr(user_id, "⚠️ <b>Diqqat!</b>\n\nBarcha ovozlar o'chiriladi.\nDavom etasizmi?"),
        parse_mode="HTML",
        reply_markup=reset_confirm_keyboard(user_id)
    )

# =========================
# ADMIN CALLBACKS
# =========================
@dp.callback_query(F.data == "back_admin_panel")
async def back_admin_panel_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    await safe_edit_message(callback, get_admin_panel_text(user_id), admin_panel_keyboard(user_id))
    await callback.answer()


@dp.callback_query(F.data == "admin_results")
async def admin_results_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    await safe_edit_message(
        callback,
        get_results_menu_text(user_id, True),
        results_menu_keyboard_admin(user_id)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("show_results_admin:"))
async def show_results_admin(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    scope = callback.data.split(":", 1)[1]
    text = get_general_results_text(user_id) if scope == "general" else get_subject_results_text(user_id, scope)
    await safe_edit_message(callback, text, results_keyboard_admin(user_id, scope))
    await callback.answer()


@dp.callback_query(F.data.startswith("refresh_results_admin:"))
async def refresh_results_admin_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    scope = callback.data.split(":", 1)[1]
    text = get_general_results_text(user_id) if scope == "general" else get_subject_results_text(user_id, scope)
    await safe_edit_message(callback, text, results_keyboard_admin(user_id, scope))
    await callback.answer(tr(user_id, "Yangilandi"))


@dp.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    await safe_edit_message(callback, get_users_text(user_id), users_keyboard_admin(user_id))
    await callback.answer()


@dp.callback_query(F.data == "refresh_admin_users")
async def refresh_admin_users(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    await safe_edit_message(callback, get_users_text(user_id), users_keyboard_admin(user_id))
    await callback.answer(tr(user_id, "Yangilandi"))


@dp.callback_query(F.data == "admin_export")
async def admin_export_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    filename = export_votes_to_csv()
    await callback.message.answer_document(
        FSInputFile(filename),
        caption=tr(user_id, "📁 Ovozlar CSV fayl ko'rinishida.")
    )
    await callback.answer()


@dp.callback_query(F.data == "admin_open")
async def admin_open_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    open_voting()
    await safe_edit_message(callback, get_admin_panel_text(user_id), admin_panel_keyboard(user_id))
    await callback.answer(tr(user_id, "Voting ochildi!"))


@dp.callback_query(F.data == "admin_close")
async def admin_close_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    close_voting()
    await safe_edit_message(callback, get_admin_panel_text(user_id), admin_panel_keyboard(user_id))
    await callback.answer(tr(user_id, "Voting yopildi!"))


@dp.callback_query(F.data == "admin_reset_confirm")
async def admin_reset_confirm_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    await safe_edit_message(
        callback,
        tr(user_id, "⚠️ <b>Diqqat!</b>\n\nBarcha ovozlar o'chiriladi.\nDavom etasizmi?"),
        reset_confirm_keyboard(user_id)
    )
    await callback.answer()


@dp.callback_query(F.data == "cancel_reset")
async def cancel_reset_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    await safe_edit_message(callback, get_admin_panel_text(user_id), admin_panel_keyboard(user_id))
    await callback.answer(tr(user_id, "Bekor qilindi"))


@dp.callback_query(F.data == "admin_reset")
async def admin_reset_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return

    reset_votes()
    await safe_edit_message(callback, get_admin_panel_text(user_id), admin_panel_keyboard(user_id))
    await callback.answer(tr(user_id, "Reset qilindi!"))

# =========================
# TEXT HANDLER
# =========================
@dp.message(F.text)
async def text_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    if message.text.lower() == "results":
        await message.answer(
            get_results_menu_text(user_id, False),
            parse_mode="HTML",
            reply_markup=results_menu_keyboard_user(user_id)
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
