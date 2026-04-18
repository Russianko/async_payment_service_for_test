from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import OutboxEvent
from app.repositories.outbox import OutboxRepository


class OutboxService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.outbox_repo = OutboxRepository(session)

    async def create_payment_created_event(
        self,
        payment_id: str,
        idempotency_key: str,
    ) -> OutboxEvent:
        # Создаем событие в outbox

        # ВАЖНО:
        # - происходит в той же транзакции, что и payment
        # - обеспечивает атомарность
        outbox_event = OutboxEvent(
            event_type="payments.new",
            payload={
                "payment_id": payment_id,
                "idempotency_key": idempotency_key,
            },
        )

        return await self.outbox_repo.add(outbox_event)