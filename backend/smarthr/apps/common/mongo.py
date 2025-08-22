from django.conf import settings
from pymongo import MongoClient

_client = None
_db = None

def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(settings.MONGO_URI, uuidRepresentation="standard")
        _db = _client.get_database(settings.MONGO_DB)
    return _db
