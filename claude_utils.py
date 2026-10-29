import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

def ask_claude(prompt, system=None, max_tokens=500):
    """Отправляет запрос Claude. Возвращает текст ответа или None при ошибке."""
    params = {
        "model": "claude-haiku-5-5",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    # system передаём только если он задан
    if system is not None:
        params["system"] = system

    try:
        message = client.messages.create(**params)
    except anthropic.AuthenticationError:
        print("Неверный ключ API (проверь ANTHROPIC_API_KEY в .env).")
        return None
    except anthropic.RateLimitError:
        print("Слишком много запросов, попробуй позже.")
        return None
    except anthropic.APIConnectionError:
        print("Нет соединения с API Claude.")
        return None
    except anthropic.APIStatusError as e:
        print(f"Ошибка API Claude, код {e.status_code}")
        return None

    if message.stop_reason == "max_tokens":
        print("Внимание: ответ Claude обрезан, увеличь max_tokens.")

    # Ответ состоит из блоков разных типов, берём только текстовые
    texts = [block.text for block in message.content if block.type == "text"]

    if not texts:
        print("В ответе Claude нет текста.")
        return None

    return "".join(texts)