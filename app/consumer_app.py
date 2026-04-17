import asyncio

from faststream import FastStream

from app.consumers.payment_consumer import process_payment  # noqa: F401
from app.consumers.webhook_consumer import (
    process_webhook,  # noqa: F401
    webhook_retry_queue,
    webhook_dlq_queue,
)
from app.core.broker import broker

app = FastStream(broker)


@app.after_startup
async def declare_extra_queues() -> None:
    await broker.declare_queue(webhook_retry_queue)
    await broker.declare_queue(webhook_dlq_queue)


if __name__ == "__main__":
    asyncio.run(app.run())