import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "finora-super-secret-key-change-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "finora-jwt-secret-key-secure-2026")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # MongoDB Configuration
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/finora_db")
    DB_NAME = os.environ.get("DB_NAME", "finora_db")
    
    # Environment
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")
    PORT = int(os.environ.get("PORT", 5000))
    HOST = os.environ.get("HOST", "0.0.0.0")
