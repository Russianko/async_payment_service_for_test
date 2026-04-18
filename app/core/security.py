from fastapi import Header, HTTPException, status
from app.core.config import settings


# Простая проверка API-ключа.
# Используется как dependency на уровне роутеров.
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    # ВАЖНО:
    # Это упрощенная схема аутентификации.
    # В проде обычно используются:
    # - OAuth2/JWT
    # - mTLS
    # - или API Gateway с авторизацией

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )