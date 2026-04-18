import asyncio
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.broker import broker
from app.core.db import AsyncSessionLocal
from app.models.outbox import OutboxEvent, OutboxStatusEnum


BATCH_SIZE = 50
POLL_INTERVAL = 2  # секунды


async def fetch_pending_events(session: AsyncSession) -> list[OutboxEvent]:
    # Получаем события, которые еще не отправлены
    stmt = (
        select(OutboxEvent)
        .where(OutboxEvent.status == OutboxStatusEnum.PENDING)
        .order_by(OutboxEvent.created_at)
        .limit(BATCH_SIZE)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def mark_processed(session: AsyncSession, event_id):
    # Помечаем событие как успешно отправленное
    stmt = (
        update(OutboxEvent)
        .where(OutboxEvent.id == event_id)
        .values(
            status=OutboxStatusEnum.PROCESSED,
            published_at=datetime.now(timezone.utc),
        )
    )
    await session.execute(stmt)


async def mark_failed(session: AsyncSession, event: OutboxEvent, error: str):
    # Увеличиваем retry_count и сохраняем ошибку
    stmt = (
        update(OutboxEvent)
        .where(OutboxEvent.id == event.id)
        .values(
            retry_count=event.retry_count + 1,
            last_error=error,
        )
    )
    await session.execute(stmt)


async def publish_event(event: OutboxEvent):
    # Публикация события в RabbitMQ
    await broker.publish(
        event.payload,
        queue=event.event_type,
    )


async def run_outbox_relay():
    print("OUTBOX RELAY STARTED")

    while True:
        async with AsyncSessionLocal() as session:
            events = await fetch_pending_events(session)

            if not events:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            for event in events:
                try:
                    await publish_event(event)

                    await mark_processed(session, event.id)

                    print("OUTBOX SENT:", event.id)

                except Exception as e:
                    await mark_failed(session, event, str(e))
                    print("OUTBOX FAILED:", event.id, str(e))

            await session.commit()