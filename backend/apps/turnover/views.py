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
    permission_classes = [AllowAny]  # dev; tighten for prod

    def get(self, request):
        limit = int(request.query_params.get("limit", "200"))
        col = get_db()[EMP_COLLECTION]

        # read employee docs (no writes)
        rows = list(col.find({}, {"_id": 0}))
        if not rows:
            return Response({"count": 0, "model_version": model_version(), "results": []}, status=200)

        # build features frame
        feats = pd.DataFrame([_extract_features(r) for r in rows])
        probs = score_dataframe(feats)

        # make response rows
        thr = float(getattr(settings, "PREHIRE_THRESHOLD", 0.45))  # reuse threshold for High/Low label
        results = []
        for r, p in zip(rows, probs):
            results.append({
                "employee_id": r.get("employee_id") or r.get("EmployeeID"),
                "full_name": r.get("full_name") or r.get("FullName"),
                "department": r.get("department") or r.get("Department"),
                "job_role": r.get("job_role") or r.get("JobRole"),
                "probability": float(round(p, 6)),
                "risk_flag": "High" if p >= thr else "Low",
            })

        # sort: high → low
        results.sort(key=lambda x: x["probability"], reverse=True)
        return Response({
            "count": min(limit, len(results)),
            "model_version": model_version(),
            "results": results[:limit]
        }, status=200)
