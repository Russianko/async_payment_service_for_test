Payment Processing Service
📌 Описание

Сервис обработки платежей с event-driven архитектурой.

Поддерживает:

создание платежей
идемпотентность запросов
асинхронную обработку через очередь
webhook-уведомления
retry и DLQ для доставки webhook
🏗️ Архитектура

Компоненты системы:

API (FastAPI)
Принимает запросы на создание и получение платежей
PostgreSQL
Хранение платежей и outbox событий
RabbitMQ
Очереди для асинхронной обработки и доставки webhook
Consumers (FastStream)
Обрабатывают платежи и webhook события
🔁 Основной flow
Client
  ↓
POST /payments
  ↓
API
  ├─ сохраняет payment в DB
  ├─ сохраняет outbox event
  └─ публикует message → payments.new
  ↓
RabbitMQ
  ↓
payment_consumer
  ├─ обрабатывает платёж (success / fail)
  ├─ обновляет статус в DB
  └─ публикует message → payments.webhook.send
  ↓
webhook_consumer
  ├─ отправляет HTTP webhook
  ├─ при ошибке → retry queue
  └─ после лимита → DLQ
🔌 API
Создание платежа
POST /api/v1/payments

Headers:

X-API-Key: <api_key>
Idempotency-Key: <unique_key>

Body:

{
  "amount": 100.5,
  "currency": "RUB",
  "description": "Test payment",
  "metadata": {
    "order_id": "123"
  },
  "webhook_url": "http://example.com/webhook"
}

Response:

{
  "payment_id": "...",
  "status": "pending",
  "created_at": "..."
}
Получение платежа
GET /api/v1/payments/{id}
🔁 Webhook delivery

После обработки платежа отправляется HTTP callback:

{
  "payment_id": "...",
  "status": "succeeded | failed",
  "amount": "100.50",
  "currency": "RUB",
  "description": "...",
  "metadata": {...},
  "processed_at": "..."
}
🔄 Retry и DLQ

Webhook delivery реализован через отдельный consumer.

Retry политика
до 3 попыток
интервал ≈ 10 секунд (через RabbitMQ TTL)
Очереди
payments.webhook.send — основная очередь доставки
payments.webhook.retry — очередь с задержкой (TTL + DLX)
payments.webhook.dlq — очередь неудачных событий
Поведение
attempt 1 → fail → retry
attempt 2 → fail → retry
attempt 3 → fail → DLQ
🗄️ Модель данных (payments)
поле	описание
id	UUID
amount	сумма
currency	валюта
status	pending / succeeded / failed
idempotency_key	защита от дублей
webhook_url	endpoint
processed_at	время обработки
webhook_attempts	количество попыток
webhook_delivered_at	время успешной доставки
webhook_last_error	последняя ошибка
⚙️ Запуск
Требования
Docker
Docker Compose
Запуск
docker compose up --build -d
Проверка
curl http://127.0.0.1:8000/health
🧪 Примеры тестирования
Успешный webhook
"webhook_url": "http://api:8000/test-webhook"

Ожидается:

webhook доставлен
webhook_attempts = 1
Ошибка webhook (retry + DLQ)
"webhook_url": "http://api:8000/not-found"

Ожидается:

3 попытки доставки
запись в DLQ
webhook_last_error заполнен
⚠️ Ограничения
outbox используется в упрощённом виде (без отдельного relay)
retry фиксированный (без exponential backoff)
нет дедупликации webhook событий
consumers запускаются в одном процессе
📈 Возможные улучшения
полноценный outbox relay
exponential backoff
идемпотентность webhook
раздельные сервисы (payment / webhook)
мониторинг и метрики
circuit breaker для webhook
💬 Итог

Это выглядит как:

не “учебный CRUD”
а реальный backend с очередями, retry и отказоустойчивостью