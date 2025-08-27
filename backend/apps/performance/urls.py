from django.urls import path
from .views import PerformanceRankView

urlpatterns = [
    path("rank/", PerformanceRankView.as_view(), name="performance-rank"),
]
