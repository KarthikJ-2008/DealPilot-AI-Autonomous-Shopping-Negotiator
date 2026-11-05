from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB_NAME]


def get_db():
    """Dependency provider returning the async MongoDB database instance."""
    return db