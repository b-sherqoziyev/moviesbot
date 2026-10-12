import redis.asyncio as aioredis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.core.config import settings
from app.services.subscription_service import SubscriptionService

# Redis client
redis_client: aioredis.Redis = aioredis.from_url(
    settings.redis_connection_url,
    decode_responses=True
)

# Aiogram FSM uchun Redis saqlash joyi
storage: RedisStorage = RedisStorage(redis=redis_client)

# Telegram Bot obyekti (Standart HTML parse mode bilan)
bot: Bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Dispatcher
dp: Dispatcher = Dispatcher(storage=storage)

# Markaziy SubscriptionService nusxasi
subscription_service: SubscriptionService = SubscriptionService(redis_client)
