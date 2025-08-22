from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.common.mongo import get_db

@api_view(["POST"])
@permission_classes([AllowAny])
def policy_query(request):
    q = (request.data.get("q") or "").strip()
    slug = (request.data.get("slug") or "").strip()  # optional direct fetch by slug
    col = get_db().policies

    # 1) direct by slug if provided
    if slug:
        doc = col.find_one({"slug": slug}, {"_id": 0})
        if not doc:
            return Response({"error": "Policy not found"}, status=404)
        doc["method"] = "by-slug"; doc["confidence"] = 1.0
        return Response(doc)

    if not q:
        return Response({"error": "Empty query"}, status=400)

    # 2) text search (requires a text index)
    cursor = col.find(
        {"$text": {"$search": q}},
        {"score": {"$meta": "textScore"}, "_id": 0, "title": 1, "slug": 1, "category": 1, "policy_description": 1}
    ).sort([("score", {"$meta": "textScore"})]).limit(3)
    results = list(cursor)
    if results:
        top = results[0]
        # simple confidence scaling 0.6–0.95
        top["confidence"] = 0.6 + min(0.35, float(top.get("score", 1.0)) / 10.0)
        top["method"] = "text-search"
        # add 1-2 alternatives (titles + slugs) if available
        alts = [{"title": r["title"], "slug": r["slug"]} for r in results[1:3]]
        if alts:
            top["alternatives"] = alts
        return Response(top)

    return Response({
        "error": "No matching policy found",
        "suggestions": []  # keep simple
    }, status=404)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from smarthr.apps.common.mongo import get_db  # or from apps.common... if you moved it

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def policy_query(request):
    # accept query via GET ?q=...&slug=... or via POST body
    if request.method == "GET":
        q = (request.query_params.get("q") or "").strip()
        slug = (request.query_params.get("slug") or "").strip()
    else:
        q = (request.data.get("q") or "").strip()
        slug = (request.data.get("slug") or "").strip()

    col = get_db().policies

    if slug:
        doc = col.find_one({"slug": slug}, {"_id": 0})
        if not doc:
            return Response({"error": "Policy not found"}, status=404)
        doc["method"] = "by-slug"; doc["confidence"] = 1.0
        return Response(doc)

    if not q:
        return Response({"error": "Empty query"}, status=400)

    cur = col.find(
        {"$text": {"$search": q}},
        {"score": {"$meta": "textScore"}, "_id": 0, "title": 1, "slug": 1, "category": 1, "policy_description": 1}
    ).sort([("score", {"$meta": "textScore"})]).limit(3)
    results = list(cur)
    if results:
        top = results[0]
        top["confidence"] = 0.6 + min(0.35, float(top.get("score", 1.0)) / 10.0)
        top["method"] = "text-search"
        if len(results) > 1:
            top["alternatives"] = [{"title": r["title"], "slug": r["slug"]} for r in results[1:3]]
        return Response(top)

    return Response({"error": "No matching policy found"}, status=404)
