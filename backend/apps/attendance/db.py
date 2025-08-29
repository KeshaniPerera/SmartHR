from django.conf import settings
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from gridfs import GridFS

_client = None
_db = None
_fs = None

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI)
    return _client

def get_db():
    """Return DB from URI if present; else fallback to settings.MONGODB_DB_NAME."""
    global _db
    if _db is None:
        client = get_client()
        try:
            db = client.get_default_database()  # raises if no db in URI
        except ConfigurationError:
            db = None
        if db is None:
            name = getattr(settings, "MONGODB_DB_NAME", None)
            if not name:
                raise RuntimeError("No default DB in MONGODB_URI and MONGODB_DB_NAME not set.")
            db = client[name]
        _db = db
    return _db

def get_fs():
    global _fs
    if _fs is None:
        bucket = getattr(settings, "MONGODB_GRIDFS_BUCKET", "fs")
        _fs = GridFS(get_db(), collection=bucket)
    return _fs

def employees_col():
    return get_db()["employees"]

def attendance_col():
    col = get_db()["attendance"]
    col.create_index([("employeeCode", 1), ("date", 1)], unique=True)
    return col
