import os

import requests
from dotenv import load_dotenv

load_dotenv()


def send_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token is None or chat_id is None:
        print("Нет TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID в .env")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        print("Не удалось отправить сообщение в Telegram.")
        return False
    return True