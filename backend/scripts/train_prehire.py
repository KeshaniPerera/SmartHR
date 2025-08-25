# backend/scripts/train_prehire.py
import os, json, joblib
import pandas as pd
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import sklearn

BASE = Path(__file__).resolve().parents[1]
csv_path = BASE / "data" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
out_dir = BASE / "apps" / "prehire" / "artifacts"
out_dir.mkdir(parents=True, exist_ok=True)

print("Using sklearn:", sklearn.__version__)
print("Reading:", csv_path)

df = pd.read_csv(csv_path)
df.columns = [c.strip().replace(" ", "_") for c in df.columns]
for c in ["EmployeeCount","Over18","StandardHours","EmployeeNumber"]:
    if c in df.columns: df.drop(columns=c, inplace=True)

y = df["Attrition"].map({"Yes":1, "No":0}).astype(int)

PREHIRE_COLS = [
    "Age","Gender","BusinessTravel","Department","Education","EducationField",
    "JobRole","MaritalStatus","DistanceFromHome","TotalWorkingYears",
    "NumCompaniesWorked","StockOptionLevel","TrainingTimesLastYear",
]
X = df[PREHIRE_COLS].copy()

num_cols = X.select_dtypes(include=["int64","float64"]).columns.tolist()
cat_cols = X.select_dtypes(include=["object"]).columns.tolist()

pre = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num_cols),
    ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")), ("oh", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
])

clf = RandomForestClassifier(
    n_estimators=400,
    min_samples_split=4,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

pipe = Pipeline([("pre", pre), ("clf", clf)])

Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
pipe.fit(Xtr, ytr)

joblib.dump(pipe, out_dir / "prehire_attrition.pkl")
with open(out_dir / "prehire_schema.json", "w") as f:
    json.dump({"feature_order": PREHIRE_COLS, "sklearn_version": sklearn.__version__}, f, indent=2)

print("Saved:", out_dir / "prehire_attrition.pkl")
print("Saved:", out_dir / "prehire_schema.json")
