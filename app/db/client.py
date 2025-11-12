from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.utils.mongo_metrics import increment_connections
import redis.asyncio as redis
import json
from loguru import logger 

client = AsyncIOMotorClient(settings.DATABASE_URL)
increment_connections()
db = client.get_default_database()

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)