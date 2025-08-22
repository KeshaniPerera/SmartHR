from django.urls import path
from .views import policy_query

urlpatterns = [ path("nlp/policy", policy_query) ]
