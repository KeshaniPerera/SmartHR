from pathlib import Path
import os
from dotenv import load_dotenv



BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")  

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "apps.nlp",
    "apps.prehire",
    "apps.turnover",
    "apps.performance",

]



MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "smarthr.urls"
TEMPLATES = []
WSGI_APPLICATION = "smarthr.wsgi.application"

# Django ORM not used; keep a dummy DB to satisfy Django internals
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

# CORS (Frontend on Vite 5173)
CORS_ALLOW_ALL_ORIGINS = True  # keep simple for dev

# Timezone
TIME_ZONE = "Asia/Colombo"
USE_TZ = True

# Mongo config (used by our helper)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "smarthr")



REST_FRAMEWORK = {
    # renderers/parsers: JSON only
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],

    # no auth for now (since we didn't enable django.contrib.auth)
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],

    # stop DRF from importing AnonymousUser, etc.
    "UNAUTHENTICATED_USER": None,
    "UNAUTHENTICATED_TOKEN": None,
}

CORS_ALLOW_ALL_ORIGINS = True 