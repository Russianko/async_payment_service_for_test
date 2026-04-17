from fastapi import APIRouter

from app.api.v1.payments import router as payments_router

# Точка сборки всех роутеров API.
# Здесь формируется публичный HTTP-контракт сервиса.
# В будущем можно добавить:
# - /webhooks
# - /admin
# - /health
api_router = APIRouter()

api_router.include_router(payments_router)
