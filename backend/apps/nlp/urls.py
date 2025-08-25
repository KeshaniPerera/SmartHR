from django.urls import path
from .views import policy_query
from .views_router_debug import route_debug
from .views_query import nlp_query

urlpatterns = [
    path("nlp/policy", policy_query),         # existing (direct policy lookup)
    path("nlp/route-debug", route_debug),     # router debug
    path("nlp/query", nlp_query),             # NEW unified endpoint
]
