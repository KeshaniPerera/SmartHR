from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import bcrypt

from apps.common.mongo import get_db

# ---- helpers ----
def _session_payload_from_doc(doc):
    # never return password_hash
    return {
        "emp_id": doc["emp_id"],
        "account_type": doc.get("account_type", "employee"),
        "status": doc.get("status", "active"),
    }

def _require_session(request):
    emp_id = request.session.get("emp_id")
    if not emp_id:
        return None
    return {
        "emp_id": emp_id,
        "account_type": request.session.get("account_type", "employee"),
    }

def role_required(roles):
    """
    Decorator for APIView dispatch to enforce role.
    Usage:
      @method_decorator(role_required(["hr"]), name="dispatch")
    """
    def deco(view_func):
        def _wrapped(view, request, *args, **kwargs):
            sess = _require_session(request)
            if not sess:
                return Response({"detail": "Not authenticated"}, status=401)
            if sess["account_type"] not in roles:
                return Response({"detail": "Forbidden"}, status=403)
            return view_func(view, request, *args, **kwargs)
        return _wrapped
    return deco

# ---- Views ----

@method_decorator(csrf_exempt, name="dispatch")  # allow login from React without CSRF dance
class LoginView(APIView):
    authentication_classes = []  # we'll set session manually
    permission_classes = []

    def post(self, request):
        data = request.data or {}
        emp_id = str(data.get("emp_id", "")).strip()
        password = str(data.get("password", "")).strip()
        if not emp_id or not password:
            return Response({"detail": "emp_id and password are required"}, status=400)

        col = get_db()["accounts"]
        doc = col.find_one({"emp_id": emp_id, "status": "active"})
        if not doc:
            return Response({"detail": "Invalid credentials"}, status=401)

        ok = bcrypt.checkpw(password.encode("utf-8"), doc["password_hash"].encode("utf-8"))
        if not ok:
            return Response({"detail": "Invalid credentials"}, status=401)

        # set session
        request.session["emp_id"] = doc["emp_id"]
        request.session["account_type"] = doc.get("account_type", "employee")
        request.session["logged_in"] = True

        return Response({"user": _session_payload_from_doc(doc)})

class MeView(APIView):
    def get(self, request):
        sess = _require_session(request)
        if not sess:
            return Response({"detail": "Not authenticated"}, status=401)
        return Response({"user": sess})

@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(APIView):
    def post(self, request):
        request.session.flush()
        return Response({"detail": "ok"})

# Example of a protected endpoint (HR-only)
@method_decorator(role_required(["hr"]), name="dispatch")
class HROnlyPing(APIView):
    def get(self, request):
        return Response({"detail": "pong-hr"})
