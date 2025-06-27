from django.urls import path
from .views import login_api

urlpatterns = [
    path('api/login/', login_api),
]
