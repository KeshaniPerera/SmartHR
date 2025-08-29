from django.urls import path
from . import views

urlpatterns = [
    path("scan", views.scan, name="attendance-scan"),
    path("enroll/<str:employee_code>", views.enroll_one, name="attendance-enroll-one"),  # optional helper
]
