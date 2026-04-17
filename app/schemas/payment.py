from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.payment import CurrencyEnum, PaymentStatusEnum


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: CurrencyEnum
    description: str = Field(..., min_length=1, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: HttpUrl


class PaymentResponse(BaseModel):
    payment_id: UUID
    status: str
    created_at: datetime

    model_config = ConfigDict(
        json_encoders={Decimal: float}
    )


class PaymentDetailResponse(BaseModel):
    id: UUID
    amount: Decimal
    currency: str
    description: str
    metadata: dict
    status: str
    idempotency_key: str
    webhook_url: str
    processed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(
        json_encoders={Decimal: float}
    )
