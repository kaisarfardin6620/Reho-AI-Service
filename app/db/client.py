from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.utils.mongo_metrics import increment_connections

client = AsyncIOMotorClient(settings.DATABASE_URL)
increment_connections()

db = client.get_default_database()