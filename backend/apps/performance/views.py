from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from apps.common.mongo import get_db
from .constants import PERFORMANCE_FEATURES, EMP_COLLECTION
from .services import score_dataframe, model_version
import pandas as pd

def _coerce_overtime(v):
    if v in ("Yes","No"): return v
    if isinstance(v, bool): return "Yes" if v else "No"
    if isinstance(v, (int, float)): return "Yes" if v else "No"
    s = str(v).strip().lower()
    if s in ("y","yes","true","1"): return "Yes"
    if s in ("n","no","false","0",""): return "No"
    return "No"

def _extract_features(doc: dict) -> dict:
    # Our Employee Insights are flat documents; still tolerate nested 'features' if present.
    src = doc.get("features") or doc
    out = {}
    for k in PERFORMANCE_FEATURES:
        val = src.get(k)
        if k == "OverTime":
            val = _coerce_overtime(val)
        out[k] = val
    return out

class PerformanceRankView(APIView):
    permission_classes = [AllowAny]  # dev; tighten later

    def get(self, request):
        limit = int(request.query_params.get("limit", "200"))
        col = get_db()[EMP_COLLECTION]

        rows = list(col.find({}, {"_id": 0}))
        if not rows:
            return Response({"count": 0, "model_version": model_version(), "results": []}, status=200)

        feats = pd.DataFrame([_extract_features(r) for r in rows])
        probs = score_dataframe(feats)

        # Label "High" if prob >= PERFORMANCE_THRESHOLD (default 0.6)
        thr = float(getattr(settings, "PERFORMANCE_THRESHOLD", 0.6))

        def pick(r, *keys):
            for k in keys:
                if k in r and r[k] is not None:
                    return r[k]
            return None

        def norm_str(v):
            if v is None:
                return None
            if not isinstance(v, str):
                v = str(v)
            v = v.strip()
            return v if v else None

        # 1) build rows (may miss full_name in Employee Insights)
        results = []
        for r, p in zip(rows, probs):
            emp_id    = norm_str(pick(r, "emp_id", "employee_id", "EmployeeID", "EmpID", "id"))
            full_name = norm_str(pick(r, "full_name", "fullName", "FullName", "name"))  # may be None here
            dept      = norm_str(pick(r, "department", "Department", "dept", "Dept"))
            job_role  = norm_str(pick(r, "job_role", "JobRole", "jobTitle", "JobTitle", "role"))

            results.append({
                "emp_id": emp_id,
                "full_name": full_name,  # filled in step 2 if missing
                "department": dept,
                "job_role": job_role,
                "probability": float(round(p, 6)),
                "label": "High" if p >= thr else "Low",
            })

        # 2) JOIN full_name from employees on emp_id (only fill if missing)
        emp_ids = [r["emp_id"] for r in results if r.get("emp_id")]
        if emp_ids:
            people = get_db()["employees"].find(
                {"emp_id": {"$in": emp_ids}},
                {"_id": 0, "emp_id": 1, "full_name": 1}
            )
            name_map = {norm_str(p.get("emp_id")): norm_str(p.get("full_name")) for p in people}
            for r in results:
                if not r.get("full_name"):
                    r["full_name"] = name_map.get(r.get("emp_id"))

        # sort HIGH → LOW
        results.sort(key=lambda x: x["probability"], reverse=True)
        return Response({
            "count": min(limit, len(results)),
            "model_version": model_version(),
            "results": results[:limit]
        }, status=200)
