from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import json
import requests

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# URL для вызова GitHub Actions вручную
GITHUB_API_URL = "https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/workflows/backup.yml/dispatches"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Токен для работы с GitHub API

# Клавиатура с кнопками (убрали кнопку графика)
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("📥 Check in"),
    KeyboardButton("📊 My streak")
).add(
    KeyboardButton("🔝 Top streaks"),
    KeyboardButton("🏆 All-time top"),
)

DATA_FILE = "data.json"

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
    text = f"""Hello, {username}!

I'm Pull-up Tracker Bot 💪
I'll help you track your daily workout progress — globally!

Just press '📥 Check in' after each workout day.

Available options:
📥 Check in — mark today's workout
📊 My streak — show your current streak
🔝 Top streaks — leaderboard by streak
🏆 All-time top — total workouts leaderboard
"""
    await message.reply(text, reply_markup=keyboard)

@dp.message_handler(commands=["turnik"])
async def checkin(message: Message):
    data = load_data()
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.full_name
    now = datetime.now().date()
    now_str = str(now)

    if user_id not in data:
        data[user_id] = {
            "username": username,
            "current_streak": 1,
            "total_days": 1,
            "checkin_dates": [now_str],
            "last_checkin": now_str
        }
        await message.reply(f"{username}, your first day is checked in!", reply_markup=keyboard)
    else:
        user = data[user_id]
        last = datetime.fromisoformat(user["last_checkin"]).date()

        if now == last:
            await message.reply(f"{username}, you've already checked in today!", reply_markup=keyboard)
            return

        if now - last == timedelta(days=1):
            user["current_streak"] += 1
        else:
            user["current_streak"] = 1

        user["total_days"] += 1
        user["last_checkin"] = now_str

        if now_str not in user.get("checkin_dates", []):
            user.setdefault("checkin_dates", []).append(now_str)

        await message.reply(f"{username}, logged! Your streak: {user['current_streak']} days", reply_markup=keyboard)

    save_data(data)

@dp.message_handler(commands=["status"])
async def status(message: Message):
    data = load_data()
    user_id = str(message.from_user.id)

    if user_id in data:
        user = data[user_id]
        await message.reply(
            f"📊 Your streak: {user['current_streak']} days in a row\\nTotal check-ins: {user.get('total_days', 0)}",
            reply_markup=keyboard
        )
    else:
        await message.reply("You haven't checked in yet. Press '📥 Check in'", reply_markup=keyboard)

@dp.message_handler(commands=["leaders"])
async def leaders(message: Message):
    data = load_data()

    leaderboard = sorted(data.items(), key=lambda x: x[1]["current_streak"], reverse=True)
    text = "**🔥 Global Top Current Streaks:**\\n"
    for i, (uid, udata) in enumerate(leaderboard, 1):
        text += f"{i}. @{udata['username']}: {udata['current_streak']} days\\n"

    await message.reply(text, reply_markup=keyboard)

@dp.message_handler(commands=["leaders_all"])
async def leaders_all(message: Message):
    data = load_data()

    leaderboard = sorted(data.items(), key=lambda x: x[1].get("total_days", 0), reverse=True)
    text = "**🏆 Global All-Time Top:**\\n"
    for i, (uid, udata) in enumerate(leaderboard, 1):
        total = udata.get("total_days", 0)
        text += f"{i}. @{udata['username']}: {total} check-ins\\n"

    await message.reply(text, reply_markup=keyboard)

# Function to call GitHub Actions for backup
@dp.message_handler(commands=["save_backup"])
async def save_backup(message: Message):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "ref": "main"
    }

    try:
        response = requests.post(GITHUB_API_URL, json=payload, headers=headers)
        if response.status_code == 201:
            await message.reply("Backup started successfully! 🚀", reply_markup=keyboard)
        else:
            await message.reply(f"Failed to start backup. Error: {response.status_code}", reply_markup=keyboard)
    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}", reply_markup=keyboard)

if __name__ == "__main__":
    executor.start_polling(dp)
"""

with open("/mnt/data/bot.py", "w", encoding="utf-8") as f:
    f.write(corrected_bot_code)

"/mnt/data/bot.py"
