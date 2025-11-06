from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.utils.mongo_metrics import MONGO_CONNECTIONS

client = AsyncIOMotorClient(settings.DATABASE_URL)
MONGO_CONNECTIONS.set(len(client.nodes))  # Track number of MongoDB nodes

db = client.get_default_database()