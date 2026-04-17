import httpx

from app.models.payment import Payment


class WebhookService:
    def build_payment_payload(self, payment: Payment) -> dict:
        return {
            "payment_id": str(payment.id),
            "status": payment.status.value,
            "amount": str(payment.amount),
            "currency": payment.currency.value,
            "description": payment.description,
            "metadata": payment.payment_metadata,
            "processed_at": (
                payment.processed_at.isoformat() if payment.processed_at else None
            ),
        }

    async def send_payment_result(self, payment: Payment) -> None:
        if not payment.webhook_url:
            return

        payload = self.build_payment_payload(payment)
        await self.send_payload(payment.webhook_url, payload)

    async def send_payload(self, webhook_url: str, payload: dict) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
            )
            response.raise_for_status()