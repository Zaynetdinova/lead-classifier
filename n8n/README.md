# Автоматизация в n8n

Два workflow для n8n (проверено на self-hosted, запуск через `npx n8n`):

- `lead-classifier.workflow.json`: принимает заявку по webhook, отправляет её в `/classify`, срочные заявки (не спам) присылает в Telegram. Если API недоступен или вернул ошибку, в Telegram приходит текст заявки, записывает все разобранные заявки в Google Sheets.
- `error-alerts.workflow.json`: срабатывает на сбои основного workflow и присылает в Telegram название workflow, узел и текст ошибки.

## Как подключить

1. Запустите API: `uvicorn app:app --reload`.
2. В n8n: **Workflows → Import from file**, импортируйте оба файла.
3. Создайте credentials:
   - **Telegram API**: токен бота от @BotFather;
   - **Header Auth**: имя заголовка `X-API-Key`, значение равно `API_ACCESS_KEY` из `.env`;
   - **Google Sheets OAuth2 API**: для self-hosted n8n нужно создать своё приложение в Google Cloud Console (включить Google Sheets API и Drive API, создать OAuth client, добавить redirect URL из n8n) и подключить аккаунт.
4. В узлах **HTTP Request** и Telegram выберите свои credentials.
5. Во всех Telegram-узлах замените `YOUR_CHAT_ID` на свой chat id.
6. В основном workflow: меню `...` → **Settings** → **Error Workflow**, выберите «Оповещение об ошибках» (после импорта связь нужно задать заново).
7. Сохраните и включите (Publish) оба workflow.

## Таблица для записи заявок

Создайте Google-таблицу и в первой строке листа впишите заголовки:

`received_at`, `name`, `budget`, `rooms`, `category`, `urgency`, `summary`

В узле «Запись в таблицу» выберите свою таблицу и лист. В таблицу попадают все разобранные заявки, в том числе спам (с `category = spam`).


## Проверка

Тестовый адрес (узел Webhook должен слушать событие):

```
curl -X POST http://localhost:5678/webhook-test/lead \
  -H "Content-Type: application/json" \
  -d '{"text": "Ищу однушку до 6 млн, срочно"}'
```

Рабочий адрес (workflow включён): `http://localhost:5678/webhook/lead`. Результаты запусков смотрите на вкладке **Executions**.

## Замечания

- Если n8n запущен в Docker, API на хосте доступен по адресу `host.docker.internal:8000`, а не `127.0.0.1:8000`.
- Error Workflow срабатывает только на автоматических запусках (не на ручных тестах) и только если запуск завершился ошибкой. Ветка ошибок узла HTTP Request считается обработкой, поэтому после неё стоит узел **Stop and Error**.
- Для входа используется webhook: Telegram Trigger на локальном компьютере не работает без публичного адреса.