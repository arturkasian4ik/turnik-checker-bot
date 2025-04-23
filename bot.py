
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import json
import matplotlib.pyplot as plt

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "data.json"

# Клавиатура с кнопками
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("📥 Check in"),
    KeyboardButton("📊 My streak")
).add(
    KeyboardButton("🔝 Top streaks"),
    KeyboardButton("🏆 All-time top"),
    KeyboardButton("📈 Activity graph")
)

@dp.message_handler(lambda message: message.text == "📥 Check in")
async def handle_checkin_button(message: Message):
    await checkin(message)

@dp.message_handler(lambda message: message.text == "📊 My streak")
async def handle_status_button(message: Message):
    await status(message)

@dp.message_handler(lambda message: message.text == "🔝 Top streaks")
async def handle_leaders_button(message: Message):
    await leaders(message)

@dp.message_handler(lambda message: message.text == "🏆 All-time top")
async def handle_leaders_all_button(message: Message):
    await leaders_all(message)

@dp.message_handler(lambda message: message.text == "📈 Activity graph")
async def handle_graph_button(message: Message):
    await graph(message)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@dp.message_handler(commands=["start"])
async def start(message: Message):
    username = message.from_user.username or message.from_user.full_name
    text = f"""Привет, {username}!

Я — Турник-бот 💪
Я помогу тебе отслеживать твои ежедневные занятия.

Просто нажимай кнопку /turnik каждый день после тренировки.
Команды:
📥 /turnik — Отметить день
📊 /status — Твоя серия и прогресс
🔝 /leaders — Рейтинг по текущей серии
🏆 /leaders_all — Рейтинг по всем дням
📈 /graph — График активности
"""
    await message.reply(text, reply_markup=keyboard)

@dp.message_handler(commands=["turnik"])
async def checkin(message: Message):
    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.full_name
    now = datetime.now().date()
    now_str = str(now)

    if chat_id not in data:
        data[chat_id] = {}

    if user_id not in data[chat_id]:
        data[chat_id][user_id] = {
            "username": username,
            "current_streak": 1,
            "total_days": 1,
            "checkin_dates": [now_str],
            "last_checkin": now_str
        }
        await message.reply(f"{username}, твой первый день учтен!", reply_markup=keyboard)
    else:
        user = data[chat_id][user_id]
        last = datetime.fromisoformat(user["last_checkin"]).date()

        if now == last:
            await message.reply(f"{username}, ты уже отмечался сегодня!", reply_markup=keyboard)
            return

        if now - last == timedelta(days=1):
            user["current_streak"] += 1
        else:
            user["current_streak"] = 1

        user["total_days"] += 1
        user["last_checkin"] = now_str

        if "checkin_dates" not in user:
            user["checkin_dates"] = []

        if now_str not in user["checkin_dates"]:
            user["checkin_dates"].append(now_str)

        await message.reply(f"{username}, отмечено! Серия: {user['current_streak']}", reply_markup=keyboard)

    save_data(data)

@dp.message_handler(commands=["status"])
async def status(message: Message):
    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)

    if chat_id in data and user_id in data[chat_id]:
        user = data[chat_id][user_id]
        await message.reply(
            f"📊 Твоя серия: {user['current_streak']} дней подряд\nВсего дней: {user.get('total_days', 0)}",
            reply_markup=keyboard
        )
    else:
        await message.reply("Ты еще не начинал! Напиши /turnik", reply_markup=keyboard)

@dp.message_handler(commands=["leaders"])
async def leaders(message: Message):
    data = load_data()
    chat_id = str(message.chat.id)

    if chat_id not in data:
        await message.reply("Пока никто не начал", reply_markup=keyboard)
        return

    leaderboard = sorted(data[chat_id].items(), key=lambda x: x[1]["current_streak"], reverse=True)
    text = "**🔥 Рейтинг по серии:**\n"
    for i, (uid, udata) in enumerate(leaderboard, 1):
        text += f"{i}. @{udata['username']}: {udata['current_streak']} дней\n"

    await message.reply(text, reply_markup=keyboard)

@dp.message_handler(commands=["leaders_all"])
async def leaders_all(message: Message):
    data = load_data()
    chat_id = str(message.chat.id)

    if chat_id not in data:
        await message.reply("Пока никто не начал", reply_markup=keyboard)
        return

    leaderboard = sorted(data[chat_id].items(), key=lambda x: x[1].get("total_days", 0), reverse=True)
    text = "**🏆 Рейтинг за всё время:**\n"
    for i, (uid, udata) in enumerate(leaderboard, 1):
        total = udata.get("total_days", 0)
        text += f"{i}. @{udata['username']}: {total} дней\n"

    await message.reply(text, reply_markup=keyboard)

@dp.message_handler(commands=["graph"])
async def graph(message: Message):
    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)

    if chat_id not in data or user_id not in data[chat_id]:
        await message.reply("Нет данных для графика. Сначала напиши /turnik.", reply_markup=keyboard)
        return

    user = data[chat_id][user_id]
    dates = user.get("checkin_dates", [])

    if not dates:
        await message.reply("Нет данных для построения графика.", reply_markup=keyboard)
        return

    dates_sorted = sorted(dates)
    date_counts = {}
    for d in dates_sorted:
        date_counts[d] = date_counts.get(d, 0) + 1

    x = list(date_counts.keys())
    y = list(date_counts.values())

    plt.figure(figsize=(8, 4))
    plt.plot(x, y, marker='o')
    plt.xticks(rotation=45, ha='right')
    plt.title("Твоя активность по дням")
    plt.xlabel("Дата")
    plt.ylabel("Занятия")
    plt.tight_layout()

    filename = f"graph_{user_id}.png"
    plt.savefig(filename)
    plt.close()

    photo = InputFile(filename)
    await bot.send_photo(message.chat.id, photo, caption="Вот твой график 💪", reply_markup=keyboard)
    os.remove(filename)

if __name__ == "__main__":
    executor.start_polling(dp)
