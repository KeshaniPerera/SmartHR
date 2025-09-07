
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone
import pytz

from .serializers import PrehireInputSerializer
from .services import predict_probability, model_version
from .constants import COLLECTION_NAME
from apps.common.mongo import get_db  
class PrehirePredictView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        s = PrehireInputSerializer(data=request.data)
        if not s.is_valid():
            print("Prehire validation errors:", s.errors)
            return Response({"errors": s.errors}, status=status.HTTP_400_BAD_REQUEST)

        features = s.to_feature_dict()
        meta = s.meta()  

        proba = predict_probability(features)
        threshold = float(getattr(settings, "PREHIRE_THRESHOLD", 0.45))
        risk_flag = "High" if proba >= threshold else "Low"

        db = get_db()
        col = db[COLLECTION_NAME]

        doc = {
            **meta,                      
            "candidate": features,       
            "probability": proba,
            "risk_flag": risk_flag,
            "threshold": threshold,
            "model_version": model_version(),
            "created_at": timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)).isoformat(),
        }

        try:
            # optional: make candidate_id unique (comment out if you don’t want this)
            col.create_index("candidate_id", unique=False, background=True)
        except Exception as _:
            pass

        try:
            ins = col.insert_one(doc)
            saved = True
            doc_id = str(ins.inserted_id)
        except Exception as e:
            print("Mongo save failed:", repr(e))
            saved = False
            doc_id = None

        return Response({
            "id": doc_id,
            "probability": round(proba, 4),
            "risk_flag": risk_flag,
            "threshold": threshold,
            "model_version": doc["model_version"],
            "saved": saved,
            "candidate_id": meta["candidate_id"],
            "candidate_name": meta["candidate_name"],
        }, status=200)