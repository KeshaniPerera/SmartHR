# backend/apps/prehire/services.py
import os, json, joblib, threading, hashlib, pandas as pd
from django.conf import settings

_LOCK = threading.Lock()
_MODEL = None
_SCHEMA = None

ART_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ART_DIR, "prehire_attrition.pkl")
SCHEMA_PATH = os.path.join(ART_DIR, "prehire_schema.json")

def _load():
    global _MODEL, _SCHEMA
    with _LOCK:
        if _MODEL is None:
            _MODEL = joblib.load(MODEL_PATH)
        if _SCHEMA is None:
            _SCHEMA = {}
            if os.path.exists(SCHEMA_PATH):
                with open(SCHEMA_PATH, "r") as f:
                    _SCHEMA = json.load(f)

def model_version() -> str:
    try:
        with open(MODEL_PATH, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except Exception:
        return "unknown"

def predict_probability(payload: dict) -> float:
    _load()
    order = (_SCHEMA or {}).get("feature_order")
    if not order:
        order = sorted(payload.keys())

    row = {k: payload.get(k, None) for k in order}
    X = pd.DataFrame([row], columns=order)
    proba = _MODEL.predict_proba(X)[:, 1][0]
    return float(proba)
