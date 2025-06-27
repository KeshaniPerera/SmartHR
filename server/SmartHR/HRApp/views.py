from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import User
import json

@csrf_exempt
def login_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({"detail": "Invalid username or password"}, status=400)

            # Plain-text password check
            if password == user.password:
                return JsonResponse({
                    "message": "Login successful",
                    "user_type": user.type,
                    "user_id": user.id
                })
            else:
                return JsonResponse({"detail": "Invalid username or password"}, status=400)

        except Exception as e:
            return JsonResponse({"detail": "Error logging in", "error": str(e)}, status=500)

    return JsonResponse({"detail": "Method not allowed"}, status=405)
