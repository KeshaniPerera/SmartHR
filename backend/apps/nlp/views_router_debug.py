from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.nlp.router import route

@api_view(["GET"])
@permission_classes([AllowAny])
def route_debug(request):
    q = (request.query_params.get("q") or "").strip()
    if not q:
        return Response({"error":"q is required"}, status=400)
    r = route(q)
    return Response(r.model_dump())
