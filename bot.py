import os
import csv
import re
import asyncio
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Tuple

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

# =========================
# SOZLAMALAR
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8760253406:AAFn7DlQEUhKF4LlcAvwI0mjK4Dp_DMdsTE")
CHANNEL_USERNAME = "@QASHQADARYOPMMrasmiy"
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "5298063089,7361393654").split(",") if x.strip().isdigit()]

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
            "tom_1": "Norov Otajon Shomurodovich", "tom_2": "Abdixolikov Abdulazizxon Abduvohob o‘g‘li",
            "tom_3": "Azimova Nigora Anvar qizi", "tom_4": "Abatov Doston Ro‘zimurod o‘g‘li",
            "tom_5": "Jalilova Komila Abdullayevna", "tom_6": "Oqboyeva Zulfiya Bobonazarovna",
            "tom_7": "Sevastyanova Nadejda Aleksandrovna", "tom_8": "Xidirova Feruza To‘rayevna",
            "tom_9": "Ergasheva Dilorom Muradilloyevna",
        },
    },
    "pedagogika_psixologiya_va_talim_menejmenti": {
        "name": "Pedagogika, psixologiya va ta’lim menejmenti",
        "teachers": {
            "pptm_1": "Umarov Lutfillo Murodilloyevich", "pptm_2": "Baratova Nasiba Turobovna",
            "pptm_3": "Bekmurodova Dilnoza Pirimovna", "pptm_4": "Meyliyev Jobar Nurmatovna",
            "pptm_5": "Ochilov Og‘abek Narzullayevich", "pptm_6": "Shoniyozova Dilafruz Sabirovna",
            "pptm_7": "Yaratov Xamidjon Muxtorovich", "pptm_8": "Nazarov Asliddin Faxriddin o‘g‘li",
            "pptm_9": "Ergasheva Dilafruz Ergamqulovna", "pptm_10": "Soatov Asadulloh Jabborovich",
        },
    },
    "aniq_va_tabiiy_fanlar": {
        "name": "Aniq va tabiiy fanlar",
        "teachers": {
            "atf_1": "Jobborov Farhod Bo‘rinevich", "atf_2": "Karimova Habiba Abduraxmonovna",
            "atf_3": "Quldoshova Maftuna Jumanzar qizi", "atf_4": "Mallaev Xamro Ro‘ziboyevich",
            "atf_5": "Mamatov Bekzod Farxotovich", "atf_6": "Pardaeva Muqaddas Zafar qizi",
            "atf_7": "Parmanov Jahongir Rayhonovich", "atf_8": "Rahmatullayev Erkin Shokirovich",
            "atf_9": "Suyarov Zoir Shojmardonovich", "atf_10": "Tursunova Maftuna Sulton qizi",
            "atf_11": "Umarov Ibrohimxon Norxuja o‘g‘li", "atf_12": "Chariev Rashid Ravshanovich",
            "atf_13": "Elmurodov Sherdil Ergashyevich", "atf_14": "Eshmonov Laziz Norxo‘rja o‘g‘li",
            "atf_15": "Karaeva Dilfuzaxon Mamasharipovna", "atf_16": "Salomova Madina Sodiq qizi",
        },
    },
    "amaliy_va_ijtimoiy_fanlar": {
        "name": "Amaliy va ijtimoiy fanlar",
        "teachers": {
            "aif_1": "Yo‘ldashev Bekmirza Elmurodovich", "aif_2": "Jabboborov Laziz Hamza o‘g‘li",
            "aif_3": "Nurmatov Samandar Fayratovich", "aif_4": "Batoshov Inatillo Kungirovich",
            "aif_5": "Rajabov Ruslan Bozorovich", "aif_6": "Sanaev Azamat Alponovich",
            "aif_7": "Shamsiev Jahongir Qulmurod o‘g‘li", "aif_8": "Xudoyberdiev Axrorboy Nabi o‘g‘li",
            "aif_9": "Xasanova Gulnora Qorshanbiyevna", "aif_10": "Eshnazarova Maziya Allanazarovna",
        },
    },
    "maktabgacha_boshlangich_va_maxsus_talim": {
        "name": "Maktabgacha, boshlang‘ich va maxsus ta’lim",
        "teachers": {
            "mbmt_1": "Irisova Sayyora Rajabovna", "mbmt_2": "Azizova Dilnoz Yo‘ldoshevna",
            "mbmt_3": "G‘oyimov Umar Eshmurodovich", "mbmt_4": "Ziyoyeva Madina Mansur qizi",
            "mbmt_5": "Karimova Umida Sharopovna", "mbmt_6": "Qorliyeva Guzal Alimardonovna",
            "mbmt_7": "Qurbanova Xusnora Xudoyberdi qizi", "mbmt_8": "Rajabova Xurshida Hakimovna",
            "mbmt_9": "Razzaqova Dilnoza Akramovna", "mbmt_10": "Sadinova Marjona Akmal qizi",
            "mbmt_11": "Shaxmurodova Dilxaxon Almardanovna", "mbmt_12": "Ergasheva Xusniya Mirzoxid qizi",
            "mbmt_13": "Zaripova Muslima Qurbonovna",
        },
    },
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# =========================
# TRANSLIT
# =========================
def latin_to_cyrillic_text(text: str) -> str:
    if not text: return ""
    for old, new in [("O‘","Ў"),("o‘","ў"),("G‘","Ғ"),("g‘","ғ"),("O'","Ў"),("o'","ў"),("G'","Ғ"),("g'","ғ"),
                     ("Sh","Ш"),("sh","ш"),("Ch","Ч"),("ch","ч"),("Ya","Я"),("ya","я"),("Yo","Ё"),("yo","ё"),
                     ("Yu","Ю"),("yu","ю"),("Ts","Ц"),("ts","ц")]:
        text = text.replace(old, new)
    return text.translate(str.maketrans({
        "A":"А","a":"а","B":"Б","b":"б","D":"Д","d":"д","E":"Е","e":"е","F":"Ф","f":"ф",
        "G":"Г","g":"г","H":"Ҳ","h":"ҳ","I":"И","i":"и","J":"Ж","j":"ж","K":"К","k":"к",
        "L":"Л","l":"л","M":"М","m":"м","N":"Н","n":"н","O":"О","o":"о","P":"П","p":"п",
        "Q":"Қ","q":"қ","R":"Р","r":"р","S":"С","s":"с","T":"Т","t":"т","U":"У","u":"у",
        "V":"В","v":"в","X":"Х","x":"х","Y":"Й","y":"й","Z":"З","z":"з","`":"ъ","’":"ъ","'":"ъ"
    }))

def cyrillic_to_latin_text(text: str) -> str:
    if not text: return ""
    for old, new in [("Ў","O'"),("ў","o'"),("Ғ","G'"),("ғ","g'"),("Ш","Sh"),("ш","sh"),("Ч","Ch"),("ch","ch"),
                     ("Я","Ya"),("ya","ya"),("Ё","Yo"),("ё","yo"),("Ю","Yu"),("ю","yu"),("Ц","Ts"),("ц","ts")]:
        text = text.replace(old, new)
    return text.translate(str.maketrans({
        "А":"A","а":"a","Б":"B","б":"b","Д":"D","д":"d","Е":"E","е":"e","Ф":"F","ф":"f",
        "Г":"G","г":"g","Ҳ":"H","ҳ":"h","И":"I","и":"i","Ж":"J","ж":"j","К":"K","k":"k",
        "Л":"L","l":"l","М":"M","м":"m","Н":"N","n":"n","О":"O","о":"o","П":"P","p":"p",
        "Қ":"Q","q":"q","Р":"R","r":"r","С":"S","s":"s","Т":"T","t":"t","У":"U","u":"u",
        "В":"V","v":"v","Х":"X","x":"x","Й":"Y","й":"y","З":"Z","z":"z","Ъ":"'","ъ":"'"
    }))

def translit_html_safe(text: str, script: str) -> str:
    if not text: return ""
    parts = re.split(r"(<[^>]+>)", text)
    return "".join(part if (part.startswith("<") and part.endswith(">")) else 
                   (latin_to_cyrillic_text(part) if script == "cyrillic" else cyrillic_to_latin_text(part)) for part in parts)

# =========================
# DB HELPERS
# =========================
def init_db():
    cursor.execute("""CREATE TABLE IF NOT EXISTS votes (
        user_id INTEGER PRIMARY KEY, full_name TEXT, username TEXT,
        subject_key TEXT NOT NULL, teacher_key TEXT NOT NULL, voted_at TEXT)""")
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("""CREATE TABLE IF NOT EXISTS user_prefs (
        user_id INTEGER PRIMARY KEY, script TEXT DEFAULT 'latin', access_granted INTEGER DEFAULT 0)""")
    conn.commit()
    if get_setting("voting_open", "") == "": set_setting("voting_open", "1")

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
    return cursor.fetchone()[0] if cursor.fetchone() else "latin"

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

def is_admin(user_id: int) -> bool: return user_id in ADMIN_IDS
def is_voting_open() -> bool: return get_setting("voting_open", "1") == "1"
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
    filled = max(0, min(round((percent / 100) * length), length))
    return "▓" * filled + "░" * (length - filled)

def get_all_teachers_flat():
    return [(sk, tk, tn) for sk, sd in SUBJECTS.items() for tk, tn in sd["teachers"].items()]

# =========================
# OPTIMIZED RESULT FUNCTIONS (1 QUERY ONLY!)
# =========================
def get_vote_counts() -> Dict[Tuple[str, str], int]:
    cursor.execute("SELECT subject_key, teacher_key, COUNT(*) FROM votes GROUP BY subject_key, teacher_key")
    return {(row[0], row[1]): row[2] for row in cursor.fetchall()}

def get_general_results_text(user_id: int) -> str:
    total = get_total_votes()
    counts = get_vote_counts()
    lines = ["📊 <b>Umumiy natijalar</b>\n"]
    for sk, tk, tn in get_all_teachers_flat():
        cnt = counts.get((sk, tk), 0)
        pct = (cnt / total * 100) if total > 0 else 0
        lines.append(f"<b>{tn}</b> — {get_subject_name(sk)}\n<code>{build_progress_bar(pct)}</code>  <b>{pct:.1f}%</b>  •  {cnt} ta\n")
    lines.append(f"🗳 <b>Jami ovozlar:</b> {total}")
    lines.append(f"{'🟢' if is_voting_open() else '🔴'} <b>Holat:</b> {'Ochiq' if is_voting_open() else 'Yopiq'}")
    text = "\n".join(lines)
    return tr(user_id, text[:4000] + ("\n\n... qisqartirildi" if len(text) > 4000 else ""))

def get_subject_results_text(user_id: int, subject_key: str) -> str:
    if subject_key not in SUBJECTS:
        return tr(user_id, "Noto'g'ri fan.")
    total = get_total_votes()
    counts = get_vote_counts()
    lines = [f"📊 <b>{get_subject_name(subject_key)} bo'yicha natijalar</b>\n"]
    for tk, tn in SUBJECTS[subject_key]["teachers"].items():
        cnt = counts.get((subject_key, tk), 0)
        pct = (cnt / total * 100) if total > 0 else 0
        lines.append(f"<b>{tn}</b>\n<code>{build_progress_bar(pct)}</code>  <b>{pct:.1f}%</b>  •  {cnt} ta\n")
    lines.append(f"🗳 <b>Jami ovozlar:</b> {total}")
    lines.append(f"{'🟢' if is_voting_open() else '🔴'} <b>Holat:</b> {'Ochiq' if is_voting_open() else 'Yopiq'}")
    text = "\n".join(lines)
    return tr(user_id, text[:4000] + ("\n\n... qisqartirildi" if len(text) > 4000 else ""))

def get_users_text(user_id: int) -> str:
    cursor.execute("SELECT user_id, full_name, username, subject_key, teacher_key, voted_at FROM votes ORDER BY voted_at DESC")
    rows = cursor.fetchall()
    if not rows: return tr(user_id, "👥 Hali hech kim ovoz bermagan.")
    lines = [f"👥 <b>Kim kimga ovoz berdi</b>\n\nJami: {len(rows)} ta foydalanuvchi\n"]
    for i, (uid, fn, un, sk, tk, va) in enumerate(rows, 1):
        line = f"{i}. <b>{fn or 'Noma''lum'}</b>"
        if un: line += f" (@{un})"
        line += f"\n   → Fan: {get_subject_name(sk)}\n   → O'qituvchi: {get_teacher_name(sk, tk)}\n   → ID: <code>{uid}</code>"
        if va: line += f"\n   → {va}"
        lines.append(line)
    text = "\n\n".join(lines)
    return tr(user_id, text[:4000] + ("\n\n... qisqartirildi" if len(text) > 4000 else ""))

def export_votes_to_csv() -> str:
    cursor.execute("SELECT user_id, full_name, username, subject_key, teacher_key, voted_at FROM votes ORDER BY voted_at DESC")
    rows = cursor.fetchall()
    with open(EXPORT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["User ID", "Full Name", "Username", "Subject", "Teacher", "Voted At"])
        for uid, fn, un, sk, tk, va in rows:
            w.writerow([uid, fn or "", un or "", get_subject_name(sk), get_teacher_name(sk, tk), va or ""])
    return EXPORT_FILE

async def check_user_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in {ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED}
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
        return False

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup | None = None):
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            try:
                await callback.message.answer(text=text, parse_mode="HTML", reply_markup=reply_markup)
            except: pass
    except Exception as e:
        logging.error(f"safe_edit_message error: {e}")
    finally:
        try: await callback.answer()
        except: pass

# =========================
# TEXTS & KEYBOARDS
# =========================
def get_welcome_text(user_id: int) -> str:
    return tr(user_id, "🚀 <b>Botdan foydalanish uchun quyidagilarni bajaring:</b>\n\n1️⃣ 📢 Telegram kanalga obuna bo'ling\n2️⃣ 📘 Facebook sahifaga obuna bo'ling\n3️⃣ 📸 Instagram sahifaga obuna bo'ling\n\n👇 Barchasini bajargach, <b>Tekshirish</b> tugmasini bosing")

def get_home_text(user_id: int) -> str: return tr(user_id, "🏠 <b>Bosh menyu</b>\n\nKerakli bo'limni tanlang:")

def get_help_text(user_id: int) -> str:
    return tr(user_id, "ℹ️ <b>Yordam</b>\n\n• Avval Telegram kanalga obuna bo'ling\n• Facebook sahifaga obuna bo'ling\n• Instagram sahifaga obuna bo'ling\n• So'ng Tekshirish tugmasini bosing\n• Ovoz berish uchun kafedra tanlanadi\n• Keyin o'qituvchi tanlanadi\n• Har bir foydalanuvchi faqat 1 marta ovoz bera oladi\n• Natijalarni istalgan payt ko'rishingiz mumkin")

def get_already_voted_text(user_id: int) -> str: return tr(user_id, "✅ <b>Siz allaqachon ovoz berib bo'lgansiz</b>\n\nQayta ovoz berish mumkin emas.\n📊 Natijalarni ko'rishingiz mumkin.")

def get_closed_text(user_id: int) -> str: return tr(user_id, "🔒 <b>Ovoz berish hozircha yopilgan</b>\n\nAdmin tomonidan ovoz berish vaqtincha to'xtatilgan.")

def get_subject_select_text(user_id: int) -> str: return tr(user_id, "🗂 <b>Kafedrani tanlang</b>\n\nQuyidagi bo'limlardan birini tanlang:")

def get_teacher_select_text(user_id: int, subject_key: str) -> str: return tr(user_id, f"{SUBJECTS[subject_key]['name']}\n\n<b>O'qituvchini tanlang:</b>")

def get_results_menu_text(user_id: int, is_admin: bool = False) -> str:
    title = "Admin natijalar bo'limi" if is_admin else "Natijalar bo'limi"
    return tr(user_id, f"📊 <b>{title}</b>\n\nKerakli bo'limni tanlang:\n• Umumiy natijalar\n• Kafedralar bo'yicha natijalar")

def get_admin_panel_text(user_id: int) -> str:
    status = "🟢 Ochiq" if is_voting_open() else "🔴 Yopiq"
    return tr(user_id, f"🎛 <b>Admin panel</b>\n\nVoting holati: {status}\nJami ovozlar: {get_total_votes()}")

def script_switch_button(user_id: int, page: str = "home") -> InlineKeyboardButton:
    txt = "🔤 Krill" if get_user_script(user_id) == "latin" else "🔤 Lotin"
    new_script = "cyrillic" if get_user_script(user_id) == "latin" else "latin"
    return InlineKeyboardButton(text=txt, callback_data=f"set_script:{new_script}:{page}")

def subscription_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "📢 Telegram kanal"), url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "📘 Facebook sahifa"), url=FACEBOOK_URL))
    kb.row(InlineKeyboardButton(text=tr(user_id, "📸 Instagram sahifa"), url=INSTAGRAM_URL))
    kb.row(InlineKeyboardButton(text=tr(user_id, "✅ Tekshirish"), callback_data="check_subscription"),
           InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user"))
    kb.row(script_switch_button(user_id, "subscription"))
    return kb.as_markup()

def home_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if has_access(user_id):
        kb.row(InlineKeyboardButton(text=tr(user_id, "🗳 Ovoz berish"), callback_data="go_vote_panel"),
               InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user"))
    else:
        kb.row(InlineKeyboardButton(text=tr(user_id, "✅ Obunani tekshirish"), callback_data="check_subscription"),
               InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "ℹ️ Yordam"), callback_data="help_info"),
           script_switch_button(user_id, "home"))
    return kb.as_markup()

def subjects_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for sk, sd in SUBJECTS.items():
        kb.row(InlineKeyboardButton(text=tr(user_id, sd["name"]), callback_data=f"subject:{sk}"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"),
           script_switch_button(user_id, "subjects"))
    return kb.as_markup()

def teachers_keyboard(user_id: int, subject_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    teachers = list(SUBJECTS[subject_key]["teachers"].items())
    for i in range(0, len(teachers), 2):
        kb.row(*[InlineKeyboardButton(text=tr(user_id, tn), callback_data=f"vote:{subject_key}:{tk}") for tk, tn in teachers[i:i+2]])
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Kafedralarga qaytish"), callback_data="go_vote_panel"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"),
           script_switch_button(user_id, f"teachers_{subject_key}"))
    return kb.as_markup()

def results_menu_keyboard_user(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "📊 Umumiy"), callback_data="show_results_user:general"))
    for sk, sd in SUBJECTS.items():
        kb.row(InlineKeyboardButton(text=tr(user_id, sd["name"]), callback_data=f"show_results_user:{sk}"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Orqaga"), callback_data="go_home"),
           script_switch_button(user_id, "user_results_menu"))
    return kb.as_markup()

def results_menu_keyboard_admin(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "📊 Umumiy"), callback_data="show_results_admin:general"))
    for sk, sd in SUBJECTS.items():
        kb.row(InlineKeyboardButton(text=tr(user_id, sd["name"]), callback_data=f"show_results_admin:{sk}"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel"),
           script_switch_button(user_id, "admin_results_menu"))
    return kb.as_markup()

def results_keyboard_user(user_id: int, scope: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "🔄 Yangilash"), callback_data=f"refresh_results_user:{scope}"),
           InlineKeyboardButton(text=tr(user_id, "📂 Bo'limlar"), callback_data="show_results_menu_user"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"),
           script_switch_button(user_id, f"user_result_{scope}"))
    return kb.as_markup()

def results_keyboard_admin(user_id: int, scope: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "🔄 Yangilash"), callback_data=f"refresh_results_admin:{scope}"),
           InlineKeyboardButton(text=tr(user_id, "📂 Bo'limlar"), callback_data="admin_results"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel"),
           script_switch_button(user_id, f"admin_result_{scope}"))
    return kb.as_markup()

def after_vote_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "📊 Natijalar"), callback_data="show_results_menu_user"),
           InlineKeyboardButton(text=tr(user_id, "🏠 Bosh menyu"), callback_data="go_home"))
    kb.row(script_switch_button(user_id, "after_vote"))
    return kb.as_markup()

def admin_panel_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "📊 Results"), callback_data="admin_results"),
           InlineKeyboardButton(text=tr(user_id, "👥 Users"), callback_data="admin_users"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "📁 Export"), callback_data="admin_export"),
           InlineKeyboardButton(text=tr(user_id, "♻ Reset"), callback_data="admin_reset_confirm"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "🔓 Open"), callback_data="admin_open"),
           InlineKeyboardButton(text=tr(user_id, "🔒 Close"), callback_data="admin_close"))
    kb.row(script_switch_button(user_id, "admin_panel"))
    return kb.as_markup()

def reset_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "❌ Bekor qilish"), callback_data="cancel_reset"),
           InlineKeyboardButton(text=tr(user_id, "✅ Ha, o'chirish"), callback_data="admin_reset"))
    kb.row(InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel"),
           script_switch_button(user_id, "admin_reset_confirm"))
    return kb.as_markup()

def users_keyboard_admin(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(user_id, "🔄 Yangilash"), callback_data="refresh_admin_users"),
           InlineKeyboardButton(text=tr(user_id, "⬅️ Admin panel"), callback_data="back_admin_panel"))
    kb.row(script_switch_button(user_id, "admin_users"))
    return kb.as_markup()

# =========================
# HANDLERS
# =========================
@dp.message(Command("start"))
async def start_handler(message: Message):
    uid = message.from_user.id
    ensure_user(uid)
    logging.info(f"START | {uid}")
    if not await check_user_subscription(uid):
        reset_access(uid)
        await message.answer(get_welcome_text(uid), parse_mode="HTML", reply_markup=subscription_keyboard(uid))
        return
    await message.answer(get_home_text(uid) if has_access(uid) else get_welcome_text(uid),
                         parse_mode="HTML", reply_markup=home_keyboard(uid) if has_access(uid) else subscription_keyboard(uid))

@dp.callback_query(F.data.startswith("set_script:"))
async def set_script_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    parts = callback.data.split(":", 2)
    if len(parts) < 2: 
        await callback.answer("Xato", show_alert=True)
        return
    script, page = parts[1], parts[2] if len(parts) > 2 else "home"
    if script not in ("latin", "cyrillic"):
        await callback.answer("Xato", show_alert=True)
        return
    set_user_script(uid, script)
    logging.info(f"SCRIPT | {uid} → {script} | page={page}")
    try:
        if page == "subscription":
            await safe_edit_message(callback, get_welcome_text(uid), subscription_keyboard(uid))
        elif page == "admin_panel":
            await safe_edit_message(callback, get_admin_panel_text(uid), admin_panel_keyboard(uid))
        elif page == "admin_results_menu":
            await safe_edit_message(callback, get_results_menu_text(uid, True), results_menu_keyboard_admin(uid))
        elif page.startswith("admin_result_"):
            scope = page.replace("admin_result_", "", 1)
            txt = get_general_results_text(uid) if scope == "general" else get_subject_results_text(uid, scope)
            await safe_edit_message(callback, txt, results_keyboard_admin(uid, scope))
        elif page == "admin_users":
            await safe_edit_message(callback, get_users_text(uid), users_keyboard_admin(uid))
        elif page == "admin_reset_confirm":
            await safe_edit_message(callback, tr(uid, "⚠️ <b>Diqqat!</b>\n\nBarcha ovozlar o'chiriladi.\nDavom etasizmi?"), reset_confirm_keyboard(uid))
        elif page == "user_results_menu":
            await safe_edit_message(callback, get_results_menu_text(uid, False), results_menu_keyboard_user(uid))
        elif page.startswith("user_result_"):
            scope = page.replace("user_result_", "", 1)
            txt = get_general_results_text(uid) if scope == "general" else get_subject_results_text(uid, scope)
            await safe_edit_message(callback, txt, results_keyboard_user(uid, scope))
        elif page == "subjects":
            await safe_edit_message(callback, get_subject_select_text(uid), subjects_keyboard(uid))
        elif page.startswith("teachers_"):
            sk = page.replace("teachers_", "", 1)
            if sk in SUBJECTS:
                await safe_edit_message(callback, get_teacher_select_text(uid, sk), teachers_keyboard(uid, sk))
            else:
                await safe_edit_message(callback, get_home_text(uid), home_keyboard(uid))
        elif page == "after_vote":
            await safe_edit_message(callback, get_already_voted_text(uid), home_keyboard(uid))
        elif page == "help":
            kb = InlineKeyboardBuilder()
            kb.row(InlineKeyboardButton(text=tr(uid, "⬅️ Orqaga"), callback_data="go_home"))
            kb.row(script_switch_button(uid, "help"))
            await safe_edit_message(callback, get_help_text(uid), kb.as_markup())
        else:
            await safe_edit_message(callback, get_home_text(uid) if has_access(uid) else get_welcome_text(uid),
                                    home_keyboard(uid) if has_access(uid) else subscription_keyboard(uid))
    except Exception as e:
        logging.error(f"set_script error: {e}")
        await callback.answer("Xatolik", show_alert=True)

@dp.callback_query(F.data == "go_home")
async def go_home_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    ensure_user(uid)
    await safe_edit_message(callback, get_home_text(uid) if has_access(uid) else get_welcome_text(uid),
                            home_keyboard(uid) if has_access(uid) else subscription_keyboard(uid))

@dp.callback_query(F.data == "help_info")
async def help_info_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    ensure_user(uid)
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=tr(uid, "⬅️ Orqaga"), callback_data="go_home"))
    kb.row(script_switch_button(uid, "help"))
    await safe_edit_message(callback, get_help_text(uid), kb.as_markup())

@dp.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    ensure_user(uid)
    if not await check_user_subscription(uid):
        reset_access(uid)
        await callback.answer(get_subscription_required_alert(uid) if 'get_subscription_required_alert' in globals() else "Obuna bo'ling!", show_alert=True)
        return
    grant_access(uid)
    await safe_edit_message(callback, tr(uid, "✅ <b>Tekshiruv muvaffaqiyatli o'tdi</b>\n\nEndi bosh menyudan kerakli bo'limni tanlang:"), home_keyboard(uid))

@dp.callback_query(F.data == "go_vote_panel")
async def go_vote_panel_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    ensure_user(uid)
    if not has_access(uid) or not await check_user_subscription(uid):
        await safe_edit_message(callback, get_welcome_text(uid), subscription_keyboard(uid))
        await callback.answer("Obuna bo'ling!", show_alert=True)
        return
    if has_voted(uid):
        await safe_edit_message(callback, get_already_voted_text(uid), home_keyboard(uid))
        return
    if not is_voting_open():
        await safe_edit_message(callback, get_closed_text(uid), home_keyboard(uid))
        return
    await safe_edit_message(callback, get_subject_select_text(uid), subjects_keyboard(uid))

@dp.callback_query(F.data.startswith("subject:"))
async def subject_select_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    ensure_user(uid)
    if not has_access(uid) or not await check_user_subscription(uid) or has_voted(uid) or not is_voting_open():
        await safe_edit_message(callback, get_home_text(uid), home_keyboard(uid))
        return
    sk = callback.data.split(":")[1]
    if sk not in SUBJECTS:
        await callback.answer(tr(uid, "Noto'g'ri bo'lim"), show_alert=True)
        return
    await safe_edit_message(callback, get_teacher_select_text(uid, sk), teachers_keyboard(uid, sk))

@dp.callback_query(F.data.startswith("vote:"))
async def vote_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    ensure_user(uid)
    if not has_access(uid) or not await check_user_subscription(uid) or not is_voting_open() or has_voted(uid):
        await callback.answer(tr(uid, "Ovoz berish mumkin emas"), show_alert=True)
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer(tr(uid, "Noto'g'ri tanlov"), show_alert=True)
        return
    _, sk, tk = parts
    if sk not in SUBJECTS or tk not in SUBJECTS[sk]["teachers"]:
        await callback.answer(tr(uid, "Noto'g'ri tanlov"), show_alert=True)
        return
    save_vote(uid, callback.from_user.full_name or "Noma'lum", callback.from_user.username or "", sk, tk)
    txt = f"✅ <b>Ovoz muvaffaqiyatli qabul qilindi</b>\n\n<b>Bo'lim:</b> {SUBJECTS[sk]['name']}\n<b>Tanlovingiz:</b> {SUBJECTS[sk]['teachers'][tk]}\n\nRahmat!"
    await safe_edit_message(callback, tr(uid, txt), after_vote_keyboard(uid))

# RESULTS
@dp.callback_query(F.data == "show_results_menu_user")
async def show_results_menu_user(callback: CallbackQuery):
    uid = callback.from_user.id
    ensure_user(uid)
    await safe_edit_message(callback, get_results_menu_text(uid, False), results_menu_keyboard_user(uid))

@dp.callback_query(F.data.startswith("show_results_user:"))
async def show_results_user(callback: CallbackQuery):
    uid = callback.from_user.id
    ensure_user(uid)
    logging.info(f"RESULTS USER | {uid} | {callback.data}")
    scope = callback.data.split(":", 1)[1]
    txt = get_general_results_text(uid) if scope == "general" else get_subject_results_text(uid, scope)
    await safe_edit_message(callback, txt, results_keyboard_user(uid, scope))

@dp.callback_query(F.data.startswith("refresh_results_user:"))
async def refresh_results_user(callback: CallbackQuery):
    uid = callback.from_user.id
    ensure_user(uid)
    scope = callback.data.split(":", 1)[1]
    txt = get_general_results_text(uid) if scope == "general" else get_subject_results_text(uid, scope)
    await safe_edit_message(callback, txt, results_keyboard_user(uid, scope))

@dp.message(Command("results"))
async def results_handler(message: Message):
    uid = message.from_user.id
    ensure_user(uid)
    await message.answer(get_results_menu_text(uid, False), parse_mode="HTML", reply_markup=results_menu_keyboard_user(uid))

# ADMIN
@dp.message(Command("admin"))
async def admin_panel_handler(message: Message):
    uid = message.from_user.id
    ensure_user(uid)
    if not is_admin(uid):
        await message.answer(tr(uid, "Siz admin emassiz."))
        return
    await message.answer(get_admin_panel_text(uid), parse_mode="HTML", reply_markup=admin_panel_keyboard(uid))

@dp.message(Command("users"))
async def admin_users_handler(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        await message.answer(tr(uid, "Siz admin emassiz."))
        return
    await message.answer(get_users_text(uid), parse_mode="HTML", reply_markup=users_keyboard_admin(uid))

@dp.message(Command("export"))
async def admin_export_handler(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        await message.answer(tr(uid, "Siz admin emassiz."))
        return
    await message.answer_document(FSInputFile(export_votes_to_csv()), caption=tr(uid, "📁 Ovozlar CSV fayl"))

@dp.message(Command("open"))
async def admin_open_handler(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        await message.answer(tr(uid, "Siz admin emassiz."))
        return
    open_voting()
    await message.answer(tr(uid, "🟢 Ovoz berish ochildi."))

@dp.message(Command("close"))
async def admin_close_handler(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        await message.answer(tr(uid, "Siz admin emassiz."))
        return
    close_voting()
    await message.answer(tr(uid, "🔴 Ovoz berish yopildi."))

@dp.message(Command("reset_votes"))
async def admin_reset_handler(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        await message.answer(tr(uid, "Siz admin emassiz."))
        return
    await message.answer(tr(uid, "⚠️ <b>Diqqat!</b>\n\nBarcha ovozlar o'chiriladi.\nDavom etasizmi?"),
                         parse_mode="HTML", reply_markup=reset_confirm_keyboard(uid))

@dp.callback_query(F.data == "back_admin_panel")
async def back_admin_panel(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    await safe_edit_message(callback, get_admin_panel_text(uid), admin_panel_keyboard(uid))

@dp.callback_query(F.data == "admin_results")
async def admin_results(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    await safe_edit_message(callback, get_results_menu_text(uid, True), results_menu_keyboard_admin(uid))

@dp.callback_query(F.data.startswith("show_results_admin:"))
async def show_results_admin(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    scope = callback.data.split(":", 1)[1]
    txt = get_general_results_text(uid) if scope == "general" else get_subject_results_text(uid, scope)
    await safe_edit_message(callback, txt, results_keyboard_admin(uid, scope))

@dp.callback_query(F.data.startswith("refresh_results_admin:"))
async def refresh_results_admin(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    scope = callback.data.split(":", 1)[1]
    txt = get_general_results_text(uid) if scope == "general" else get_subject_results_text(uid, scope)
    await safe_edit_message(callback, txt, results_keyboard_admin(uid, scope))

@dp.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    await safe_edit_message(callback, get_users_text(uid), users_keyboard_admin(uid))

@dp.callback_query(F.data == "refresh_admin_users")
async def refresh_admin_users(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    await safe_edit_message(callback, get_users_text(uid), users_keyboard_admin(uid))

@dp.callback_query(F.data == "admin_export")
async def admin_export(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    await callback.message.answer_document(FSInputFile(export_votes_to_csv()), caption=tr(uid, "📁 Ovozlar CSV fayl"))
    await callback.answer()

@dp.callback_query(F.data == "admin_open")
async def admin_open(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    open_voting()
    await safe_edit_message(callback, get_admin_panel_text(uid), admin_panel_keyboard(uid))
    await callback.answer(tr(uid, "Voting ochildi!"))

@dp.callback_query(F.data == "admin_close")
async def admin_close(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    close_voting()
    await safe_edit_message(callback, get_admin_panel_text(uid), admin_panel_keyboard(uid))
    await callback.answer(tr(uid, "Voting yopildi!"))

@dp.callback_query(F.data == "admin_reset_confirm")
async def admin_reset_confirm(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    await safe_edit_message(callback, tr(uid, "⚠️ <b>Diqqat!</b>\n\nBarcha ovozlar o'chiriladi.\nDavom etasizmi?"), reset_confirm_keyboard(uid))

@dp.callback_query(F.data == "cancel_reset")
async def cancel_reset(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    await safe_edit_message(callback, get_admin_panel_text(uid), admin_panel_keyboard(uid))
    await callback.answer(tr(uid, "Bekor qilindi"))

@dp.callback_query(F.data == "admin_reset")
async def admin_reset(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer(tr(uid, "Siz admin emassiz."), show_alert=True)
        return
    reset_votes()
    await safe_edit_message(callback, get_admin_panel_text(uid), admin_panel_keyboard(uid))
    await callback.answer(tr(uid, "Reset qilindi!"))

@dp.message(F.text)
async def text_handler(message: Message):
    uid = message.from_user.id
    ensure_user(uid)
    if message.text.lower() == "results":
        await message.answer(get_results_menu_text(uid, False), parse_mode="HTML", reply_markup=results_menu_keyboard_user(uid))

# =========================
# MAIN
# =========================
async def main():
    init_db()
    logging.info("✅ Bot V3 ishga tushdi | OPTIMIZED + ALL BUGS FIXED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
