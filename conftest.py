# Настройка тестов (pytest подхватывает этот файл автоматически)
#
# Эти переменные задаются ДО импорта app.py, чтобы сервер в тестах стартовал
# с тестовым ключом и никогда не использовал настоящие ключи.

import os

os.environ["API_ACCESS_KEY"] = "test-key"
os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-a-real-key")