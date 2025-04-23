
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import json

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
            "total_days": 1,
            "last_checkin": str(now)
        }
        await message.reply(f"{username}, твой первый день учтен!")
    else:
        last = datetime.fromisoformat(data[chat_id][user_id]["last_checkin"]).date()
        if now == last:
            await message.reply(f"{username}, ты уже отмечался сегодня!")
        elif now - last == timedelta(days=1):
            data[chat_id][user_id]["current_streak"] += 1
            data[chat_id][user_id]["total_days"] += 1
            data[chat_id][user_id]["last_checkin"] = str(now)
            await message.reply(f"{username}, молодец! Уже {data[chat_id][user_id]['current_streak']} дней подряд!")
        else:
            data[chat_id][user_id]["current_streak"] = 1
            data[chat_id][user_id]["total_days"] += 1
            data[chat_id][user_id]["last_checkin"] = str(now)
            await message.reply(f"{username}, серия сброшена. Начинаем заново!")

    save_data(data)

@dp.message_handler(commands=["status"])
async def status(message: Message):
    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)

    if chat_id in data and user_id in data[chat_id]:
        user = data[chat_id][user_id]
        await message.reply(f"📊 Твоя серия: {user['current_streak']} дней подряд\nВсего дней: {user.get('total_days', 0)}")
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
    text = "**🔥 Рейтинг по серии:**\n"
    for i, (uid, udata) in enumerate(leaderboard, 1):
        text += f"{i}. @{udata['username']}: {udata['current_streak']} дней\n"

    await message.reply(text)

@dp.message_handler(commands=["leaders_all"])
async def leaders_all(message: Message):
    data = load_data()
    chat_id = str(message.chat.id)

    if chat_id not in data:
        await message.reply("Пока никто не начал")
        return

    leaderboard = sorted(data[chat_id].items(), key=lambda x: x[1].get("total_days", 0), reverse=True)
    text = "**🏆 Рейтинг за всё время:**\n"
    for i, (uid, udata) in enumerate(leaderboard, 1):
        total = udata.get("total_days", 0)
        text += f"{i}. @{udata['username']}: {total} дней\n"

    await message.reply(text)

if __name__ == "__main__":
    executor.start_polling(dp)
