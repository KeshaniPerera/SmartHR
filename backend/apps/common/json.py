from bson import ObjectId
from datetime import datetime

def mongo_to_json(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k == "_id":
                out["id"] = str(v) if isinstance(v, ObjectId) else v
            else:
                out[k] = mongo_to_json(v)
        return out
    if isinstance(obj, list):
        return [mongo_to_json(x) for x in obj]
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj
