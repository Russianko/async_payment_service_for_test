from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import OutboxEvent


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, outbox_event: OutboxEvent) -> OutboxEvent:
        self.session.add(outbox_event)
        await self.session.flush()
        await self.session.refresh(outbox_event)
        return outbox_event
