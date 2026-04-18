from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment

# В проде для конкурентных обновлений можно использовать:
# - SELECT FOR UPDATE
# - или optimistic locking (version поле)
# для избегания race conditions


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        # Репозиторий работает в рамках одной транзакции (одной сессии)
        # ВАЖНО: commit контролируется снаружи (сервисом)
        self.session = session

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        # Получение платежа по ID
        # Используется как основной способ чтения состояния (source of truth)
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        # Получение платежа по idempotency_key
        # ВАЖНО:
        # - используется для защиты от повторных POST запросов
        # - ключ уникален на уровне БД
        stmt = select(Payment).where(Payment.idempotency_key == idempotency_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, payment: Payment) -> Payment:
        # Добавление нового платежа в сессию
        # flush() - отправляет INSERT в БД, но не делает commit
        # refresh() -    подтягивает значения (например, created_at)
        self.session.add(payment)

        await self.session.flush()
        await self.session.refresh(payment)

        return payment