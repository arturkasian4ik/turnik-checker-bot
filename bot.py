from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InputFile
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
