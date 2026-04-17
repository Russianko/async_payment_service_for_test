from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class PaymentWebhookEvent(BaseModel):
    payment_id: UUID
    status: str
    amount: str
    currency: str
    description: str
    metadata: dict
    processed_at: datetime | None = None
    webhook_url: HttpUrl
    attempt: int = 1