import asyncio
import csv
import logging
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
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
BOT_TOKEN = "BOT_TOKENINGIZNI_BU_YERGA_QOYING"
CHANNEL_USERNAME = "@kanal_username"
ADMIN_IDS = [123456789]

TEACHERS = {
    "irisova_sayora": "Irisova Sayora",
    "karimova_umida": "Karimova Umida",
    "razoquva_dilnoza": "Razoquva Dilnoza",
    "sadinova_marjona": "Sadinova Marjona",
}

DB_NAME = "votes.db"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# BAZA
# =========================
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    username TEXT,
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


# =========================
# BAZA YORDAMCHI
# =========================
def ensure_column_exists():
    cursor.execute("PRAGMA table_info(votes)")
    columns = [row[1] for row in cursor.fetchall()]
    if "voted_at" not in columns:
        cursor.execute("ALTER TABLE votes ADD COLUMN voted_at TEXT")
        conn.commit()


def get_setting(key: str, default: str = "") -> str:
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else default


def set_setting(key: str, value: str):
    cursor.execute("""
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()


def init_settings():
    if get_setting("voting_open", "") == "":
        set_setting("voting_open", "1")


ensure_column_exists()
init_settings()


# =========================
# FUNKSIYALAR
# =========================
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


def save_vote(user_id: int, full_name: str, username: str, teacher_key: str):
    cursor.execute("""
        INSERT INTO votes (user_id, full_name, username, teacher_key, voted_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        full_name,
        username,
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


def build_progress_bar(percent: float, length: int = 10) -> str:
    filled = round((percent / 100) * length)
    empty = length - filled
    return "█" * filled + "░" * empty


def get_results_text() -> str:
    total_votes = get_total_votes()
    lines = ["📊 <b>Ovoz berish natijalari</b>\n"]

    for key, name in TEACHERS.items():
        cursor.execute("SELECT COUNT(*) FROM votes WHERE teacher_key = ?", (key,))
        count = cursor.fetchone()[0]
        percent = (count / total_votes * 100) if total_votes > 0 else 0
        bar = build_progress_bar(percent)

        lines.append(
            f"👩‍🏫 <b>{name}</b>\n"
            f"{bar} {percent:.1f}% | {count} ta\n"
        )

    lines.append(f"🗳 <b>Jami ovozlar:</b> {total_votes}")
    lines.append(f"{'🟢' if is_voting_open() else '🔴'} <b>Holat:</b> {'Ochiq' if is_voting_open() else 'Yopiq'}")
    return "\n".join(lines)


def get_users_text() -> str:
    cursor.execute("""
        SELECT user_id, full_name, username, teacher_key, voted_at
        FROM votes
        ORDER BY voted_at DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        return "👥 Hali hech kim ovoz bermagan."

    lines = [f"👥 <b>Kim kimga ovoz berdi</b>\n\nJami: {len(rows)} ta foydalanuvchi\n"]

    for i, row in enumerate(rows, start=1):
        user_id, full_name, username, teacher_key, voted_at = row
        teacher_name = TEACHERS.get(teacher_key, teacher_key)

        line = f"{i}. <b>{full_name or 'Noma’lum'}</b>"
        if username:
            line += f" (@{username})"
        line += f"\n   → {teacher_name}"
        line += f"\n   → ID: <code>{user_id}</code>"
        if voted_at:
            line += f"\n   → {voted_at}"
        lines.append(line)

    text = "\n\n".join(lines)
    if len(text) > 4000:
        return text[:4000] + "\n\n... matn uzun bo‘lgani uchun qisqartirildi"
    return text


def export_votes_to_csv() -> str:
    filename = "votes_export.csv"

    cursor.execute("""
        SELECT user_id, full_name, username, teacher_key, voted_at
        FROM votes
        ORDER BY voted_at DESC
    """)
    rows = cursor.fetchall()

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["User ID", "Full Name", "Username", "Teacher", "Voted At"])

        for user_id, full_name, username, teacher_key, voted_at in rows:
            teacher_name = TEACHERS.get(teacher_key, teacher_key)
            writer.writerow([
                user_id,
                full_name or "",
                username or "",
                teacher_name,
                voted_at or ""
            ])

    return filename


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


# =========================
# KLAVIATURALAR
# =========================
def subscription_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text="📢 Obuna bo‘lish",
            url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
        )
    )
    kb.row(
        InlineKeyboardButton(
            text="✅ Obunani tekshirish",
            callback_data="check_subscription"
        ),
        InlineKeyboardButton(
            text="📊 Natijalar",
            callback_data="show_results"
        )
    )
    return kb.as_markup()


def teachers_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    items = list(TEACHERS.items())
    for i in range(0, len(items), 2):
        row_buttons = []
        for key, name in items[i:i + 2]:
            row_buttons.append(
                InlineKeyboardButton(
                    text=name,
                    callback_data=f"vote:{key}"
                )
            )
        kb.row(*row_buttons)

    kb.row(
        InlineKeyboardButton(
            text="📊 Natijalarni ko‘rish",
            callback_data="show_results"
        )
    )
    return kb.as_markup()


def after_vote_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text="📊 Natijalarni ko‘rish",
            callback_data="show_results"
        )
    )
    kb.row(
        InlineKeyboardButton(
            text="🏠 Bosh menyu",
            callback_data="go_home"
        )
    )
    return kb.as_markup()


def home_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text="🗳 Ovoz berish",
            callback_data="go_vote_panel"
        ),
        InlineKeyboardButton(
            text="📊 Natijalar",
            callback_data="show_results"
        )
    )
    kb.row(
        InlineKeyboardButton(
            text="ℹ️ Yordam",
            callback_data="help_info"
        )
    )
    return kb.as_markup()


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="📊 Results", callback_data="admin_results"),
        InlineKeyboardButton(text="👥 Users", callback_data="admin_users"),
    )
    kb.row(
        InlineKeyboardButton(text="📁 Export", callback_data="admin_export"),
        InlineKeyboardButton(text="♻ Reset", callback_data="admin_reset"),
    )
    kb.row(
        InlineKeyboardButton(text="🔓 Open", callback_data="admin_open"),
        InlineKeyboardButton(text="🔒 Close", callback_data="admin_close"),
    )
    return kb.as_markup()


# =========================
# USER MATNLARI
# =========================
def get_welcome_text() -> str:
    return (
        "🎓 <b>Ovoz berish botiga xush kelibsiz!</b>\n\n"
        "Quyidagi bosqichlarni bajaring:\n"
        "1. Kanalga obuna bo‘ling\n"
        "2. Obunani tasdiqlang\n"
        "3. O‘qituvchini tanlang\n"
        "4. Natijalarni ko‘ring\n\n"
        "👇 Davom etish uchun tugmalardan foydalaning."
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
        "Admin tomonidan ovoz berish vaqtincha to‘xtatilgan.\n"
        "📊 Siz natijalarni ko‘rishingiz mumkin."
    )


def get_vote_select_text() -> str:
    return (
        "🗳 <b>O‘qituvchini tanlang</b>\n\n"
        "Quyidagi nomzodlardan biriga ovoz bering:"
    )


# =========================
# START
# =========================
@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    subscribed = await check_user_subscription(user_id)

    if not subscribed:
        await message.answer(
            get_welcome_text(),
            parse_mode="HTML",
            reply_markup=subscription_keyboard()
        )
        return

    if has_voted(user_id):
        await message.answer(
            get_already_voted_text(),
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )
        return

    if not is_voting_open():
        await message.answer(
            get_closed_text(),
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )
        return

    await message.answer(
        get_vote_select_text(),
        parse_mode="HTML",
        reply_markup=teachers_keyboard()
    )


# =========================
# USER CALLBACKLAR
# =========================
@dp.callback_query(F.data == "go_home")
async def go_home_handler(callback: CallbackQuery):
    await callback.message.answer(
        "🏠 <b>Bosh menyu</b>\n\nKerakli bo‘limni tanlang:",
        parse_mode="HTML",
        reply_markup=home_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "help_info")
async def help_info_handler(callback: CallbackQuery):
    await callback.message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "• Avval kanalga obuna bo‘ling\n"
        "• So‘ng obunani tasdiqlang\n"
        "• Bitta o‘qituvchiga 1 marta ovoz bering\n"
        "• Natijalarni istalgan payt ko‘rishingiz mumkin",
        parse_mode="HTML",
        reply_markup=home_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "go_vote_panel")
async def go_vote_panel_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    subscribed = await check_user_subscription(user_id)

    if not subscribed:
        await callback.message.answer(
            get_welcome_text(),
            parse_mode="HTML",
            reply_markup=subscription_keyboard()
        )
        await callback.answer()
        return

    if has_voted(user_id):
        await callback.message.answer(
            get_already_voted_text(),
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )
        await callback.answer()
        return

    if not is_voting_open():
        await callback.message.answer(
            get_closed_text(),
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )
        await callback.answer()
        return

    await callback.message.answer(
        get_vote_select_text(),
        parse_mode="HTML",
        reply_markup=teachers_keyboard()
    )
    await callback.answer()


# =========================
# OBUNA TEKSHIRISH
# =========================
@dp.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    subscribed = await check_user_subscription(user_id)

    if not subscribed:
        await callback.answer("Siz hali kanalga obuna bo‘lmagansiz.", show_alert=True)
        return

    if has_voted(user_id):
        await callback.message.edit_text(
            get_already_voted_text(),
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )
        await callback.answer()
        return

    if not is_voting_open():
        await callback.message.edit_text(
            get_closed_text(),
            parse_mode="HTML",
            reply_markup=home_keyboard()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "✅ <b>Obuna tasdiqlandi</b>\n\nEndi o‘qituvchini tanlang:",
        parse_mode="HTML",
        reply_markup=teachers_keyboard()
    )
    await callback.answer()


# =========================
# OVOZ BERISH
# =========================
@dp.callback_query(F.data.startswith("vote:"))
async def vote_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    subscribed = await check_user_subscription(user_id)
    if not subscribed:
        await callback.answer("Avval kanalga obuna bo‘ling.", show_alert=True)
        return

    if not is_voting_open():
        await callback.answer("Hozir ovoz berish yopilgan.", show_alert=True)
        return

    if has_voted(user_id):
        await callback.answer("Siz faqat 1 marta ovoz bera olasiz.", show_alert=True)
        return

    teacher_key = callback.data.split(":")[1]
    if teacher_key not in TEACHERS:
        await callback.answer("Noto‘g‘ri tanlov.", show_alert=True)
        return

    full_name = callback.from_user.full_name or "Noma’lum"
    username = callback.from_user.username or ""

    save_vote(user_id, full_name, username, teacher_key)

    await callback.message.edit_text(
        f"✅ <b>Ovoz muvaffaqiyatli qabul qilindi</b>\n\n"
        f"👤 <b>Tanlovingiz:</b> {TEACHERS[teacher_key]}\n\n"
        f"Rahmat, sizning ovozingiz saqlandi.",
        parse_mode="HTML",
        reply_markup=after_vote_keyboard()
    )
    await callback.answer("Ovozingiz qabul qilindi!")


# =========================
# RESULTS
# =========================
@dp.callback_query(F.data == "show_results")
async def show_results_handler(callback: CallbackQuery):
    await callback.message.answer(
        get_results_text(),
        parse_mode="HTML",
        reply_markup=home_keyboard()
    )
    await callback.answer()


@dp.message(Command("results"))
async def results_handler(message: Message):
    await message.answer(
        get_results_text(),
        parse_mode="HTML",
        reply_markup=home_keyboard()
    )


# =========================
# ADMIN BUYRUQLAR
# =========================
@dp.message(Command("admin"))
async def admin_panel_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    status_text = "🟢 Ochiq" if is_voting_open() else "🔴 Yopiq"

    await message.answer(
        f"🎛 <b>Admin panel</b>\n\n"
        f"Voting holati: {status_text}\n"
        f"Jami ovozlar: {get_total_votes()}",
        parse_mode="HTML",
        reply_markup=admin_panel_keyboard()
    )


@dp.message(Command("users"))
async def admin_users_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    await message.answer(get_users_text(), parse_mode="HTML")


@dp.message(Command("export"))
async def admin_export_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    filename = export_votes_to_csv()
    file = FSInputFile(filename)
    await message.answer_document(file, caption="📁 Ovozlar CSV fayl ko‘rinishida.")


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

    reset_votes()
    await message.answer("♻ Barcha ovozlar tozalandi.")


# =========================
# ADMIN CALLBACKLAR
# =========================
@dp.callback_query(F.data == "admin_results")
async def admin_results_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    await callback.message.answer(get_results_text(), parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    await callback.message.answer(get_users_text(), parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "admin_export")
async def admin_export_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    filename = export_votes_to_csv()
    file = FSInputFile(filename)
    await callback.message.answer_document(file, caption="📁 Ovozlar CSV fayl ko‘rinishida.")
    await callback.answer()


@dp.callback_query(F.data == "admin_open")
async def admin_open_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    open_voting()
    await callback.message.answer("🟢 Ovoz berish ochildi.")
    await callback.answer("Voting ochildi!")


@dp.callback_query(F.data == "admin_close")
async def admin_close_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    close_voting()
    await callback.message.answer("🔴 Ovoz berish yopildi.")
    await callback.answer("Voting yopildi!")


@dp.callback_query(F.data == "admin_reset")
async def admin_reset_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return

    reset_votes()
    await callback.message.answer("♻ Barcha ovozlar tozalandi.")
    await callback.answer("Reset qilindi!")


# =========================
# TEXT HANDLER
# =========================
@dp.message(F.text.lower() == "results")
async def text_results_handler(message: Message):
    await message.answer(
        get_results_text(),
        parse_mode="HTML",
        reply_markup=home_keyboard()
    )


# =========================
# MAIN
# =========================
async def main():
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
