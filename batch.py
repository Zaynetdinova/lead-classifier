# Пакетная обработка заявок: data/inbox.json -> processed_leads.json
import json
from pathlib import Path

import pandas as pd

from classifier import classify_text
from telegram_utils import send_message

BASE_DIR = Path(__file__).parent
INBOX_FILE = BASE_DIR / "data" / "inbox.json"
PROCESSED_FILE = BASE_DIR / "processed_leads.json"


def load_json_list(path):
    """Читает список из JSON-файла. Если файла нет, возвращает пустой список."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_summary(leads, failed_count):
    """Собирает текст сводки по новым заявкам. Возвращает текст и таблицу без спама."""
    df = pd.DataFrame(leads)
    real = df[df["category"] != "spam"]

    lines = [
        f"Новых заявок: {len(df)} (спам: {len(df) - len(real)}, не разобрано: {failed_count})",
        "",
        "По категориям:",
    ]
    for category, count in real["category"].value_counts().items():
        lines.append(f"  {category}: {count}")

    lines.append("")
    lines.append(f"Срочных: {(real['urgency'] == 'high').sum()}")
    if "budget" in real and real["budget"].notna().any():
        lines.append(f"Средний бюджет: {real['budget'].mean():,.0f} ₽".replace(",", " "))

    return "\n".join(lines), real


def main():
    inbox = load_json_list(INBOX_FILE)
    if not inbox:
        print(f"Нет заявок в {INBOX_FILE}")
        return

    processed = load_json_list(PROCESSED_FILE)

    # Защита от повторной обработки: пропускаем заявки, id которых уже есть в результатах
    processed_ids = {lead["id"] for lead in processed}
    new_items = [item for item in inbox if item["id"] not in processed_ids]
    print(f"Всего: {len(inbox)}, уже обработано: {len(inbox) - len(new_items)}, новых: {len(new_items)}")

    if not new_items:
        print("Новых заявок нет.")
        return

    new_leads = []
    failed_ids = []

    for item in new_items:
        lead = classify_text(item["text"])

        if lead is None:
            failed_ids.append(item["id"])
            print(f"Заявка #{item['id']} не разобрана")
            send_message(f"Заявка #{item['id']} не разобрана, проверь вручную.")
            continue

        lead["id"] = item["id"]
        lead["source"] = item["source"]
        new_leads.append(lead)

    # Неразобранные заявки в файл не попадают: при следующем запуске скрипт попробует их снова
    processed.extend(new_leads)
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    if not new_leads:
        print("Ни одну новую заявку разобрать не удалось.")
        return

    summary, real = build_summary(new_leads, len(failed_ids))
    send_message(summary)

    for _, lead in real[real["urgency"] == "high"].iterrows():
        send_message(f"Срочная заявка #{lead['id']}: {lead['summary']}")

    print("Готово")


if __name__ == "__main__":
    main()