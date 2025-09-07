from django.urls import path, include

urlpatterns = [
    path("api/", include("apps.nlp.urls")),
    path("api/prehire/", include("apps.prehire.urls")),  
    path("api/turnover/", include("apps.turnover.urls")),
    path("api/performance/", include("apps.performance.urls")),
    path("api/attendance/", include("apps.attendance.urls")),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/common/", include("apps.common.urls")),
    




]
