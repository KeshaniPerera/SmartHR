from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny  # switch to IsAuthenticated in prod
from rest_framework.response import Response
from apps.common.mongo import get_db
from apps.common.json import mongo_to_json  # the helper we added earlier

@api_view(["GET"])
@permission_classes([AllowAny])
def my_notifications(request):
    """
    Uses Django session to determine emp_id and account_type.
    HR: return all type='hr' notifications.
    Non-HR: return only their type='employee' notifications (to/empId matches).
    """
    sess = request.session or {}
    emp_id = (sess.get("emp_id") or "").strip()
    account_type = (sess.get("account_type") or "employee").strip().lower()

    if not emp_id:
        return Response({"error": "Not authenticated"}, status=401)

    db = get_db()
    is_hr = account_type == "hr"

    if is_hr:
        q = {"type": {"$regex": "^hr$", "$options": "i"}}
    else:
        q = {
            "type": {"$regex": "^employee$", "$options": "i"},
            "$or": [{"to": emp_id}, {"empId": emp_id}],
        }

    cur = db.notifications.find(
        q,
        {"_id": 1, "type": 1, "to": 1, "empId": 1, "reason": 1, "date": 1, "createdAt": 1, "meta": 1}
    ).sort("createdAt", -1)

    items = [mongo_to_json(d) for d in cur]
    return Response({
        "emp_id": emp_id,
        "is_hr": is_hr,
        "count": len(items),
        "results": items
    }, status=200)
