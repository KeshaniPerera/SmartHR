import os, math, time
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi
from openai import OpenAI

# load env
BASE = os.path.dirname(os.path.dirname(__file__))  # backend/
load_dotenv(os.path.join(BASE, ".env"))

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB  = os.getenv("MONGO_DB", "smarthr")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=10000)
db = client[MONGO_DB]

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
    # OpenAI embeddings: returns list[float] of length 1536 for -3-small
    r = oa.embeddings.create(model=EMBED_MODEL, input=text)
    return r.data[0].embedding

def main():
    col = db.policies
    cur = col.find({}, {"_id": 1, "title": 1, "category":1, "tags":1, "aliases":1, "policy_description":1, "embedding":1})
    total = col.count_documents({})
    done = 0
    for d in cur:
        done += 1
        if isinstance(d.get("embedding"), list) and len(d["embedding"]) > 0:
            print(f"[{done}/{total}] skip {d['title']} (has embedding)")
            continue
        text = build_text(d)
        vec = embed(text)
        col.update_one({"_id": d["_id"]}, {"$set": {"embedding": vec}})
        print(f"[{done}/{total}] embedded {d['title']} ({len(vec)} dims)")
        time.sleep(0.05)  # gentle pacing
    print("Done.")

if __name__ == "__main__":
    main()
