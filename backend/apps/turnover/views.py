# backend/apps/turnover/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from apps.common.mongo import get_db
from .constants import POSTHIRE_FEATURES, EMP_COLLECTION
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
    # support both nested doc['features'] and top-level fields
    src = doc.get("features") or doc
    out = {}
    for k in POSTHIRE_FEATURES:
        val = src.get(k)
        if k == "OverTime":
            val = _coerce_overtime(val)
        out[k] = val
    return out

class TurnoverRankView(APIView):
    permission_classes = [AllowAny]  

    def get(self, request):
        limit = int(request.query_params.get("limit", "200"))
        col = get_db()[EMP_COLLECTION]

        # read employee docs 
        rows = list(col.find({}, {"_id": 0}))
        if not rows:
            return Response({"count": 0, "model_version": model_version(), "results": []}, status=200)

        # build features frame
        feats = pd.DataFrame([_extract_features(r) for r in rows])
        probs = score_dataframe(feats)

        # make response rows
        thr = float(getattr(settings, "PREHIRE_THRESHOLD", 0.45))

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

        results = []
        for r, p in zip(rows, probs):
            emp_id    = norm_str(pick(r, "emp_id", "employee_id", "EmployeeID", "EmpID", "id"))
            full_name = norm_str(pick(r, "full_name", "fullName", "FullName", "name"))  # may be None (not in Insights)
            dept      = norm_str(pick(r, "department", "Department", "dept", "Dept"))
            job_role  = norm_str(pick(r, "job_role", "JobRole", "jobTitle", "JobTitle", "role"))

            results.append({
                "emp_id": emp_id,
                "full_name": full_name,  # will fill from employees below if missing
                "department": dept,
                "job_role": job_role,
                "probability": float(round(p, 6)),
                "risk_flag": "High" if p >= thr else "Low",
            })

        # ---- join full_name from employees collection ----
        emp_ids = [r["emp_id"] for r in results if r.get("emp_id")]
        if emp_ids:
            people = get_db()["employees"].find(
                {"emp_id": {"$in": emp_ids}},
                {"_id": 0, "emp_id": 1, "full_name": 1}
            )
            name_map = {norm_str(p.get("emp_id")): norm_str(p.get("full_name")) for p in people}
            for r in results:
                if not r.get("full_name"):  # only fill if missing/empty
                    r["full_name"] = name_map.get(r.get("emp_id"))

        # sort + return
        results.sort(key=lambda x: x["probability"], reverse=True)
        return Response({
            "count": min(limit, len(results)),
            "model_version": model_version(),
            "results": results[:limit]
        }, status=200)
