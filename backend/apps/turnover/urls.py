# backend/apps/turnover/urls.py
from django.urls import path
from .views import TurnoverRankView

urlpatterns = [
        path("rank/", TurnoverRankView.as_view(), name="turnover-rank"),

]
