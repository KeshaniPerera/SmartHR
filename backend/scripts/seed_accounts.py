# backend/scripts/seed_accounts.py
import os, datetime, bcrypt, random
from pathlib import Path

# Allow "apps" imports when running `python backend/scripts/seed_accounts.py`
BASE_DIR = Path(__file__).resolve().parents[1]
import sys
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smarthr.settings")

from apps.common.mongo import get_db  # <-- your existing helper

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def main():
    db = get_db()
    col = db["accounts"]

    # ensure unique index on emp_id
    col.create_index("emp_id", unique=True)

    # Two HR users
    users = [
        {"emp_id": "E001", "account_type": "hr", "password": "Password@001"},
        {"emp_id": "E002", "account_type": "hr", "password": "Password@002"},
    ]

    # Eight employees
    for i in range(3, 11):  # E003..E010
        users.append({
            "emp_id": f"E0{i}",
            "account_type": "employee",
            "password": f"Password@{i:03d}"
        })

    docs = []
    now = datetime.datetime.utcnow()
    for u in users:
        docs.append({
            "emp_id": u["emp_id"],
            "password_hash": hash_pw(u["password"]),
            "account_type": u["account_type"],   # 'hr' | 'employee'
            "status": "active",
            "created_at": now,
        })

    # Upsert by emp_id
    for d in docs:
        col.update_one({"emp_id": d["emp_id"]}, {"$set": d}, upsert=True)

    print("Seed complete. Created/updated", len(docs), "accounts.")
    print("Sample creds:")
    print("  HR        -> E001 / Password@001")
    print("  Employee  -> E003 / Password@003")

if __name__ == "__main__":
    main()
