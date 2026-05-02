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

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None

# =========================
# SOZLAMALAR
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8760253406:AAFn7DlQEUhKF4LlcAvwI0mjK4Dp_DMdsTE")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@QASHQADARYOPMMrasmiy")
TELEGRAM_CHANNEL_URL = "https://t.me/QASHQADARYOPMMrasmiy"

ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "5298063089,7361393654")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]

INSTAGRAM_URL = "https://www.instagram.com/pedagogikmahorat"
FACEBOOK_URL = "https://www.facebook.com/share/1E4ZVePTh4/"

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, "votes.db")
EXPORT_DIR = os.path.join(DATA_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

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

# Telegram callback_data 64 baytdan oshmasligi uchun qisqa aliaslar.
SUBJECT_KEYS = list(SUBJECTS.keys())
SUBJECT_ALIAS = {key: f"s{i + 1}" for i, key in enumerate(SUBJECT_KEYS)}
ALIAS_SUBJECT = {alias: key for key, alias in SUBJECT_ALIAS.items()}

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN or BOT_TOKEN == "BOT_TOKENNI_ENVGA_QOYING":
    raise ValueError("BOT_TOKEN env orqali berilishi kerak")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# =========================
# TRANSLIT
# =========================
def latin_to_cyrillic_text(text: str) -> str:
    pairs = [
        ("O‘", "Ў"), ("o‘", "ў"), ("G‘", "Ғ"), ("g‘", "ғ"),
        ("O'", "Ў"), ("o'", "ў"), ("G'", "Ғ"), ("g'", "ғ"),
        ("Sh", "Ш"), ("sh", "ш"), ("Ch", "Ч"), ("ch", "ч"),
        ("Ya", "Я"), ("ya", "я"), ("Yo", "Ё"), ("yo", "ё"),
        ("Yu", "Ю"), ("yu", "ю"), ("Ts", "Ц"), ("ts", "ц"),
    ]
    for old, new in pairs:
        text = text.replace(old, new)

    table = str.maketrans({
        "A": "А", "a": "а", "B": "Б", "b": "б", "D": "Д", "d": "д",
        "E": "Е", "e": "е", "F": "Ф", "f": "ф", "G": "Г", "g": "г",
        "H": "Ҳ", "h": "ҳ", "I": "И", "i": "и", "J": "Ж", "j": "ж",
        "K": "К", "k": "к", "L": "Л", "l": "л", "M": "М", "m": "м",
        "N": "Н", "n": "н", "O": "О", "o": "о", "P": "П", "p": "п",
        "Q": "Қ", "q": "қ", "R": "Р", "r": "р", "S": "С", "s": "с",
        "T": "Т", "t": "т", "U": "У", "u": "у", "V": "В", "v": "в",
        "X": "Х", "x": "х", "Y": "Й", "y": "й", "Z": "З", "z": "з",
        "`": "ъ", "’": "ъ", "'": "ъ",
    })
    return text.translate(table)


def cyrillic_to_latin_text(text: str) -> str:
    pairs = [
        ("Ў", "O'"), ("ў", "o'"), ("Ғ", "G'"), ("ғ", "g'"),
        ("Ш", "Sh"), ("ш", "sh"), ("Ч", "Ch"), ("ч", "ch"),
        ("Я", "Ya"), ("я", "ya"), ("Ё", "Yo"), ("ё", "yo"),
        ("Ю", "Yu"), ("ю", "yu"), ("Ц", "Ts"), ("ц", "ts"),
    ]
    for old, new in pairs:
        text = text.replace(old, new)

    table = str.maketrans({
        "А": "A", "а": "a", "Б": "B", "б": "b", "Д": "D", "д": "d",
        "Е": "E", "е": "e", "Ф": "F", "ф": "f", "Г": "G", "г": "g",
        "Ҳ": "H", "ҳ": "h", "И": "I", "и": "i", "Ж": "J", "ж": "j",
        "К": "K", "к": "k", "Л": "L", "л": "l", "М": "M", "м": "m",
        "Н": "N", "н": "n", "О": "O", "о": "o", "П": "P", "п": "p",
        "Қ": "Q", "қ": "q", "Р": "R", "р": "r", "С": "S", "с": "s",
        "Т": "T", "т": "t", "У": "U", "у": "u", "В": "V", "в": "v",
        "Х": "X", "х": "x", "Й": "Y", "й": "y", "З": "Z", "з": "z",
        "Ъ": "'", "ъ": "'", "Ь": "", "ь": "",
    })
    return text.translate(table)


def translit_html_safe(text: str, script: str) -> str:
    parts = re.split(r"(<[^>]+>)", text)
    result = []
    for part in parts:
        if part.startswith("<") and part.endswith(">"):
            result.append(part)
        else:
            result.append(latin_to_cyrillic_text(part) if script == "cyrillic" else cyrillic_to_latin_text(part))
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
        CREATE TABLE IF NOT EXISTS teacher_ratings (
            user_id INTEGER NOT NULL,
            full_name TEXT,
            username TEXT,
            subject_key TEXT NOT NULL,
            teacher_key TEXT NOT NULL,
            rating TEXT NOT NULL CHECK(rating IN ('like', 'dislike')),
            rated_at TEXT,
            PRIMARY KEY (user_id, subject_key, teacher_key)
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


def get_subject_alias(subject_key: str) -> str:
    return SUBJECT_ALIAS.get(subject_key, subject_key)


def resolve_subject(alias_or_key: str) -> str | None:
    if alias_or_key in ALIAS_SUBJECT:
        return ALIAS_SUBJECT[alias_or_key]
    if alias_or_key in SUBJECTS:
        return alias_or_key
    return None


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


def save_teacher_rating(user_id: int, full_name: str, username: str, subject_key: str, teacher_key: str, rating: str):
    cursor.execute("""
        INSERT INTO teacher_ratings (user_id, full_name, username, subject_key, teacher_key, rating, rated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, subject_key, teacher_key)
        DO UPDATE SET
            full_name = excluded.full_name,
            username = excluded.username,
            rating = excluded.rating,
            rated_at = excluded.rated_at
    """, (
        user_id,
        full_name,
        username,
        subject_key,
        teacher_key,
        rating,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()


def get_total_votes() -> int:
    cursor.execute("SELECT COUNT(*) FROM votes")
    return cursor.fetchone()[0]


def get_total_ratings() -> int:
    cursor.execute("SELECT COUNT(*) FROM teacher_ratings")
    return cursor.fetchone()[0]


def reset_votes():
    cursor.execute("DELETE FROM votes")
    conn.commit()


def reset_ratings():
    cursor.execute("DELETE FROM teacher_ratings")
    conn.commit()


def get_subject_name(subject_key: str) -> str:
    return SUBJECTS.get(subject_key, {}).get("name", subject_key)


def get_teacher_name(subject_key: str, teacher_key: str) -> str:
    return SUBJECTS.get(subject_key, {}).get("teachers", {}).get(teacher_key, teacher_key)


def build_progress_bar(percent: float, length: int = 12) -> str:
    filled = round((percent / 100) * length)
    filled = max(0, min(filled, length))
    return "▓" * filled + "░" * (length - filled)


def get_all_teachers_flat():
    items = []
    for subject_key, subject_data in SUBJECTS.items():
        for teacher_key, teacher_name in subject_data["teachers"].items():
            items.append((subject_key, teacher_key, teacher_name))
    return items


def rating_counts(subject_key: str, teacher_key: str):
    cursor.execute("""
        SELECT
            SUM(CASE WHEN rating = 'like' THEN 1 ELSE 0 END),
            SUM(CASE WHEN rating = 'dislike' THEN 1 ELSE 0 END),
            COUNT(*)
        FROM teacher_ratings
        WHERE subject_key = ? AND teacher_key = ?
    """, (subject_key, teacher_key))
    like_count, dislike_count, total = cursor.fetchone()
    like_count = like_count or 0
    dislike_count = dislike_count or 0
    total = total or 0
    like_percent = (like_count / total * 100) if total else 0
    dislike_percent = (dislike_count / total * 100) if total else 0
    return like_count, dislike_count, total, like_percent, dislike_percent


def get_subscription_required_alert(user_id: int) -> str:
    return tr(user_id, "Avval Instagram, Facebook va Telegram kanalga obuna bo'ling.")


def get_general_results_text(user_id: int) -> str:
    total_votes = get_total_votes()
    lines = ["📊 <b>Umumiy ovoz berish natijalari</b>\n"]

    for subject_key, teacher_key, teacher_name in get_all_teachers_flat():
        cursor.execute("""
            SELECT COUNT(*)
            FROM votes
            WHERE subject_key = ? AND teacher_key = ?
        """, (subject_key, teacher_key))
        count = cursor.fetchone()[0]
        percent = (count / total_votes * 100) if total_votes > 0 else 0
        lines.append(
            f"<b>{teacher_name}</b> — {get_subject_name(subject_key)}\n"
            f"<code>{build_progress_bar(percent)}</code>  <b>{percent:.1f}%</b>  •  {count} ta\n"
        )

    lines.append(f"🗳 <b>Jami ovozlar:</b> {total_votes}")
    lines.append(f"{'🟢' if is_voting_open() else '🔴'} <b>Holat:</b> {'Ochiq' if is_voting_open() else 'Yopiq'}")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n\n... qisqartirildi. To'liq ma'lumot uchun Excel oling."
    return tr(user_id, text)


def get_subject_results_text(user_id: int, subject_key: str) -> str:
    if subject_key not in SUBJECTS:
        return tr(user_id, "Noto'g'ri fan.")

    cursor.execute("SELECT COUNT(*) FROM votes WHERE subject_key = ?", (subject_key,))
    subject_total = cursor.fetchone()[0]

    lines = [f"📊 <b>{get_subject_name(subject_key)} bo'yicha natijalar</b>\n"]

    for teacher_key, teacher_name in SUBJECTS[subject_key]["teachers"].items():
        cursor.execute("""
            SELECT COUNT(*)
            FROM votes
            WHERE subject_key = ? AND teacher_key = ?
        """, (subject_key, teacher_key))
        count = cursor.fetchone()[0]
        percent = (count / subject_total * 100) if subject_total > 0 else 0

        lines.append(
            f"<b>{teacher_name}</b>\n"
            f"<code>{build_progress_bar(percent)}</code>  <b>{percent:.1f}%</b>  •  {count} ta\n"
        )

    lines.append(f"🗳 <b>Shu bo'limdagi jami ovozlar:</b> {subject_total}")
    lines.append(f"{'🟢' if is_voting_open() else '🔴'} <b>Holat:</b> {'Ochiq' if is_voting_open() else 'Yopiq'}")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n\n... qisqartirildi. To'liq ma'lumot uchun Excel oling."
    return tr(user_id, text)


def get_teacher_ratings_text(user_id: int, subject_key: str | None = None) -> str:
    if subject_key and subject_key not in SUBJECTS:
        return tr(user_id, "Noto'g'ri kafedra.")

    title = "O'qituvchilarni baholash statistikasi"
    if subject_key:
        title = f"{get_subject_name(subject_key)} baholash statistikasi"

    lines = [f"⭐ <b>{title}</b>\n"]

    teacher_items = [(subject_key, tk, tn) for tk, tn in SUBJECTS[subject_key]["teachers"].items()] if subject_key else get_all_teachers_flat()

    for s_key, t_key, teacher_name in teacher_items:
        like_count, dislike_count, total, like_percent, dislike_percent = rating_counts(s_key, t_key)

        lines.append(
            f"<b>{teacher_name}</b>\n"
            f"🏛 {get_subject_name(s_key)}\n"
            f"👍 <code>{build_progress_bar(like_percent, 10)}</code> <b>{like_percent:.1f}%</b> • {like_count} ta\n"
            f"👎 <code>{build_progress_bar(dislike_percent, 10)}</code> <b>{dislike_percent:.1f}%</b> • {dislike_count} ta\n"
            f"📌 Jami baho: <b>{total}</b> ta\n"
        )

    lines.append(f"⭐ <b>Jami baholashlar:</b> {get_total_ratings()}")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n\n... qisqartirildi. To'liq ma'lumot uchun Excel oling."
    return tr(user_id, text)


def get_top_ratings_text(user_id: int, mode: str) -> str:
    rows = []
    for subject_key, teacher_key, teacher_name in get_all_teachers_flat():
        like_count, dislike_count, total, like_percent, dislike_percent = rating_counts(subject_key, teacher_key)
        if total == 0:
            continue
        rows.append({
            "subject_key": subject_key,
            "teacher_key": teacher_key,
            "teacher_name": teacher_name,
            "like_count": like_count,
            "dislike_count": dislike_count,
            "total": total,
            "like_percent": like_percent,
            "dislike_percent": dislike_percent,
        })

    if mode == "like_high":
        title = "TOP 10 eng baland like nisbati"
        rows.sort(key=lambda x: (x["like_percent"], x["like_count"], x["total"]), reverse=True)
        percent_key = "like_percent"
        count_key = "like_count"
        emoji = "👍"
    elif mode == "like_low":
        title = "TOP 10 eng past like nisbati"
        rows.sort(key=lambda x: (x["like_percent"], -x["dislike_count"]))
        percent_key = "like_percent"
        count_key = "like_count"
        emoji = "👍"
    elif mode == "dislike_high":
        title = "TOP 10 eng baland dislike nisbati"
        rows.sort(key=lambda x: (x["dislike_percent"], x["dislike_count"], x["total"]), reverse=True)
        percent_key = "dislike_percent"
        count_key = "dislike_count"
        emoji = "👎"
    else:
        title = "TOP 10 eng past dislike nisbati"
        rows.sort(key=lambda x: (x["dislike_percent"], -x["like_count"]))
        percent_key = "dislike_percent"
        count_key = "dislike_count"
        emoji = "👎"

    lines = [f"🏆 <b>{title}</b>\n"]
    for i, row in enumerate(rows[:10], start=1):
        percent = row[percent_key]
        count = row[count_key]
        lines.append(
            f"{i}. <b>{row['teacher_name']}</b>\n"
            f"🏛 {get_subject_name(row['subject_key'])}\n"
            f"{emoji} <b>{percent:.1f}%</b> • {count} ta / jami {row['total']} ta\n"
        )

    if not rows:
        lines.append("Hali baholashlar yo'q.")

    return tr(user_id, "\n".join(lines))


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
        text = text[:4000] + "\n\n... qisqartirildi. To'liq ma'lumot uchun Excel oling."
    return tr(user_id, text)


def export_rows_xlsx(filename: str, headers: list[str], rows: list[list]):
    path = os.path.join(EXPORT_DIR, filename)
    if Workbook is None:
        csv_path = path.replace(".xlsx", ".csv")
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return csv_path

    wb = Workbook()
    ws = wb.active
    ws.title = "Hisobot"
    ws.append(headers)
    for row in rows:
        ws.append(row)

    for column_cells in ws.columns:
        max_length = 0
        col_letter = column_cells[0].column_letter
        for cell in column_cells:
            value = "" if cell.value is None else str(cell.value)
            max_length = max(max_length, len(value))
        ws.column_dimensions[col_letter].width = min(max_length + 2, 45)

    wb.save(path)
    return path


def export_votes(scope: str = "general") -> str:
    subject_key = None if scope == "general" else resolve_subject(scope)

    if subject_key:
        cursor.execute("""
            SELECT user_id, full_name, username, subject_key, teacher_key, voted_at
            FROM votes
            WHERE subject_key = ?
            ORDER BY voted_at DESC
        """, (subject_key,))
        filename = f"votes_{subject_key}.xlsx"
    else:
        cursor.execute("""
            SELECT user_id, full_name, username, subject_key, teacher_key, voted_at
            FROM votes
            ORDER BY voted_at DESC
        """)
        filename = "votes_general.xlsx"

    rows_db = cursor.fetchall()
    rows = []
    for user_id, full_name, username, s_key, t_key, voted_at in rows_db:
        rows.append([
            user_id,
            full_name or "",
            username or "",
            get_subject_name(s_key),
            get_teacher_name(s_key, t_key),
            voted_at or ""
        ])

    return export_rows_xlsx(
        filename,
        ["User ID", "Full Name", "Username", "Subject", "Teacher", "Voted At"],
        rows
    )


def export_rating_stats(scope: str = "general") -> str:
    subject_key = None if scope == "general" else resolve_subject(scope)
    teacher_items = [(subject_key, tk, tn) for tk, tn in SUBJECTS[subject_key]["teachers"].items()] if subject_key else get_all_teachers_flat()

    rows = []
    for s_key, t_key, teacher_name in teacher_items:
        like_count, dislike_count, total, like_percent, dislike_percent = rating_counts(s_key, t_key)
        rows.append([
            get_subject_name(s_key),
            teacher_name,
            like_count,
            dislike_count,
            total,
            round(like_percent, 2),
            round(dislike_percent, 2),
        ])

    filename = f"ratings_{subject_key or 'general'}.xlsx"
    return export_rows_xlsx(
        filename,
        ["Subject", "Teacher", "Like count", "Dislike count", "Total ratings", "Like %", "Dislike %"],
        rows
    )


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
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return
        try:
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=reply_markup)
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
        "1️⃣ 📸 Instagram sahifaga obuna bo'ling\n"
        "2️⃣ 📘 Facebook sahifaga obuna bo'ling\n"
        "3️⃣ 📢 Telegram kanalga obuna bo'ling\n\n"
        "👇 Barchasini bajargach, <b>✅ Tekshirish</b> tugmasini bosing"
    )


def get_home_text(user_id: int) -> str:
    return tr(user_id, "🏠 <b>Bosh menyu</b>\n\nKerakli bo'limni tanlang:")


def get_help_text(user_id: int) -> str:
    return tr(
        user_id,
        "ℹ️ <b>Yordam</b>\n\n"
        "• Avval Instagram sahifaga obuna bo'ling\n"
        "• Facebook sahifaga obuna bo'ling\n"
        "• Telegram kanalga obuna bo'ling\n"
        "• So'ng Tekshirish tugmasini bosing\n"
        "• Ovoz berish uchun kafedra tanlanadi\n"
        "• Keyin o'qituvchi tanlanadi\n"
        "• O'qituvchilarni baholash bo'limida xohlagan o'qituvchiga 👍 yoki 👎 bosish mumkin\n"
        "• Har bir foydalanuvchi ovoz berishda faqat 1 marta qatnashadi\n"
        "• Baholashda har bir o'qituvchiga 1 ta baho beriladi, keyin uni o'zgartirish mumkin"
    )


def get_already_voted_text(user_id: int) -> str:
    return tr(
        user_id,
        "✅ <b>Siz allaqachon ovoz berib bo'lgansiz</b>\n\n"
        "Qayta ovoz berish mumkin emas.\n"
        "📊 Natijalarni ko'rishingiz mumkin."
    )


def get_closed_text(user_id: int) -> str:
    return tr(user_id, "🔒 <b>Ovoz berish hozircha yopilgan</b>\n\nAdmin tomonidan ovoz berish vaqtincha to'xtatilgan.")


def get_subject_select_text(user_id: int) -> str:
    return tr(user_id, "🗂 <b>Kafedrani tanlang</b>\n\nQuyidagi bo'limlardan birini tanlang:")


def get_teacher_select_text(user_id: int, subject_key: str) -> str:
    return tr(user_id, f"🏛 <b>{SUBJECTS[subject_key]['name']}</b>\n\n<b>O'qituvchini tanlang:</b>")


def get_rating_menu_text(user_id: int) -> str:
    return tr(user_id, "⭐ <b>O'qituvchilarni baholash</b>\n\nBaholash uchun avval kafedrani tanlang:")


def get_rating_text(user_id: int, subject_key: str, teacher_key: str) -> str:
    return tr(
        user_id,
        f"⭐ <b>O'qituvchini baholash</b>\n\n"
        f"🏛 <b>Kafedra:</b> {get_subject_name(subject_key)}\n"
        f"👤 <b>O'qituvchi:</b> {get_teacher_name(subject_key, teacher_key)}\n\n"
        f"Quyidagilardan birini tanlang:"
    )


def get_results_menu_text(user_id: int, is_admin_view: bool = False) -> str:
    title = "Admin natijalar bo'limi" if is_admin_view else "Natijalar bo'limi"
    return tr(user_id, f"📊 <b>{title}</b>\n\nKerakli bo'limni tanlang:")


def get_admin_panel_text(user_id: int) -> str:
    status_text = "🟢 Ochiq" if is_voting_open() else "🔴 Yopiq"
    return tr(
        user_id,
        f"🎛 <b>Admin panel</b>\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🗳 <b>Voting holati:</b> {status_text}\n"
        f"📊 <b>Jami ovozlar:</b> {get_total_votes()}\n"
        f"⭐ <b>Jami baholashlar:</b> {get_total_ratings()}\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"Kerakli boshqaruv bo'limini tanlang:"
    )

# =========================
# KLAVIATURALAR
# =========================
def script_switch_button(user_id: int) -> InlineKeyboardButton:
    if get_user_script(user_id) == "latin":
        return InlineKeyboardButton(text="🔤 Krill", callback_data="toggle_script")
    return InlineKeyboardButton(text="🔤 Lotin", callback_data="toggle_script")


def subscription_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "1️⃣ 📸 Instagram"), url=INSTAGRAM_URL))
    kb.row(InlineKeyboardButton(text=tr(user_id, "2️⃣ 📘 Facebook"), url=FACEBOOK_URL))
    kb.row(InlineKeyboardButton(text=tr(user_id, "3️⃣ 📢 Telegram kanal"), url=TELEGRAM_CHANNEL_URL))
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "✅ Tekshirish"), callback_data="check_subscription"),
        InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user")
    )
    kb.row(script_switch_button(user_id))
    return kb.as_markup()


def home_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if has_access(user_id):
        kb.row(
            InlineKeyboardButton(text=tr(user_id, "🗳 Ovoz berish"), callback_data="go_vote_panel"),
            InlineKeyboardButton(text=tr(user_id, "⭐ Baholash"), callback_data="go_rating_panel")
        )
        kb.row(InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user"))
    else:
        kb.row(
            InlineKeyboardButton(text=tr(user_id, "✅ Obunani tekshirish"), callback_data="check_subscription"),
            InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user")
        )

    kb.row(
        InlineKeyboardButton(text=tr(user_id, "ℹ️ Yordam"), callback_data="help_info"),
        script_switch_button(user_id)
    )
    return kb.as_markup()


def subjects_keyboard(user_id: int, mode: str = "vote") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    prefix = "sub" if mode == "vote" else "rsub"

    for subject_key, subject_data in SUBJECTS.items():
        alias = get_subject_alias(subject_key)
        kb.row(InlineKeyboardButton(text=tr(user_id, f"🏛 {subject_data['name']}"), callback_data=f"{prefix}:{alias}"))

    kb.row(InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"), script_switch_button(user_id))
    return kb.as_markup()


def teachers_keyboard(user_id: int, subject_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    alias = get_subject_alias(subject_key)
    teachers = list(SUBJECTS[subject_key]["teachers"].items())

    for i in range(0, len(teachers), 2):
        row = []
        for teacher_key, teacher_name in teachers[i:i + 2]:
            row.append(InlineKeyboardButton(text=tr(user_id, f"👤 {teacher_name}"), callback_data=f"vote:{alias}:{teacher_key}"))
        kb.row(*row)

    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Kafedralarga qaytish"), callback_data="go_vote_panel"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"), script_switch_button(user_id))
    return kb.as_markup()


def rating_teachers_keyboard(user_id: int, subject_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    alias = get_subject_alias(subject_key)

    for teacher_key, teacher_name in SUBJECTS[subject_key]["teachers"].items():
        kb.row(InlineKeyboardButton(text=tr(user_id, f"⭐ {teacher_name}"), callback_data=f"rteach:{alias}:{teacher_key}"))

    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Kafedralarga qaytish"), callback_data="go_rating_panel"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"), script_switch_button(user_id))
    return kb.as_markup()


def like_dislike_keyboard(user_id: int, subject_key: str, teacher_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    alias = get_subject_alias(subject_key)
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "👍 Like"), callback_data=f"rate:l:{alias}:{teacher_key}"),
        InlineKeyboardButton(text=tr(user_id, "👎 Dislike"), callback_data=f"rate:d:{alias}:{teacher_key}")
    )
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ O'qituvchilarga qaytish"), callback_data=f"rsub:{alias}"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"))
    return kb.as_markup()


def results_menu_keyboard_user(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "📊 Umumiy ovozlar"), callback_data="ures:general"))
    for subject_key, subject_data in SUBJECTS.items():
        kb.row(InlineKeyboardButton(text=tr(user_id, f"🏛 {subject_data['name']}"), callback_data=f"ures:{get_subject_alias(subject_key)}"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Orqaga"), callback_data="go_home"), script_switch_button(user_id))
    return kb.as_markup()


def results_keyboard_user(user_id: int, scope: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🔄 Yangilash"), callback_data=f"uref:{scope}"),
        InlineKeyboardButton(text=tr(user_id, "📂 Bo'limlar"), callback_data="show_results_menu_user")
    )
    kb.row(InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"), script_switch_button(user_id))
    return kb.as_markup()


def results_menu_keyboard_admin(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "📊 Umumiy ovozlar"), callback_data="ares:general"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "⭐ Baholash statistikasi"), callback_data="admin_ratings_menu"))
    for subject_key, subject_data in SUBJECTS.items():
        kb.row(InlineKeyboardButton(text=tr(user_id, f"🏛 {subject_data['name']}"), callback_data=f"ares:{get_subject_alias(subject_key)}"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel"), script_switch_button(user_id))
    return kb.as_markup()


def results_keyboard_admin(user_id: int, scope: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🔄 Yangilash"), callback_data=f"aref:{scope}"),
        InlineKeyboardButton(text=tr(user_id, "📂 Bo'limlar"), callback_data="admin_results")
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "📁 Excel olish"), callback_data=f"export_votes:{scope}"),
        InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel")
    )
    kb.row(script_switch_button(user_id))
    return kb.as_markup()


def admin_ratings_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "⭐ Umumiy baholash"), callback_data="arate:general"))
    for subject_key, subject_data in SUBJECTS.items():
        kb.row(InlineKeyboardButton(text=tr(user_id, f"🏛 {subject_data['name']}"), callback_data=f"arate:{get_subject_alias(subject_key)}"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "🏆 TOP reytinglar"), callback_data="top_menu"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel"))
    return kb.as_markup()


def ratings_keyboard_admin(user_id: int, scope: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🔄 Yangilash"), callback_data=f"arref:{scope}"),
        InlineKeyboardButton(text=tr(user_id, "📂 Bo'limlar"), callback_data="admin_ratings_menu")
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "📁 Excel olish"), callback_data=f"export_ratings:{scope}"),
        InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel")
    )
    return kb.as_markup()


def top_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "👍 Like baland TOP 10"), callback_data="top:like_high"),
        InlineKeyboardButton(text=tr(user_id, "👍 Like past TOP 10"), callback_data="top:like_low")
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "👎 Dislike baland TOP 10"), callback_data="top:dislike_high"),
        InlineKeyboardButton(text=tr(user_id, "👎 Dislike past TOP 10"), callback_data="top:dislike_low")
    )
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Baholash bo'limi"), callback_data="admin_ratings_menu"))
    return kb.as_markup()


def top_result_keyboard(user_id: int, mode: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🔄 Yangilash"), callback_data=f"top:{mode}"),
        InlineKeyboardButton(text=tr(user_id, "⬅️ TOP menyu"), callback_data="top_menu")
    )
    return kb.as_markup()


def after_vote_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "⭐ O'qituvchilarni baholash"), callback_data="go_rating_panel"))
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user"),
        InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home")
    )
    kb.row(script_switch_button(user_id))
    return kb.as_markup()


def admin_panel_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "📊 Ovoz natijalari"), callback_data="admin_results"),
        InlineKeyboardButton(text=tr(user_id, "⭐ Baholash foizlari"), callback_data="admin_ratings_menu")
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🏆 TOP reytinglar"), callback_data="top_menu"),
        InlineKeyboardButton(text=tr(user_id, "👥 Foydalanuvchilar"), callback_data="admin_users")
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "📁 Excel ovozlar"), callback_data="export_votes:general"),
        InlineKeyboardButton(text=tr(user_id, "📁 Excel rating"), callback_data="export_ratings:general")
    )
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "♻ Reset ovozlar"), callback_data="admin_reset_confirm"),
        InlineKeyboardButton(text=tr(user_id, "🗑 Reset rating"), callback_data="admin_reset_ratings_confirm")
    )
    kb.row(InlineKeyboardButton(text=tr(user_id, "🔓 Open / 🔒 Close"), callback_data="admin_toggle_voting"))
    kb.row(script_switch_button(user_id))
    return kb.as_markup()


def reset_confirm_keyboard(user_id: int, reset_type: str = "votes") -> InlineKeyboardMarkup:
    yes_callback = "admin_reset" if reset_type == "votes" else "admin_reset_ratings"
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "❌ Bekor qilish"), callback_data="cancel_reset"),
        InlineKeyboardButton(text=tr(user_id, "✅ Ha, o'chirish"), callback_data=yes_callback)
    )
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel"))
    return kb.as_markup()


def users_keyboard_admin(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text=tr(user_id, "🔄 Yangilash"), callback_data="refresh_admin_users"),
        InlineKeyboardButton(text=tr(user_id, "📁 Excel olish"), callback_data="export_votes:general")
    )
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel"))
    kb.row(script_switch_button(user_id))
    return kb.as_markup()

# =========================
# RENDER HELPERS
# =========================
async def render_user_results(callback: CallbackQuery, scope: str):
    user_id = callback.from_user.id
    subject_key = None if scope == "general" else resolve_subject(scope)
    if scope != "general" and not subject_key:
        await callback.answer(tr(user_id, "Noto'g'ri bo'lim."), show_alert=True)
        return
    text = get_general_results_text(user_id) if scope == "general" else get_subject_results_text(user_id, subject_key)
    await safe_edit_message(callback, text, results_keyboard_user(user_id, scope))
    await callback.answer()


async def render_admin_results(callback: CallbackQuery, scope: str):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    subject_key = None if scope == "general" else resolve_subject(scope)
    if scope != "general" and not subject_key:
        await callback.answer(tr(user_id, "Noto'g'ri bo'lim."), show_alert=True)
        return
    text = get_general_results_text(user_id) if scope == "general" else get_subject_results_text(user_id, subject_key)
    await safe_edit_message(callback, text, results_keyboard_admin(user_id, scope))
    await callback.answer()


async def render_admin_ratings(callback: CallbackQuery, scope: str):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    subject_key = None if scope == "general" else resolve_subject(scope)
    if scope != "general" and not subject_key:
        await callback.answer(tr(user_id, "Noto'g'ri bo'lim."), show_alert=True)
        return
    await safe_edit_message(callback, get_teacher_ratings_text(user_id, subject_key), ratings_keyboard_admin(user_id, scope))
    await callback.answer()

# =========================
# START
# =========================
@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    if not await check_user_subscription(user_id):
        reset_access(user_id)
        await message.answer(get_welcome_text(user_id), parse_mode="HTML", reply_markup=subscription_keyboard(user_id))
        return

    grant_access(user_id)
    await message.answer(get_home_text(user_id), parse_mode="HTML", reply_markup=home_keyboard(user_id))


@dp.callback_query(F.data == "toggle_script")
async def toggle_script_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    current = get_user_script(user_id)
    new_script = "cyrillic" if current == "latin" else "latin"
    set_user_script(user_id, new_script)

    # Hech qaysi boshqa oynaga otmaydi. Faqat global sozlamani o'zgartiradi.
    await callback.answer(tr(user_id, "Til yozuvi o'zgartirildi. Oynani yangilash uchun bo'lim tugmasini qayta bosing."), show_alert=False)


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
    kb.row(script_switch_button(user_id))
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

    await safe_edit_message(callback, get_subject_select_text(user_id), subjects_keyboard(user_id, "vote"))
    await callback.answer()


@dp.callback_query(F.data == "go_rating_panel")
async def go_rating_panel_handler(callback: CallbackQuery):
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

    await safe_edit_message(callback, get_rating_menu_text(user_id), subjects_keyboard(user_id, "rating"))
    await callback.answer()


@dp.callback_query(F.data.startswith("sub:"))
async def subject_select_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    alias = callback.data.split(":", 1)[1]
    subject_key = resolve_subject(alias)

    if not subject_key:
        await callback.answer(tr(user_id, "Noto'g'ri bo'lim tanlandi."), show_alert=True)
        return

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

    await safe_edit_message(callback, get_teacher_select_text(user_id, subject_key), teachers_keyboard(user_id, subject_key))
    await callback.answer()


@dp.callback_query(F.data.startswith("rsub:"))
async def rating_subject_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    alias = callback.data.split(":", 1)[1]
    subject_key = resolve_subject(alias)

    if not subject_key:
        await callback.answer(tr(user_id, "Noto'g'ri kafedra."), show_alert=True)
        return

    await safe_edit_message(callback, get_teacher_select_text(user_id, subject_key), rating_teachers_keyboard(user_id, subject_key))
    await callback.answer()


@dp.callback_query(F.data.startswith("rteach:"))
async def rating_teacher_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    _, alias, teacher_key = callback.data.split(":")
    subject_key = resolve_subject(alias)

    if not subject_key or teacher_key not in SUBJECTS[subject_key]["teachers"]:
        await callback.answer(tr(user_id, "Noto'g'ri o'qituvchi."), show_alert=True)
        return

    await safe_edit_message(callback, get_rating_text(user_id, subject_key, teacher_key), like_dislike_keyboard(user_id, subject_key, teacher_key))
    await callback.answer()


@dp.callback_query(F.data.startswith("rate:"))
async def rate_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer(tr(user_id, "Noto'g'ri baho."), show_alert=True)
        return

    _, short_rating, alias, teacher_key = parts
    subject_key = resolve_subject(alias)
    rating = "like" if short_rating == "l" else "dislike" if short_rating == "d" else None

    if rating not in ("like", "dislike") or not subject_key or teacher_key not in SUBJECTS[subject_key]["teachers"]:
        await callback.answer(tr(user_id, "Noto'g'ri baho."), show_alert=True)
        return

    save_teacher_rating(
        user_id=user_id,
        full_name=callback.from_user.full_name or "Noma'lum",
        username=callback.from_user.username or "",
        subject_key=subject_key,
        teacher_key=teacher_key,
        rating=rating,
    )

    emoji = "👍 Like" if rating == "like" else "👎 Dislike"
    text = (
        f"✅ <b>Bahongiz saqlandi</b>\n\n"
        f"👤 <b>O'qituvchi:</b> {get_teacher_name(subject_key, teacher_key)}\n"
        f"🏛 <b>Kafedra:</b> {get_subject_name(subject_key)}\n"
        f"⭐ <b>Sizning bahongiz:</b> {emoji}\n\n"
        f"Xohlasangiz, boshqa o'qituvchilarni ham baholashingiz mumkin."
    )

    await safe_edit_message(callback, tr(user_id, text), rating_teachers_keyboard(user_id, subject_key))
    await callback.answer(tr(user_id, "Bahongiz qabul qilindi!"))


@dp.callback_query(F.data.startswith("vote:"))
async def vote_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer(tr(user_id, "Noto'g'ri tanlov."), show_alert=True)
        return

    _, alias, teacher_key = parts
    subject_key = resolve_subject(alias)

    if not subject_key or teacher_key not in SUBJECTS[subject_key]["teachers"]:
        await callback.answer(tr(user_id, "Noto'g'ri o'qituvchi."), show_alert=True)
        return

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
    await safe_edit_message(callback, get_results_menu_text(user_id, False), results_menu_keyboard_user(user_id))
    await callback.answer()


@dp.callback_query(F.data.startswith("ures:"))
async def show_results_user(callback: CallbackQuery):
    await render_user_results(callback, callback.data.split(":", 1)[1])


@dp.callback_query(F.data.startswith("uref:"))
async def refresh_results_user(callback: CallbackQuery):
    await render_user_results(callback, callback.data.split(":", 1)[1])

# =========================
# ADMIN COMMANDS
# =========================
@dp.message(Command("admin"))
async def admin_panel_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    if not is_admin(user_id):
        await message.answer(tr(user_id, "Siz admin emassiz."))
        return

    await message.answer(get_admin_panel_text(user_id), parse_mode="HTML", reply_markup=admin_panel_keyboard(user_id))


@dp.message(Command("users"))
async def admin_users_handler(message: Message):
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer(tr(user_id, "Siz admin emassiz."))
        return

    await message.answer(get_users_text(user_id), parse_mode="HTML", reply_markup=users_keyboard_admin(user_id))


@dp.message(Command("results"))
async def results_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)
    await message.answer(get_results_menu_text(user_id, False), parse_mode="HTML", reply_markup=results_menu_keyboard_user(user_id))


@dp.message(Command("export"))
async def admin_export_handler(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer(tr(user_id, "Siz admin emassiz."))
        return
    filename = export_votes("general")
    await message.answer_document(FSInputFile(filename), caption=tr(user_id, "📁 Ovozlar Excel fayl ko'rinishida."))


@dp.message(Command("export_ratings"))
async def admin_export_ratings_handler(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer(tr(user_id, "Siz admin emassiz."))
        return
    filename = export_rating_stats("general")
    await message.answer_document(FSInputFile(filename), caption=tr(user_id, "📁 Baholash statistikasi Excel fayl ko'rinishida."))


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


@dp.callback_query(F.data == "admin_toggle_voting")
async def admin_toggle_voting_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    if is_voting_open():
        close_voting()
        msg = "Voting yopildi!"
    else:
        open_voting()
        msg = "Voting ochildi!"
    await safe_edit_message(callback, get_admin_panel_text(user_id), admin_panel_keyboard(user_id))
    await callback.answer(tr(user_id, msg))


@dp.callback_query(F.data == "admin_results")
async def admin_results_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    await safe_edit_message(callback, get_results_menu_text(user_id, True), results_menu_keyboard_admin(user_id))
    await callback.answer()


@dp.callback_query(F.data.startswith("ares:"))
async def show_results_admin(callback: CallbackQuery):
    await render_admin_results(callback, callback.data.split(":", 1)[1])


@dp.callback_query(F.data.startswith("aref:"))
async def refresh_results_admin_handler(callback: CallbackQuery):
    await render_admin_results(callback, callback.data.split(":", 1)[1])


@dp.callback_query(F.data == "admin_ratings_menu")
async def admin_ratings_menu_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    await safe_edit_message(callback, tr(user_id, "⭐ <b>Baholash statistikasi</b>\n\nQaysi bo'lim statistikasi kerak?"), admin_ratings_menu_keyboard(user_id))
    await callback.answer()


@dp.callback_query(F.data.startswith("arate:"))
async def admin_ratings_callback(callback: CallbackQuery):
    await render_admin_ratings(callback, callback.data.split(":", 1)[1])


@dp.callback_query(F.data.startswith("arref:"))
async def refresh_admin_ratings_callback(callback: CallbackQuery):
    await render_admin_ratings(callback, callback.data.split(":", 1)[1])


@dp.callback_query(F.data == "top_menu")
async def top_menu_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    await safe_edit_message(callback, tr(user_id, "🏆 <b>TOP reytinglar</b>\n\nKerakli reyting turini tanlang:"), top_menu_keyboard(user_id))
    await callback.answer()


@dp.callback_query(F.data.startswith("top:"))
async def top_result_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    mode = callback.data.split(":", 1)[1]
    await safe_edit_message(callback, get_top_ratings_text(user_id, mode), top_result_keyboard(user_id, mode))
    await callback.answer()


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


@dp.callback_query(F.data.startswith("export_votes:"))
async def export_votes_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    scope = callback.data.split(":", 1)[1]
    filename = export_votes(scope)
    await callback.message.answer_document(FSInputFile(filename), caption=tr(user_id, "📁 Ovozlar Excel fayl ko'rinishida."))
    await callback.answer()


@dp.callback_query(F.data.startswith("export_ratings:"))
async def export_ratings_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    scope = callback.data.split(":", 1)[1]
    filename = export_rating_stats(scope)
    await callback.message.answer_document(FSInputFile(filename), caption=tr(user_id, "📁 Baholash statistikasi Excel fayl ko'rinishida."))
    await callback.answer()


@dp.callback_query(F.data == "admin_reset_confirm")
async def admin_reset_confirm_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    await safe_edit_message(callback, tr(user_id, "⚠️ <b>Diqqat!</b>\n\nBarcha ovozlar o'chiriladi.\nDavom etasizmi?"), reset_confirm_keyboard(user_id, "votes"))
    await callback.answer()


@dp.callback_query(F.data == "admin_reset_ratings_confirm")
async def admin_reset_ratings_confirm_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    await safe_edit_message(callback, tr(user_id, "⚠️ <b>Diqqat!</b>\n\nBarcha like/dislike baholashlar o'chiriladi.\nDavom etasizmi?"), reset_confirm_keyboard(user_id, "ratings"))
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
    await callback.answer(tr(user_id, "Ovozlar reset qilindi!"))


@dp.callback_query(F.data == "admin_reset_ratings")
async def admin_reset_ratings_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(tr(user_id, "Siz admin emassiz."), show_alert=True)
        return
    reset_ratings()
    await safe_edit_message(callback, get_admin_panel_text(user_id), admin_panel_keyboard(user_id))
    await callback.answer(tr(user_id, "Baholashlar reset qilindi!"))

# =========================
# TEXT HANDLER
# =========================
@dp.message(F.text)
async def text_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    if message.text.lower() == "results":
        await message.answer(get_results_menu_text(user_id, False), parse_mode="HTML", reply_markup=results_menu_keyboard_user(user_id))

# =========================
# MAIN
# =========================
async def main():
    init_db()
    logging.info(f"Bot ishga tushdi. Baza: {DB_NAME}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
