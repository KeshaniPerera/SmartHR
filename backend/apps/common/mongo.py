import os
import certifi
from pymongo import MongoClient
from django.conf import settings

_client = None

def _client_singleton():
    global _client
    if _client is not None:
        return _client

    tls_args = {
        "tls": True,
        "serverSelectionTimeoutMS": int(os.getenv("MONGO_SELECT_TIMEOUT_MS", "10000")),
        "connectTimeoutMS": int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "8000")),
        "appname": "smarthr-backend",
    }
    # If behind SSL inspection/proxy, allow a temporary dev bypass
    if os.getenv("USE_MONGO_TLS_INSECURE", "0") == "1":
        tls_args["tlsAllowInvalidCertificates"] = True
    else:
        tls_args["tlsCAFile"] = certifi.where()

    _client = MongoClient(settings.MONGO_URI, **tls_args)
    # fail fast 
    _client.admin.command("ping")
    return _client

def get_db():
    return _client_singleton()[settings.MONGO_DB]
