import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


# Статусы событий outbox
class OutboxStatusEnum(StrEnum):
    PENDING = "pending"      # ожидает отправки
    PROCESSED = "processed"  # успешно опубликовано в брокер
    FAILED = "failed"        # не удалось отправить (после retries)


class OutboxEvent(Base):
    __tablename__ = "outbox"

    # Уникальный ID события
    # ВАЖНО: может использоваться как event_id для идемпотентности downstream
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Тип события (например: payment_created, webhook_send)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)

    # Payload события (то, что отправляется в брокер)
    # JSONB позволяет гибко хранить структуру
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Текущий статус обработки outbox события
    status: Mapped[OutboxStatusEnum] = mapped_column(
        Enum(
            OutboxStatusEnum,
            name="outbox_status_enum",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=OutboxStatusEnum.PENDING,
        nullable=False,
    )

    # Количество попыток публикации
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Последняя ошибка при попытке публикации
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Когда событие было успешно отправлено в брокер
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Время создания записи
    # ВАЖНО: используется для порядка обработки (FIFO-ish)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )