import json
import time
from datetime import datetime, timedelta

DATA_FILE = "data.json"

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def reset_streaks():
    data = load_data()
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    for chat_id in data:
        for user_id, info in data[chat_id].items():
            last_checkin = datetime.fromisoformat(info["last_checkin"]).date()
            if last_checkin < yesterday:
                print(f"Сброшен streak для {info['username']} в чате {chat_id}")
                info["current_streak"] = 0
    save_data(data)

if __name__ == "__main__":
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 1:
            reset_streaks()
            print("Обнуление streak'ов завершено.")
            time.sleep(60)  # Подождать 1 минуту, чтобы не выполнить 2 раза
        time.sleep(30)  # Проверять каждые 30 секунд