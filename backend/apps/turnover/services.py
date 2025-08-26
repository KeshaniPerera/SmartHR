# backend/apps/turnover/services.py
import joblib, json, threading, pandas as pd, numpy as np, hashlib
from pathlib import Path

_LOCK = threading.Lock()
_MODEL = None
_SCHEMA = None
ART_DIR = Path(__file__).with_suffix("").parent / "artifacts"
MODEL_PATH = ART_DIR / "posthire_turnover.pkl"
SCHEMA_PATH = ART_DIR / "posthire_schema.json"

def _load():
    global _MODEL, _SCHEMA
    with _LOCK:
        if _MODEL is None:
            _MODEL = joblib.load(MODEL_PATH)
        if _SCHEMA is None and SCHEMA_PATH.exists():
            _SCHEMA = json.loads(SCHEMA_PATH.read_text())
        elif _SCHEMA is None:
            _SCHEMA = {"feature_order": None}

def model_version():
    try:
        return hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()[:12]
    except Exception:
        return "unknown"

def score_dataframe(df_features: pd.DataFrame) -> np.ndarray:
    _load()
    order = (_SCHEMA or {}).get("feature_order") or list(df_features.columns)
    for col in order:
        if col not in df_features.columns:
            df_features[col] = None
    df_features = df_features[order]
    return _MODEL.predict_proba(df_features)[:, 1]
