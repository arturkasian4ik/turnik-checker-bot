from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiohttp import web
from dotenv import load_dotenv
import os
import json
import requests
from datetime import datetime, timedelta

# Загружаем переменные окружения
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GITHUB_API_URL = "https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/workflows/backup.yml/dispatches"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# URL для Webhook (Render)
WEBHOOK_URL = 'https://turnik-checker-bot.onrender.com/webhook'
PORT = int(os.getenv('PORT', 5000))

# Клавиатура с кнопками
keyboard = InlineKeyboardMarkup(row_width=2)
keyboard.add(
    InlineKeyboardButton("📥 Check in", callback_data="checkin"),
    InlineKeyboardButton("📊 My streak", callback_data="status")
).add(
    InlineKeyboardButton("🔝 Top streaks", callback_data="leaders"),
    InlineKeyboardButton("🏆 All-time top", callback_data="leaders_all")
)

# Файл для хранения данных
DATA_FILE = "data.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

# Загрузка и сохранение данных
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Установка Webhook
async def on_start():
    await bot.set_webhook(WEBHOOK_URL)

# Команда /start
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

# Обработчик для кнопки "Check in"
@dp.callback_query_handler(lambda c: c.data == 'checkin')
async def callback_checkin(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    username = callback_query.from_user.username or callback_query.from_user.full_name
    data = load_data()
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
        await callback_query.message.answer(f"{username}, your first day is checked in!", reply_markup=keyboard)
    else:
        user = data[user_id]
        last = datetime.fromisoformat(user["last_checkin"]).date()

        if now == last:
            await callback_query.message.answer(f"{username}, you've already checked in today!", reply_markup=keyboard)
            return

        if now - last == timedelta(days=1):
            user["current_streak"] += 1
        else:
            user["current_streak"] = 1

        user["total_days"] += 1
        user["last_checkin"] = now_str

        if now_str not in user.get("checkin_dates", []):
            user.setdefault("checkin_dates", []).append(now_str)

        await callback_query.message.answer(f"{username}, logged! Your streak: {user['current_streak']} days", reply_markup=keyboard)

    save_data(data)

# Команда /status
@dp.callback_query_handler(lambda c: c.data == 'status')
async def callback_status(callback_query: types.CallbackQuery):
    data = load_data()
    user_id = str(callback_query.from_user.id)

    if user_id in data:
        user = data[user_id]
        await callback_query.message.answer(
            f"📊 Your streak: {user['current_streak']} days in a row\nTotal check-ins: {user.get('total_days', 0)}",
            reply_markup=keyboard
        )
    else:
        await callback_query.message.answer("You haven't checked in yet. Press '📥 Check in'", reply_markup=keyboard)

# Команда /leaders (Топ по серии)
@dp.callback_query_handler(lambda c: c.data == 'leaders')
async def callback_leaders(callback_query: types.CallbackQuery):
    data = load_data()

    leaderboard = sorted(data.items(), key=lambda x: x[1]["current_streak"], reverse=True)
    text = "**🔥 Global Top Current Streaks:**\n"
    for i, (uid, udata) in enumerate(leaderboard, 1):
        text += f"{i}. @{udata['username']}: {udata['current_streak']} days\n"

    await callback_query.message.answer(text, reply_markup=keyboard)

# Команда /leaders_all (Топ по всем тренировкам)
@dp.callback_query_handler(lambda c: c.data == 'leaders_all')
async def callback_leaders_all(callback_query: types.CallbackQuery):
    data = load_data()

    leaderboard = sorted(data.items(), key=lambda x: x[1].get("total_days", 0), reverse=True)
    text = "**🏆 Global All-Time Top:**\n"
    for i, (uid, udata) in enumerate(leaderboard, 1):
        total = udata.get("total_days", 0)
        text += f"{i}. @{udata['username']}: {total} check-ins\n"

    await callback_query.message.answer(text, reply_markup=keyboard)

# Функция для сохранения данных в GitHub (backup)
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

# Главная функция запуска бота с Webhook
async def main():
    await on_start()  # Устанавливаем webhook
    app = web.Application()
    app.router.add_post('/webhook', dp.start_webhook)  # Обработчик для webhook
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())  # Запускаем сервер на Render
