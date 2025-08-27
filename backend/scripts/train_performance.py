import os, json, hashlib
from pathlib import Path
import numpy as np, pandas as pd, joblib, sklearn

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
OUT  = BASE / "apps" / "performance" / "artifacts"
OUT.mkdir(parents=True, exist_ok=True)

MODEL_PATH  = OUT / "performance_high.pkl"
SCHEMA_PATH = OUT / "performance_schema.json"
METRICS_PATH= OUT / "performance_metrics.json"

PERFORMANCE_FEATURES = [
    "JobInvolvement","JobLevel","JobSatisfaction","EnvironmentSatisfaction",
    "RelationshipSatisfaction","WorkLifeBalance","YearsAtCompany",
    "YearsInCurrentRole","YearsSinceLastPromotion","YearsWithCurrManager",
    "OverTime","MonthlyIncome","JobRole","Department"
]

print("Using sklearn:", sklearn.__version__)
print("Reading:", DATA)
if not DATA.exists():
    raise FileNotFoundError(f"Dataset not found at {DATA}")

df = pd.read_csv(DATA)

# Target: High performer if PerformanceRating >= 4
if "PerformanceRating" not in df.columns:
    raise KeyError("PerformanceRating not found")
y = (df["PerformanceRating"] >= 4).astype(int)

missing = [c for c in PERFORMANCE_FEATURES if c not in df.columns]
if missing:
    raise KeyError(f"Missing columns: {missing}")

X = df[PERFORMANCE_FEATURES].copy()

cat_cols = ["OverTime", "JobRole", "Department"]
num_cols = [c for c in PERFORMANCE_FEATURES if c not in cat_cols]

pre = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                      ("sc",  StandardScaler())]), num_cols),
    ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                      ("oh",  OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
], remainder="drop")

clf = RandomForestClassifier(
    n_estimators=500,
    min_samples_split=4,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

pipe = Pipeline([("pre", pre), ("clf", clf)])

Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
pipe.fit(Xtr, ytr)

proba = pipe.predict_proba(Xte)[:, 1]
pred  = (proba >= 0.5).astype(int)

acc = accuracy_score(yte, pred)
try:
    auc = roc_auc_score(yte, proba)
except Exception:
    auc = float("nan")
cm = confusion_matrix(yte, pred).tolist()
cr = classification_report(yte, pred, output_dict=True)

metrics = {
    "sklearn_version": sklearn.__version__,
    "accuracy": acc,
    "roc_auc": auc,
    "confusion_matrix": cm,
    "classification_report": cr,
    "n_train": int(len(ytr)),
    "n_test": int(len(yte)),
    "features": PERFORMANCE_FEATURES,
    "label_positive": "High Performer (PerformanceRating >= 4)"
}

print("\n=== Performance (High Performer) metrics ===")
print(f"Accuracy : {acc:.4f}")
print(f"ROC AUC  : {auc:.4f}")
print(f"CM       : {cm}")

joblib.dump(pipe, MODEL_PATH)
with open(SCHEMA_PATH, "w") as f:
    json.dump({"feature_order": PERFORMANCE_FEATURES, "sklearn_version": sklearn.__version__}, f, indent=2)
with open(METRICS_PATH, "w") as f:
    json.dump(metrics, f, indent=2)

sha = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()[:12]
print(f"\nSaved model  : {MODEL_PATH}")
print(f"Saved schema : {SCHEMA_PATH}")
print(f"Saved metrics: {METRICS_PATH}")
print("Model version:", sha)
