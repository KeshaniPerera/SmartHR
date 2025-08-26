# backend/apps/turnover/apps.py
from django.apps import AppConfig

class TurnoverConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.turnover"          
    verbose_name = "Turnover"
