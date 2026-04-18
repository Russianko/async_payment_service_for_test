from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.payment import CurrencyEnum, PaymentStatusEnum


class PaymentCreateRequest(BaseModel):
    # Сумма платежа
    # ВАЖНО:
    # - Decimal используется вместо float (избегаем ошибок округления)
    # - gt=0 - базовая бизнес валидация
    # - decimal_places=2 - ограничение для валют (но в реальности зависит от currency)
    amount: Decimal = Field(..., gt=0, decimal_places=2)

    # Валюта платежа
    currency: CurrencyEnum

    # Описание (например, заказ)
    description: str = Field(..., min_length=1, max_length=1000)

    # Дополнительные данные
    # ВАЖНО: гибкое поле, но в проде часто ограничивается схемой
    metadata: dict[str, Any] = Field(default_factory=dict)

    # URL для webhook
    # HttpUrl уже валидирует формат
    webhook_url: HttpUrl


class PaymentResponse(BaseModel):
    # Минимальный ответ при создании платежа
    payment_id: UUID
    status: str
    created_at: datetime

    # ВАЖНО:
    # Decimal сериализуется в float > возможна потеря точности
    # В проде лучше отдавать строки
    model_config = ConfigDict(
        json_encoders={Decimal: float}
    )


class PaymentDetailResponse(BaseModel):
    # Полный ответ по платежу (source of truth)
    id: UUID
    amount: Decimal
    currency: str
    description: str
    metadata: dict
    status: str
    idempotency_key: str
    webhook_url: str

    # Когда обработан (async слой)
    processed_at: datetime | None

    # Когда создан
    created_at: datetime

    # Те же замечания по Decimal
    model_config = ConfigDict(
        json_encoders={Decimal: float}
    )