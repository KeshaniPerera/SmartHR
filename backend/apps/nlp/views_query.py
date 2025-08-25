from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.nlp.executor import execute_free_text

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def nlp_query(request):
    if request.method == "GET":
        q = (request.query_params.get("q") or "").strip()
    else:
        q = (request.data.get("q") or "").strip()
    if not q:
        return Response({"error": "q is required"}, status=400)
    out = execute_free_text(q)
    return Response(out)
