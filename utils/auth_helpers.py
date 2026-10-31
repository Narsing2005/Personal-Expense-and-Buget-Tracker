import bcrypt
from bson import ObjectId
from datetime import datetime, date

def hash_password(password: str) -> str:
    """Hash a password using Bcrypt with a generated salt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def check_password(password: str, hashed_password: str) -> bool:
    """Verify a plain password against the Bcrypt hashed password."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def serialize_doc(doc):
    """Serialize a MongoDB document into a JSON-friendly dict."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == "_id":
                result["id"] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, (datetime, date)):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = serialize_doc(value)
            elif isinstance(value, list):
                result[key] = [serialize_doc(v) for v in value]
            else:
                result[key] = value
        return result
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc
