import json, datetime as dt
import numpy as np
from zoneinfo import ZoneInfo
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
# NEW
from apps.attendance.db import attendance_col, get_db, get_fs
from apps.attendance.ocv_recognition import recognize_image_base64, extract_feature_from_bgr, refresh_known



ZONE = ZoneInfo("Asia/Colombo")

def _today_str_colombo(now=None):
    now = now or dt.datetime.now(tz=ZONE)
    return now.strftime("%Y-%m-%d")

def _cutoff_dt(now=None):
    now = now or dt.datetime.now(tz=ZONE)
    return now.replace(hour=12, minute=1, second=0, microsecond=0)

def _json(req):
    if req.body:
        try:
            return json.loads(req.body.decode("utf-8"))
        except Exception:
            return {}
    return {}

@csrf_exempt
def scan(req):
    if req.method != "POST":
        return JsonResponse({"ok": False, "error": "method_not_allowed"}, status=405)

    body = _json(req)
    image = body.get("imageBase64")
    if not image:
        return JsonResponse({"ok": False, "message": "Invalid Entry", "reason": "no_image"}, status=200)

    r = recognize_image_base64(image, float(settings.ATTENDANCE_SIM_THRESHOLD))
    if not r.get("ok"):
        return JsonResponse({"ok": False, "message": "Invalid Entry", **r}, status=200)

    employee_code = r["employeeCode"]
    conf = r["confidence"]

    now = dt.datetime.now(tz=ZONE)
    date_str = _today_str_colombo(now)
    cutoff = _cutoff_dt(now)
    is_out = now > cutoff

    col = attendance_col()
    q = {"employeeCode": employee_code, "date": date_str}
    doc = col.find_one(q)

    result_type = None
    if not doc:
        payload = {
            "employeeCode": employee_code,
            "date": date_str,
            "inTime": None if is_out else now.astimezone(dt.timezone.utc),
            "outTime": now.astimezone(dt.timezone.utc) if is_out else None,
            "method": "face",
            "lastConfidence": conf,
        }
        col.update_one(q, {"$setOnInsert": payload}, upsert=True)
        result_type = "OUT" if is_out else "IN"
    else:
        update = {"lastConfidence": conf}
        if is_out:
            if not doc.get("outTime"):
                update["outTime"] = now.astimezone(dt.timezone.utc)
                result_type = "OUT"
            else:
                result_type = "OUT_DUPLICATE"
        else:
            if not doc.get("inTime"):
                update["inTime"] = now.astimezone(dt.timezone.utc)
                result_type = "IN"
            else:
                result_type = "IN_DUPLICATE"
        col.update_one(q, {"$set": update})

    return JsonResponse({
        "ok": True,
        "type": result_type,
        "employeeCode": employee_code,
        "confidence": conf
    })

# -------- Optional helper: Re-enroll one employee from latest GridFS photo --------
@csrf_exempt
def enroll_one(req, employee_code: str):
    if req.method != "POST":
        return JsonResponse({"ok": False, "error": "method_not_allowed"}, status=405)
    db = get_db(); fs = get_fs()
    files = list(db[f"{settings.MONGODB_GRIDFS_BUCKET}.files"]
                 .find({"filename": {"$regex": f"^{employee_code}", "$options": "i"}})
                 .sort("uploadDate", -1).limit(1))
    if not files:
        return JsonResponse({"ok": False, "error": "no_photo"}, status=404)
    data = fs.get(files[0]["_id"]).read()

    import cv2, numpy as np
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    feat = extract_feature_from_bgr(img)
    if feat is None:
        return JsonResponse({"ok": False, "message": "Invalid Entry", "reason": "no_face"}, status=200)

    db["employees"].update_one({"employeeCode": employee_code},
                               {"$set": {"faceEmbedding": feat.tolist()}},
                               upsert=True)
    refresh_known()
    return JsonResponse({"ok": True, "employeeCode": employee_code})
