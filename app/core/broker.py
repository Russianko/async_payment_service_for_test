from faststream.rabbit import RabbitBroker

from app.core.config import settings


# Инициализация брокера сообщений (RabbitMQ).
#
# ВАЖНО:
# - используется один брокер на всё приложение
# - он управляет publish и subscribe
#
# В проде часто:
# - отдельные сервисы имеют свои брокеры
# - или используется слой абстракций
broker = RabbitBroker(settings.rabbitmq_url)