from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import OutboxEvent


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        # Репозиторий outbox работает в той же транзакции, что и бизнес-операция
        # Это ключ к transactional outbox паттерну
        self.session = session

    async def add(self, outbox_event: OutboxEvent) -> OutboxEvent:
        # Добавление события в outbox таблицу
        # ВАЖНО:
        # - событие сохраняется в той же транзакции, что и payment
        # - публикация в брокер происходит позже (через relay)
        self.session.add(outbox_event)

        await self.session.flush()
        await self.session.refresh(outbox_event)

        return outbox_event