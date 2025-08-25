import os, json, time
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.read_preferences import SecondaryPreferred
import certifi
from openai import OpenAI

# load env
BASE = os.path.dirname(os.path.dirname(__file__))  # backend/
load_dotenv(os.path.join(BASE, ".env"))

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB  = os.getenv("MONGO_DB", "smarthr")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
OUT_PATH = os.path.join(BASE, "scripts", "update_embeddings.js")

# connect for READS ONLY (prefer secondaries to avoid needing primary)
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000,
    read_preference=SecondaryPreferred(),   # <- key
)
db = client[MONGO_DB]
col = db.policies

oa = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL") or None)

def build_text(doc):
    parts = [
        doc.get("title",""),
        doc.get("category",""),
        " ".join(doc.get("tags",[]) or []),
        " ".join(doc.get("aliases",[]) or []),
        doc.get("policy_description","")
    ]
    return "\n".join([p for p in parts if p]).strip()

def embed(text):
    r = oa.embeddings.create(model=EMBED_MODEL, input=text)
    return r.data[0].embedding

def js_str(s: str) -> str:
    # safely quote a JS string (for slug)
    return s.replace("\\", "\\\\").replace('"', '\\"')

def main():
    docs = list(col.find({}, {"_id": 0, "slug": 1, "title": 1, "category":1, "tags":1, "aliases":1, "policy_description":1, "embedding":1}))
    print(f"Found {len(docs)} policy docs to process.")
    updates = []
    for i, d in enumerate(docs, 1):
        if isinstance(d.get("embedding"), list) and d["embedding"]:
            print(f"[{i}/{len(docs)}] skip {d['slug']} (has embedding)")
            continue
        text = build_text(d)
        vec = embed(text)
        # build a mongosh updateOne line by slug
        updates.append(
            f'db.policies.updateOne({{ slug: "{js_str(d["slug"])}" }}, {{ $set: {{ embedding: {json.dumps(vec)} }} }});'
        )
        print(f"[{i}/{len(docs)}] prepared update for {d['slug']}")
        time.sleep(0.05)

    if not updates:
        print("Nothing to update. All docs already have embeddings.")
        return

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("use('smarthr');\n")
        for u in updates:
            f.write(u + "\n")

    print(f"Wrote {len(updates)} updates to {OUT_PATH}")
    print("Next run:\n  mongosh \"<your Atlas SRV URI>/smarthr\" " + OUT_PATH)

if __name__ == "__main__":
    main()
