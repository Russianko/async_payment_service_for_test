from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.api.test_webhook import router as test_webhook_router
from app.core.broker import broker
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.connect()
    yield
    await broker.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(test_webhook_router)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}