import asyncio
import logging
import sqlite3
import os

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# =========================
# SOZLAMALAR
# =========================
BOT_TOKEN = "8760253406:AAFn7DlQEUhKF4LlcAvwI0mjK4Dp_DMdsTE"
CHANNEL_USERNAME = "@botuchun10"   # masalan: @my_channel
ADMIN_IDS = [5298063089]  # bu yerga admin telegram id yoziladi

TEACHERS = {
    "irisova_sayora": "Irisova Sayora",
    "karimova_umida": "Karimova Umida",
    "razoquva_dilnoza": "Razoquva Dilnoza",
    "sadinova_marjona": "Sadinova Marjona",
}

DB_NAME = "votes.db"

# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)

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
    teacher_key TEXT NOT NULL
)
""")
conn.commit()

# =========================
# BOT
# =========================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================
# KLAVIATURALAR
# =========================
def subscription_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(
            text="📢 Kanalga obuna bo‘lish",
            url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
        )
    )
    kb.row(
        InlineKeyboardButton(
            text="✅ Obunani tekshirish",
            callback_data="check_subscription"
        )
    )
    kb.row(
        InlineKeyboardButton(
            text="📊 Results",
            callback_data="show_results"
        )
    )

    return kb.as_markup()


def teachers_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for key, name in TEACHERS.items():
        kb.row(
            InlineKeyboardButton(
                text=name,
                callback_data=f"vote:{key}"
            )
        )

    kb.row(
        InlineKeyboardButton(
            text="📊 Results",
            callback_data="show_results"
        )
    )

    return kb.as_markup()


# =========================
# YORDAMCHI FUNKSIYALAR
# =========================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def has_voted(user_id: int) -> bool:
    cursor.execute("SELECT 1 FROM votes WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None


def save_vote(user_id: int, full_name: str, username: str, teacher_key: str):
    cursor.execute(
        """
        INSERT INTO votes (user_id, full_name, username, teacher_key)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, full_name, username, teacher_key)
    )
    conn.commit()


def get_total_votes() -> int:
    cursor.execute("SELECT COUNT(*) FROM votes")
    return cursor.fetchone()[0]


def get_results_text() -> str:
    total_votes = get_total_votes()

    lines = ["📊 Ovoz berish natijalari:\n"]

    for key, name in TEACHERS.items():
        cursor.execute(
            "SELECT COUNT(*) FROM votes WHERE teacher_key = ?",
            (key,)
        )
        count = cursor.fetchone()[0]
        percent = (count / total_votes * 100) if total_votes > 0 else 0
        lines.append(f"• {name}: {count} ta ovoz — {percent:.1f}%")

    lines.append(f"\nJami ovozlar: {total_votes}")
    return "\n".join(lines)


def get_users_text() -> str:
    cursor.execute("""
        SELECT user_id, full_name, username, teacher_key
        FROM votes
        ORDER BY rowid DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        return "Hali hech kim ovoz bermagan."

    lines = [f"👥 Ovoz bergan foydalanuvchilar soni: {len(rows)}\n"]

    for i, row in enumerate(rows, start=1):
        user_id, full_name, username, teacher_key = row
        teacher_name = TEACHERS.get(teacher_key, teacher_key)

        user_line = f"{i}. {full_name or 'Noma’lum'}"
        if username:
            user_line += f" (@{username})"
        user_line += f" → {teacher_name}"
        user_line += f" | ID: {user_id}"

        lines.append(user_line)

    text = "\n".join(lines)

    # Telegram xabar limiti sababli bo‘lib yuborish mumkin
    if len(text) > 4000:
        return text[:4000] + "\n\n... davom etadi"

    return text


def reset_votes():
    cursor.execute("DELETE FROM votes")
    conn.commit()


async def check_user_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in {
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        }
    except Exception as e:
        logging.error(f"Subscription tekshirishda xatolik: {e}")
        return False


# =========================
# HANDLERLAR
# =========================
@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id

    subscribed = await check_user_subscription(user_id)

    if not subscribed:
        await message.answer(
            "Assalomu alaykum.\n\n"
            "Botdan foydalanish uchun avval kanalga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )
        return

    if has_voted(user_id):
        await message.answer(
            "Siz allaqachon ovoz berib bo‘lgansiz.\n\n"
            "Natijalarni ko‘rish uchun pastdagi tugmadan foydalaning.",
            reply_markup=teachers_keyboard()
        )
        return

    await message.answer(
        "Quyidagi o‘qituvchilardan birini tanlang:",
        reply_markup=teachers_keyboard()
    )


@dp.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    subscribed = await check_user_subscription(user_id)

    if not subscribed:
        await callback.answer("Siz hali kanalga obuna bo‘lmagansiz.", show_alert=True)
        return

    if has_voted(user_id):
        await callback.message.edit_text(
            "Obuna tasdiqlandi ✅\n\n"
            "Siz allaqachon ovoz berib bo‘lgansiz.",
            reply_markup=teachers_keyboard()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "Obuna tasdiqlandi ✅\n\n"
        "Endi o‘qituvchilardan birini tanlang:",
        reply_markup=teachers_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("vote:"))
async def vote_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    subscribed = await check_user_subscription(user_id)
    if not subscribed:
        await callback.answer("Avval kanalga obuna bo‘ling.", show_alert=True)
        return

    if has_voted(user_id):
        await callback.answer("Siz faqat 1 marta ovoz bera olasiz.", show_alert=True)
        return

    teacher_key = callback.data.split(":")[1]

    if teacher_key not in TEACHERS:
        await callback.answer("Noto‘g‘ri tanlov.", show_alert=True)
        return

    full_name = callback.from_user.full_name
    username = callback.from_user.username if callback.from_user.username else ""

    save_vote(user_id, full_name, username, teacher_key)

    await callback.message.edit_text(
        f"✅ Siz {TEACHERS[teacher_key]} uchun ovoz berdingiz.\n\nRahmat!"
    )
    await callback.answer("Ovozingiz qabul qilindi!")


@dp.callback_query(F.data == "show_results")
async def show_results_handler(callback: CallbackQuery):
    await callback.message.answer(get_results_text())
    await callback.answer()


@dp.message(Command("results"))
async def admin_results_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    await message.answer(get_results_text())


@dp.message(Command("users"))
async def admin_users_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    await message.answer(get_users_text())


@dp.message(Command("reset_votes"))
async def admin_reset_votes_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Siz admin emassiz.")
        return

    reset_votes()
    await message.answer("✅ Barcha ovozlar tozalandi.")


@dp.message(F.text.lower() == "results")
async def text_results_handler(message: Message):
    await message.answer(get_results_text())


# =========================
# MAIN
# =========================
async def main():
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())