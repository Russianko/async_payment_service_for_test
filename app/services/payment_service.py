from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentCreateRequest
from app.services.outbox_service import OutboxService
from app.services.publisher_service import PublisherService


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.payment_repo = PaymentRepository(session)
        self.outbox_service = OutboxService(session)
        self.publisher_service = PublisherService()

    async def create_payment(
        self,
        payload: PaymentCreateRequest,
        idempotency_key: str,
    ) -> Payment:
        existing_payment = await self.payment_repo.get_by_idempotency_key(idempotency_key)
        if existing_payment:
            return existing_payment

        payment = Payment(
            amount=payload.amount,
            currency=payload.currency,
            description=payload.description,
            payment_metadata=payload.metadata,
            idempotency_key=idempotency_key,
            webhook_url=str(payload.webhook_url),
        )

        self.session.add(payment)
        await self.session.flush()

        await self.outbox_service.create_payment_created_event(
            payment_id=str(payment.id),
            idempotency_key=idempotency_key,
        )

        await self.session.commit()
        await self.session.refresh(payment)

        await self.publisher_service.publish_new_payment(
            payment_id=str(payment.id),
            idempotency_key=idempotency_key,
        )

        return payment

    async def get_payment(self, payment_id: UUID) -> Payment:
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )
        return payment