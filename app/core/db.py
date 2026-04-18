from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Базовый класс для всех ORM моделей.
# Используется SQLAlchemy Declarative API.
class Base(DeclarativeBase):
    pass


# Создание асинхронного движка.
# ВАЖНО:
# - используется asyncpg драйвер
# - echo включается только в debug режиме (логирует SQL)
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)


# Фабрика сессий.
# expire_on_commit=False важно:
# объект остается доступен после commit (часто нужно в async flow)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Dependency для FastAPI.
# Каждому запросу - отдельная сессия.
#
# ВАЖНО:
# - сессия закрывается автоматически
# - транзакция контролируется вручную (commit внутри сервисов)
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session