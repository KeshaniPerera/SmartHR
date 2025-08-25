from django.urls import path, include

urlpatterns = [
    path("api/", include("apps.nlp.urls")),
    path("api/prehire/", include("apps.prehire.urls")),  

]
