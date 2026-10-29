# Тесты чистых функций классификатора. Claude здесь не вызывается.

import pytest

from classifier import parse_json, validate_lead

GOOD = {
    "name": "Анна",
    "budget": 6000000,
    "rooms": 1,
    "category": "buy",
    "urgency": "high",
    "summary": "Ищет однушку до 6 млн",
}


# --- parse_json ---
def test_parse_json_plain():
    assert parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_removes_markdown_wrapper():
    raw = '```json\n{"a": 1}\n```'
    assert parse_json(raw) == {"a": 1}


def test_parse_json_garbage_returns_none():
    assert parse_json("это не JSON") is None


# --- validate_lead ---
def test_validate_good_lead():
    assert validate_lead(GOOD) is True


def test_validate_budget_null_is_ok():
    assert validate_lead({**GOOD, "budget": None}) is True


@pytest.mark.parametrize(
    "field, value",
    [
        ("category", "unknown"),    # такой категории нет
        ("category", None),
        ("urgency", "critical"),    # такой срочности нет
        ("budget", "много"),        # бюджет должен быть числом
    ],
)
def test_validate_bad_values(field, value):
    assert validate_lead({**GOOD, field: value}) is False


@pytest.mark.parametrize("not_a_dict", [None, [], "текст", 42])
def test_validate_not_a_dict(not_a_dict):
    assert validate_lead(not_a_dict) is False

def test_validate_studio_rooms_zero_is_ok():
    # студия записывается как rooms = 0, и это допустимое значение
    assert validate_lead({**GOOD, "rooms": 0}) is True


def test_parse_json_without_closing_backticks():
    # модель иногда открывает блок ```json, но не закрывает его
    raw = '```json\n{"a": 1}'
    assert parse_json(raw) == {"a": 1}