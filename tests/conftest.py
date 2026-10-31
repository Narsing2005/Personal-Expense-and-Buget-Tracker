import pytest
import mongomock
from app import create_app
from database import DatabaseManager

class TestConfig:
    TESTING = True
    SECRET_KEY = "finora-super-test-secret-key-32-bytes-long!"
    JWT_SECRET_KEY = "finora-super-test-jwt-secret-key-32-bytes-long!"
    DB_NAME = "finora_test_db"
    MONGO_URI = "mongodb://localhost:27017/finora_test_db"

@pytest.fixture(scope="session")
def app():
    # Force mock database for isolated fast tests
    DatabaseManager._client = mongomock.MongoClient()
    DatabaseManager._db = DatabaseManager._client["finora_test_db"]
    DatabaseManager._is_mock = True
    DatabaseManager._init_indexes()

    app = create_app(TestConfig)
    return app

@pytest.fixture(scope="function")
def client(app):
    with app.test_client() as test_client:
        with app.app_context():
            # Clear test database collections before each test
            db = DatabaseManager.get_db()
            db.users.delete_many({})
            db.transactions.delete_many({})
            db.budgets.delete_many({})
            db.notifications.delete_many({})
        yield test_client

@pytest.fixture(scope="function")
def auth_headers(client):
    # Register and login a standard test user
    client.post("/api/auth/register", json={
        "name": "Jordan Lee",
        "email": "jordan@example.com",
        "password": "Password123!"
    })
    login_res = client.post("/api/auth/login", json={
        "email": "jordan@example.com",
        "password": "Password123!"
    })
    token = login_res.get_json()["token"]
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
