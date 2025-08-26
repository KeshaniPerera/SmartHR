# backend/scripts/train_turnover.py
import os, json, hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
import sklearn

# ---------- paths ----------
BASE = Path(__file__).resolve().parents[1]  # .../backend
DATA = BASE / "data" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
OUT = BASE / "apps" / "turnover" / "artifacts"
OUT.mkdir(parents=True, exist_ok=True)

MODEL_PATH = OUT / "posthire_turnover.pkl"
SCHEMA_PATH = OUT / "posthire_schema.json"
METRICS_PATH = OUT / "turnover_metrics.json"

# ---------- features ----------
POSTHIRE_COLS = [
    "JobInvolvement","JobLevel","JobSatisfaction","EnvironmentSatisfaction",
    "RelationshipSatisfaction","WorkLifeBalance","YearsAtCompany",
    "YearsInCurrentRole","YearsSinceLastPromotion","YearsWithCurrManager",
    "OverTime","MonthlyIncome","PerformanceRating"
]

print(f"Using sklearn: {sklearn.__version__}")
print(f"Reading: {DATA}")
if not DATA.exists():
    raise FileNotFoundError(f"Dataset not found at {DATA}. Put the CSV there and retry.")

# ---------- load ----------
df = pd.read_csv(DATA)

# target
if "Attrition" not in df.columns:
    raise KeyError("Column 'Attrition' not found in dataset.")
y = df["Attrition"].map({"Yes": 1, "No": 0}).astype(int)

# features subset (post-hire)
missing = [c for c in POSTHIRE_COLS if c not in df.columns]
if missing:
    raise KeyError(f"Missing expected columns: {missing}")
X = df[POSTHIRE_COLS].copy()

# ---------- dtypes ----------
# Treat only OverTime as categorical; keep all 1–5 ratings as numeric
cat_cols = ["OverTime"]
num_cols = [c for c in POSTHIRE_COLS if c not in cat_cols]

pre = ColumnTransformer(
    transformers=[
        ("num", Pipeline(steps=[
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
        ]), num_cols),
        ("cat", Pipeline(steps=[
            ("imp", SimpleImputer(strategy="most_frequent")),
            ("oh", OneHotEncoder(handle_unknown="ignore")),
        ]), cat_cols),
    ],
    remainder="drop",
    n_jobs=None,
)

clf = RandomForestClassifier(
    n_estimators=500,
    min_samples_split=4,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)

pipe = Pipeline([
    ("pre", pre),
    ("clf", clf),
])

# ---------- train/test ----------
Xtr, Xte, ytr, yte = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

pipe.fit(Xtr, ytr)

# ---------- eval ----------
proba_te = pipe.predict_proba(Xte)[:, 1]
pred_te = (proba_te >= 0.5).astype(int)

acc = accuracy_score(yte, pred_te)
try:
    auc = roc_auc_score(yte, proba_te)
except Exception:
    auc = float("nan")

cm = confusion_matrix(yte, pred_te).tolist()
cr = classification_report(yte, pred_te, output_dict=True)

metrics = {
    "sklearn_version": sklearn.__version__,
    "accuracy": acc,
    "roc_auc": auc,
    "confusion_matrix": cm,
    "classification_report": cr,
    "n_train": int(len(ytr)),
    "n_test": int(len(yte)),
    "features": POSTHIRE_COLS,
}

print("\n=== Turnover (post-hire) metrics ===")
print(f"Accuracy : {acc:.4f}")
print(f"ROC AUC  : {auc:.4f}")
print(f"CM       : {cm}")

# ---------- save artifacts ----------
joblib.dump(pipe, MODEL_PATH)
with open(SCHEMA_PATH, "w") as f:
    json.dump({"feature_order": POSTHIRE_COLS, "sklearn_version": sklearn.__version__}, f, indent=2)
with open(METRICS_PATH, "w") as f:
    json.dump(metrics, f, indent=2)

# show hash/version
sha = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()[:12]
print(f"\nSaved model: {MODEL_PATH}")
print(f"Saved schema: {SCHEMA_PATH}")
print(f"Saved metrics: {METRICS_PATH}")
print(f"Model version (sha12): {sha}")
