from app.core.broker import broker


class PublisherService:
    async def publish_new_payment(self, payment_id: str, idempotency_key: str) -> None:
        # Публикация события напрямую в RabbitMQ

        # ВАЖНО:
        # Этот способ НЕ является надежным:
        # - если publish упадет после commit БД > событие потеряно

        # В проде это должно происходить через outbox relay
        await broker.publish(
            {
                "payment_id": payment_id,
                "idempotency_key": idempotency_key,
            },
            queue="payments.new",
        )