
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio
import json
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

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

@dp.message_handler(commands=["turnik"])
async def checkin(message: Message):
    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.full_name
    now = datetime.now().date()

    if chat_id not in data:
        data[chat_id] = {}

    if user_id not in data[chat_id]:
        data[chat_id][user_id] = {
            "username": username,
            "current_streak": 1,
            "last_checkin": str(now)
        }
        await message.reply(f"{username}, твой первый день учтен!")
    else:
        last = datetime.fromisoformat(data[chat_id][user_id]["last_checkin"]).date()
        if now == last:
            await message.reply(f"{username}, ты уже отмечался сегодня!")
        elif now - last == timedelta(days=1):
            data[chat_id][user_id]["current_streak"] += 1
            data[chat_id][user_id]["last_checkin"] = str(now)
            await message.reply(f"{username}, молодец! Уже {data[chat_id][user_id]['current_streak']} дней подряд!")
        else:
            data[chat_id][user_id]["current_streak"] = 1
            data[chat_id][user_id]["last_checkin"] = str(now)
            await message.reply(f"{username}, серия сброшена. Начинаем заново!")

    save_data(data)

@dp.message_handler(commands=["status"])
async def status(message: Message):
    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)

    if chat_id in data and user_id in data[chat_id]:
        streak = data[chat_id][user_id]["current_streak"]
        await message.reply(f"Твоя текущая серия: {streak} дней подряд")
    else:
        await message.reply("Ты еще не начинал! Напиши /turnik")

@dp.message_handler(commands=["leaders"])
async def leaders(message: Message):
    data = load_data()
    chat_id = str(message.chat.id)

    if chat_id not in data:
        await message.reply("Пока никто не начал")
        return

    leaderboard = sorted(data[chat_id].items(), key=lambda x: x[1]["current_streak"], reverse=True)
    text = "**Текущий рейтинг:**\n"
    for i, (uid, udata) in enumerate(leaderboard, 1):
        text += f"{i}. @{udata['username']}: {udata['current_streak']} дней\n"

    await message.reply(text)

if __name__ == '__main__':
    executor.start_polling(dp)
