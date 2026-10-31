import logging
from pymongo import MongoClient, ASCENDING
import pymongo.errors

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _client = None
    _db = None
    _is_mock = False

    @classmethod
    def get_db(cls, app=None):
        if cls._db is None or cls._client is None:
            cls.init_db(app)
        return cls._db

    @classmethod
    def init_db(cls, app=None):
        mongo_uri = "mongodb://localhost:27017/finora_db"
        db_name = "finora_db"

        if app and "MONGO_URI" in app.config:
            mongo_uri = app.config["MONGO_URI"]
        if app and "DB_NAME" in app.config:
            db_name = app.config["DB_NAME"]

        try:
            # Attempt real MongoDB connection with short timeout to test connectivity
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=1500)
            client.admin.command('ping')
            cls._client = client
            cls._db = client[db_name]
            cls._is_mock = False
            logger.info("Successfully connected to MongoDB server.")
        except Exception as e:
            logger.warning(
                f"Could not connect to live MongoDB at {mongo_uri} ({e}). "
                "Falling back to embedded in-memory database (mongomock) for seamless zero-config execution."
            )
            import mongomock
            cls._client = mongomock.MongoClient()
            cls._db = cls._client[db_name]
            cls._is_mock = True

        cls._init_indexes()
        return cls._db

    @classmethod
    def is_mock(cls):
        return cls._is_mock

    @classmethod
    def _init_indexes(cls):
        try:
            # Users collection: unique email
            cls._db.users.create_index([("email", ASCENDING)], unique=True)
            # Transactions collection: user_id and date
            cls._db.transactions.create_index([("user_id", ASCENDING), ("date", ASCENDING)])
            # Budgets collection: user_id, month, category
            cls._db.budgets.create_index([("user_id", ASCENDING), ("month", ASCENDING), ("category", ASCENDING)])
            # Notifications collection: user_id and created_at
            cls._db.notifications.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
        except Exception as err:
            logger.debug(f"Index creation notice: {err}")

def get_db():
    return DatabaseManager.get_db()
