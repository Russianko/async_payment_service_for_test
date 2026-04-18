import asyncio
from app.workers.outbox_relay import run_outbox_relay

if __name__ == "__main__":
    asyncio.run(run_outbox_relay())