from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.security import verify_api_key
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentDetailResponse,
    PaymentResponse,
)
from app.services.payment_service import PaymentService


# Роутер для работы с платежами.
# В будущем сюда могут добавляться операции refund/cancel/capture и т.д.
router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_api_key)],
)
async def create_payment(
    payload: PaymentCreateRequest,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_db_session),
) -> PaymentResponse:
    # Проверяем, что ключ идемпотентности не пустой.
    # Это базовая защита от некорректных клиентов.
    if not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must not be empty",
        )

    # ВАЖНО:
    # Idempotency-Key используется для защиты от повторных запросов.
    # Сервис должен:
    # 1. Возвращать существующий платеж при повторе того же ключа
    # 2. Проверять, что payload совпадает
    #    (иначе это конфликт - один ключ, разные данные)
    service = PaymentService(session)

    # Создание платежа:
    # - сохраняется запись в БД (pending)
    # - публикуется событие в очередь (payments.new)
    # Обработка происходит асинхронно в consumer
    payment = await service.create_payment(payload, idempotency_key)

    # Возвращаем 202, потому что платеж еще не обработан.
    # Это важно: клиент НЕ должен ожидать финальный статус здесь.
    response.status_code = status.HTTP_202_ACCEPTED

    return PaymentResponse(
        payment_id=payment.id,
        status=payment.status,  # на этом этапе почти всегда pending
        created_at=payment.created_at,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentDetailResponse,
    dependencies=[Depends(verify_api_key)],
)
async def get_payment(
    payment_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> PaymentDetailResponse:
    # Получение состояния платежа из БД.
    # Это источник истины (source of truth), а не очередь.
    service = PaymentService(session)
    payment = await service.get_payment(payment_id)

    # Важно:
    # processed_at показывает, что платеж уже прошел async обработку
    # webhook_* поля отражают статус доставки уведомления наружу
    return PaymentDetailResponse(
        id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.payment_metadata,
        status=payment.status,
        idempotency_key=payment.idempotency_key,
        webhook_url=payment.webhook_url,
        processed_at=payment.processed_at,
        created_at=payment.created_at,
    )