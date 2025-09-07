from django.urls import path
from .views import my_notifications

urlpatterns = [
    path("notifications", my_notifications, name="my-notifications"),
]
