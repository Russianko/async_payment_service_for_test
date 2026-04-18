from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class PaymentWebhookEvent(BaseModel):
    # ID платежа (связка с системой)
    payment_id: UUID

    # Статус платежа
    status: str

    # ВАЖНО:
    # amount передается как строка
    # Это правильно для webhook - избегаем проблем с float
    amount: str

    currency: str
    description: str
    metadata: dict

    # Когда платеж был обработан
    processed_at: datetime | None = None

    # Куда отправляется webhook
    webhook_url: HttpUrl

    # Номер попытки доставки
    # Используется для retry логики
    attempt: int = 1