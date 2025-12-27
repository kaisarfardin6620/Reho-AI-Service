from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.utils.mongo_metrics import increment_connections
import redis.asyncio as redis

client = AsyncIOMotorClient(settings.DATABASE_URL)
increment_connections()

db = client[settings.MONGO_DB_NAME]

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)