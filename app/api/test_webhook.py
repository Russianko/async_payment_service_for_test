from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/test-webhook")
async def test_webhook(request: Request):
    # Тестовый endpoint для проверки webhook доставки.
    # Используется как mock-получатель внешнего сервиса.

    body = await request.json()

    # Логируем входящий webhook.
    # В проде здесь должен быть структурное логирование, а не print.
    print("Incoming webhook:", body)

    # ВАЖНО:
    # Этот endpoint всегда возвращает 200 OK,
    # поэтому для теста retry логики нужно:
    # - либо возвращать 500/404
    # - либо симулировать timeout
    return {"ok": True}