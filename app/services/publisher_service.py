from app.core.broker import broker


class PublisherService:
    async def publish_new_payment(self, payment_id: str, idempotency_key: str) -> None:
        await broker.publish(
            {
                "payment_id": payment_id,
                "idempotency_key": idempotency_key,
            },
            queue="payments.new",
        )