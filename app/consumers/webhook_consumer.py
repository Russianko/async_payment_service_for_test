from datetime import datetime, timezone

from faststream.rabbit import RabbitQueue
from sqlalchemy import select

from app.core.broker import broker
from app.core.db import AsyncSessionLocal
from app.models.payment import Payment
from app.services.webhook_service import WebhookService


MAX_RETRIES = 3

webhook_service = WebhookService()

webhook_send_queue = RabbitQueue(
    name="payments.webhook.send",
    durable=True,
)

webhook_retry_queue = RabbitQueue(
    name="payments.webhook.retry",
    durable=True,
    arguments={
        "x-message-ttl": 10000,
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "payments.webhook.send",
    },
)

webhook_dlq_queue = RabbitQueue(
    name="payments.webhook.dlq",
    durable=True,
)


@broker.subscriber(webhook_send_queue)
async def process_webhook(event: dict) -> None:
    print("WEBHOOK EVENT RECEIVED:", event)

    try:
        print("TRYING WEBHOOK:", event["webhook_url"], "attempt=", event.get("attempt", 1))

        await webhook_service.send_payload(
            webhook_url=event["webhook_url"],
            payload=event,
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Payment).where(Payment.id == event["payment_id"])
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.webhook_delivered_at = datetime.now(timezone.utc)
                payment.webhook_attempts = event.get("attempt", 1)
                payment.webhook_last_error = None
                await session.commit()

        print("WEBHOOK DELIVERED:", event["payment_id"])

    except Exception as e:
        attempt = event.get("attempt", 1)
        print("WEBHOOK FAILED:", event["payment_id"], "attempt=", attempt, "error=", str(e))

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Payment).where(Payment.id == event["payment_id"])
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.webhook_attempts = attempt
                payment.webhook_last_error = str(e)
                await session.commit()

        if attempt >= MAX_RETRIES:
            print("SENDING TO DLQ:", event["payment_id"])

            await broker.publish(
                {
                    **event,
                    "final_error": str(e),
                },
                queue=webhook_dlq_queue.name,
            )
            return

        print("SENDING TO RETRY:", event["payment_id"], "next_attempt=", attempt + 1)

        await broker.publish(
            {
                **event,
                "attempt": attempt + 1,
            },
            queue=webhook_retry_queue.name,
        )