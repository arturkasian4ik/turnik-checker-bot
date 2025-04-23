
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

# English keyboard with human-friendly labels
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(
    KeyboardButton("📥 Check in"),
    KeyboardButton("📊 My streak")
).add(
    KeyboardButton("🔝 Top streaks"),
    KeyboardButton("🏆 All-time top"),
    KeyboardButton("📈 Activity graph")
)

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
📈 Activity graph — your progress graph
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
            f"📊 Your streak: {user['current_streak']} days in a row\nTotal check-ins: {user.get('total_days', 0)}",
            reply_markup=keyboard
        )
    else:
        await message.reply("You haven't checked in yet. Press '📥 Check in'", reply_markup=keyboard)

@dp.message_handler(commands=["leaders"])
async def leaders(message: Message):
    data = load_data()

    leaderboard = sorted(data.items(), key=lambda x: x[1]["current_streak"], reverse=True)
    text = "**🔥 Global Top Current Streaks:**\n"
    for i, (uid, udata) in enumerate(leaderboard, 1):
        text += f"{i}. @{udata['username']}: {udata['current_streak']} days\n"

    await message.reply(text, reply_markup=keyboard)

@dp.message_handler(commands=["leaders_all"])
async def leaders_all(message: Message):
    data = load_data()

    leaderboard = sorted(data.items(), key=lambda x: x[1].get("total_days", 0), reverse=True)
    text = "**🏆 Global All-Time Top:**\n"
    for i, (uid, udata) in enumerate(leaderboard, 1):
        total = udata.get("total_days", 0)
        text += f"{i}. @{udata['username']}: {total} check-ins\n"

    await message.reply(text, reply_markup=keyboard)

@dp.message_handler(commands=["graph"])
async def graph(message: Message):
    data = load_data()
    user_id = str(message.from_user.id)

    if user_id not in data:
        await message.reply("No data to show. Please check in first.", reply_markup=keyboard)
        return

    user = data[user_id]
    dates = user.get("checkin_dates", [])

    if not dates:
        await message.reply("No data to plot.", reply_markup=keyboard)
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
    plt.title("Activity Over Time")
    plt.xlabel("Date")
    plt.ylabel("Check-ins")
    plt.tight_layout()

    filename = f"graph_{user_id}.png"
    plt.savefig(filename)
    plt.close()

    photo = InputFile(filename)
    await bot.send_photo(message.chat.id, photo, caption="Here's your activity graph 💪", reply_markup=keyboard)
    os.remove(filename)

# Button text triggers
@dp.message_handler(lambda message: message.text == "📥 Check in")
async def btn_checkin(message: Message):
    await checkin(message)

@dp.message_handler(lambda message: message.text == "📊 My streak")
async def btn_status(message: Message):
    await status(message)

@dp.message_handler(lambda message: message.text == "🔝 Top streaks")
async def btn_leaders(message: Message):
    await leaders(message)

@dp.message_handler(lambda message: message.text == "🏆 All-time top")
async def btn_leaders_all(message: Message):
    await leaders_all(message)

@dp.message_handler(lambda message: message.text == "📈 Activity graph")
async def btn_graph(message: Message):
    await graph(message)

if __name__ == "__main__":
    executor.start_polling(dp)
