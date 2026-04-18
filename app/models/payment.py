import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Numeric, String, Text, func, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


# Поддерживаемые валюты
class CurrencyEnum(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


# Статусы платежа
class PaymentStatusEnum(StrEnum):
    PENDING = "pending"     # создан, но не обработан
    SUCCEEDED = "succeeded" # успешно обработан
    FAILED = "failed"       # ошибка обработки


class Payment(Base):
    __tablename__ = "payments"

    # Уникальный ID платежа
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Сумма платежа
    # Numeric(12,2) - стандарт для денег (без float!)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Валюта платежа
    currency: Mapped[CurrencyEnum] = mapped_column(
        Enum(
            CurrencyEnum,
            name="currency_enum",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )

    # Описание (например: заказ, услуга и т.д.)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Дополнительные данные (гибкое поле)
    payment_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    # Статус платежа (жизненный цикл)
    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(
            PaymentStatusEnum,
            name="payment_status_enum",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=PaymentStatusEnum.PENDING,
        nullable=False,
    )

    # Ключ идемпотентности
    # ВАЖНО:
    # - уникальный
    # - защищает от повторных POST запросов
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # URL для webhook callback
    webhook_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Когда платеж был обработан (consumer)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Время создания
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Количество попыток отправки webhook
    webhook_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Когда webhook был успешно доставлен
    webhook_delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Последняя ошибка webhook
    webhook_last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )