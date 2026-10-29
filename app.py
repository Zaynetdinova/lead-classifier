# API классификатора заявок (FastAPI)
#
# Запуск:   uvicorn app:app --reload
# Документация (Swagger): http://127.0.0.1:8000/docs
#
# Нужны в .env: ANTHROPIC_API_KEY, API_ACCESS_KEY
# Для уведомлений (notify=true) также: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

import json
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated



from classifier import classify_text
from telegram_utils import send_message

load_dotenv()

API_ACCESS_KEY = os.getenv("API_ACCESS_KEY")
PROCESSED_FILE = Path(__file__).parent / "processed_leads.json"

# Без ключа доступа сервер не запускаем: иначе любой смог бы тратить кредиты Claude
if not API_ACCESS_KEY:
    raise RuntimeError("Не задан API_ACCESS_KEY в .env")

app = FastAPI(title="Классификатор заявок")


# --- Схемы данных ---
class LeadRequest(BaseModel):
    """Что принимает API."""
    text: str = Field(min_length=3, max_length=2000)
    notify: bool = False    # если True и заявка срочная, отправим сообщение в Telegram


class LeadResponse(BaseModel):
    """Что возвращает API."""
    name: str | None = None
    budget: float | None = None
    rooms: int | None = None
    category: str
    urgency: str
    summary: str = ""

class LeadRequest(BaseModel):
    """Что принимает API."""
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=2000)]
    notify: bool = False

# --- Вспомогательные функции ---
def check_key(x_api_key):
    """Проверяет ключ доступа из заголовка X-API-Key."""
    # compare_digest сравнивает за постоянное время, это защищает от подбора по времени ответа
    if x_api_key is None or not secrets.compare_digest(
        x_api_key.encode("utf-8"), API_ACCESS_KEY.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Неверный или отсутствующий ключ доступа")


def read_leads():
    """Читает processed_leads.json. Если файла нет, возвращает пустой список."""
    if not PROCESSED_FILE.exists():
        return []
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Адреса API ---
@app.get("/health")
def health():
    """Проверка, что сервис жив (без ключа)."""
    return {"status": "ok"}


@app.post("/classify", response_model=LeadResponse)
def classify(request: LeadRequest, x_api_key: str | None = Header(default=None)):
    """Разбирает текст заявки и возвращает структурированные данные."""
    check_key(x_api_key)

    lead = classify_text(request.text)
    if lead is None:
        raise HTTPException(status_code=502, detail="Не удалось разобрать заявку")

    # Уведомление только по срочным заявкам, не по спаму
    if request.notify and lead["urgency"] == "high" and lead["category"] != "spam":
        send_message(f"Срочная заявка: {lead.get('summary', '')}")

    return lead


@app.get("/leads")
def get_leads(x_api_key: str | None = Header(default=None)):
    """Возвращает уже обработанные заявки из processed_leads.json."""
    check_key(x_api_key)
    return read_leads()