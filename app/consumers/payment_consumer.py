import asyncio
import random
from datetime import datetime, timezone
from uuid import UUID

from faststream.rabbit import RabbitMessage
from sqlalchemy import select

from app.core.broker import broker
from app.core.db import AsyncSessionLocal
from app.models.payment import Payment, PaymentStatusEnum


@broker.subscriber("payments.new")
async def process_payment(message: dict, rabbit_message: RabbitMessage) -> None:
    # Consumer получает событие о создании платежа.
    # Это точка перехода из sync API в async обработку.
    print("CONSUMER GOT MESSAGE:", message)

    payment_id = UUID(message["payment_id"])

    # Имитация внешней обработки (например, PSP/банк/процессинг)
    # В реальной системе здесь будет:
    # - вызов внешнего API
    # - или сложная бизнес-логика
    await asyncio.sleep(random.uniform(2, 5))

    # Имитация результата обработки
    is_success = random.random() < 0.9
    new_status = (
        PaymentStatusEnum.SUCCEEDED if is_success else PaymentStatusEnum.FAILED
    )

    async with AsyncSessionLocal() as session:
        # Загружаем платеж из БД - в данном случае БД является источником правды
        result = await session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            # Это потенциальная проблема согласованности:
            # сообщение есть, а записи нет.
            # В проде это повод для алерта или retry.
            print("PAYMENT NOT FOUND:", payment_id)
            return

        # ВАЖНО:
        # Здесь должна быть защита от повторной обработки.
        # Сейчас consumer НЕ идемпотентен.
        #
        # В реальной системе нужно:
        # if payment.status != PENDING:
        #     return
        #
        # Иначе повторная доставка сообщения может перезаписать состояние.

        payment.status = new_status
        payment.processed_at = datetime.now(timezone.utc)

        await session.commit()
        print("PAYMENT UPDATED:", payment.id, payment.status)

        try:
            # Публикуем событие для webhook доставки.
            print("SENDING WEBHOOK EVENT:", payment.webhook_url)

            await broker.publish(
                {
                    # Бизнес-данные
                    "payment_id": str(payment.id),
                    "status": payment.status.value,
                    "amount": str(payment.amount),
                    "currency": payment.currency.value,
                    "description": payment.description,
                    "metadata": payment.payment_metadata,
                    "processed_at": payment.processed_at.isoformat()
                    if payment.processed_at else None,

                    # Технические данные для доставки
                    "webhook_url": payment.webhook_url,
                    "attempt": 1,  # первая попытка доставки
                },
                queue="payments.webhook.send",
            )

            print("WEBHOOK EVENT PUBLISHED")

        except Exception as e:
            # ВАЖНО:
            # Здесь возможна потеря события:
            # платеж обновился, но webhook не отправился.
            #
            # Это классическая проблема:
            # DB commit прошел > publish не прошел.
            #
            # В проде решается через transactional outbox.
            print(f"Webhook send failed for payment {payment.id}: {e}")