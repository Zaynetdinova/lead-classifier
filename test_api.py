# Тесты API. Claude и Telegram здесь подменены, реальные запросы не уходят.

import json

import pytest
from fastapi.testclient import TestClient

import app as app_module




client = TestClient(app_module.app)
HEADERS = {"X-API-Key": app_module.API_ACCESS_KEY}
GOOD_TEXT = "Здравствуйте, я Анна. Ищу однушку до 6 млн, срочно."



def make_fake_classifier(urgency="high", category="buy"):
    """Делает подмену classify_text, которая возвращает готовый разбор."""
    def fake(text):
        return {
            "name": "Анна",
            "budget": 6000000,
            "rooms": 1,
            "category": category,
            "urgency": urgency,
            "summary": "Тестовая заявка",
        }
    return fake


@pytest.fixture
def sent_messages(monkeypatch):
    """Подменяет send_message и собирает отправленные сообщения в список."""
    messages = []
    monkeypatch.setattr(app_module, "send_message", lambda text: messages.append(text))
    return messages


# --- /health ---
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- ключ доступа ---
def test_classify_without_key_returns_401(monkeypatch):
    def must_not_be_called(text):
        raise AssertionError("Claude не должен вызываться без ключа доступа")

    monkeypatch.setattr(app_module, "classify_text", must_not_be_called)
    response = client.post("/classify", json={"text": GOOD_TEXT})
    assert response.status_code == 401


def test_classify_wrong_key_returns_401(monkeypatch):
    monkeypatch.setattr(app_module, "classify_text", make_fake_classifier())
    response = client.post(
    "/classify", json={"text": GOOD_TEXT}, headers={"X-API-Key": "wrong-key"}
)
    assert response.status_code == 401


# --- проверка входных данных ---
@pytest.mark.parametrize("bad_text", ["", "да", "   ", "  да "])
def test_bad_text_returns_422(bad_text, monkeypatch):
    def must_not_be_called(text):
        raise AssertionError("Claude не должен вызываться на некорректный текст")

    monkeypatch.setattr(app_module, "classify_text", must_not_be_called)
    response = client.post("/classify", json={"text": bad_text}, headers=HEADERS)
    assert response.status_code == 422


def test_missing_text_returns_422():
    response = client.post("/classify", json={}, headers=HEADERS)
    assert response.status_code == 422


# --- основной сценарий ---
def test_classify_ok(monkeypatch):
    monkeypatch.setattr(app_module, "classify_text", make_fake_classifier())
    response = client.post("/classify", json={"text": GOOD_TEXT}, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "buy"
    assert data["urgency"] == "high"


def test_classify_returns_502_when_classifier_fails(monkeypatch):
    monkeypatch.setattr(app_module, "classify_text", lambda text: None)
    response = client.post("/classify", json={"text": GOOD_TEXT}, headers=HEADERS)
    assert response.status_code == 502


# --- уведомления ---
def test_notify_sends_message_for_urgent_lead(monkeypatch, sent_messages):
    monkeypatch.setattr(app_module, "classify_text", make_fake_classifier(urgency="high"))
    client.post("/classify", json={"text": GOOD_TEXT, "notify": True}, headers=HEADERS)
    assert len(sent_messages) == 1


def test_notify_false_does_not_send(monkeypatch, sent_messages):
    monkeypatch.setattr(app_module, "classify_text", make_fake_classifier(urgency="high"))
    client.post("/classify", json={"text": GOOD_TEXT, "notify": False}, headers=HEADERS)
    assert sent_messages == []


def test_notify_does_not_send_for_non_urgent_lead(monkeypatch, sent_messages):
    monkeypatch.setattr(app_module, "classify_text", make_fake_classifier(urgency="low"))
    client.post("/classify", json={"text": GOOD_TEXT, "notify": True}, headers=HEADERS)
    assert sent_messages == []


def test_notify_does_not_send_for_spam(monkeypatch, sent_messages):
    fake = make_fake_classifier(urgency="high", category="spam")
    monkeypatch.setattr(app_module, "classify_text", fake)
    client.post("/classify", json={"text": GOOD_TEXT, "notify": True}, headers=HEADERS)
    assert sent_messages == []

def test_notify_message_contains_summary(monkeypatch, sent_messages):
    monkeypatch.setattr(app_module, "classify_text", make_fake_classifier(urgency="high"))
    client.post("/classify", json={"text": GOOD_TEXT, "notify": True}, headers=HEADERS)
    assert len(sent_messages) == 1
    assert "Тестовая заявка" in sent_messages[0]


# --- /leads ---
def test_leads_requires_key():
    response = client.get("/leads")
    assert response.status_code == 401


def test_leads_empty_when_file_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "PROCESSED_FILE", tmp_path / "нет_такого_файла.json")
    response = client.get("/leads", headers=HEADERS)
    assert response.status_code == 200
    assert response.json() == []


def test_leads_reads_file(monkeypatch, tmp_path):
    leads_file = tmp_path / "leads.json"
    leads_file.write_text(json.dumps([{"id": 1, "category": "buy"}]), encoding="utf-8")
    monkeypatch.setattr(app_module, "PROCESSED_FILE", leads_file)

    response = client.get("/leads", headers=HEADERS)
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "category": "buy"}]