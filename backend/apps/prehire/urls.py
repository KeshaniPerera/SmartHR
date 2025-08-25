# backend/apps/prehire/urls.py
from django.urls import path
from .views import PrehirePredictView

urlpatterns = [
    path("predict/", PrehirePredictView.as_view(), name="prehire-predict"),
]

