import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import re


from annotated_types import doc

from apps.common.mongo import get_db
from apps.nlp.router import RouteResult, route
# === Vector search config ===
USE_VECTOR = os.getenv("USE_VECTOR", "1") == "1"
VECTOR_INDEX = os.getenv("ATLAS_VECTOR_INDEX", os.getenv("ATLAS_SEARCH_INDEX", "default"))
EMBED_FIELD  = os.getenv("EMBED_FIELD", "embedding")
EMBED_MODEL  = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

from openai import OpenAI  # used for query-time embedding
_oa_vec = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL") or None)


# Atlas Search config (edit via .env if you changed names)
ATLAS_SEARCH_INDEX = os.getenv("ATLAS_SEARCH_INDEX", "default")
ATLAS_SYNONYMS = os.getenv("ATLAS_SYNONYMS", "hr-synonyms")

# Optional: short answer polish via OpenAI
USE_SUMMARIZER = os.getenv("USE_SUMMARIZER", "0") == "1"
if USE_SUMMARIZER:
    from openai import OpenAI
    _oa = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL") or None)
    SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", "gpt-4o-mini")

def _fmt_date(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    try:
        # show local-ish date only
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return str(dt)

def _summarize_if_enabled(question: str, title: str, body: str) -> str:
    if not USE_SUMMARIZER:
        return body
    try:
        prompt = (
            f"User question: {question}\n"
            f"Policy: {title}\n"
            f"Policy text:\n{body}\n\n"
            "Write a concise 2–3 sentence answer. Be precise. End with: Source: <Policy Title>."
        )
        r = _oa.responses.create(model=SUMMARIZER_MODEL, input=prompt)
        txt = r.output_text.strip()
        return txt or body
    except Exception:
        return body

# -----------------------
# Employee resolution
# -----------------------
def _resolve_employee(emp_id: Optional[str], name: Optional[str]) -> Dict[str, Any]:
    db = get_db()
    if emp_id:
        doc = db.employees.find_one({"emp_id": emp_id}, {"_id": 0})
        if doc:
            return {"ok": True, "employee": doc}
    if name:
        # case-insensitive exact; if not found, try starts-with
        exact = list(db.employees.find({"full_name": {"$regex": f"^{name}$", "$options": "i"}}, {"_id": 0}))
        if len(exact) == 1:
            return {"ok": True, "employee": exact[0]}
        if len(exact) > 1:
            return {"ok": False, "ambiguous": [e["full_name"] for e in exact]}
        prefix = list(db.employees.find({"full_name": {"$regex": f"^{name}", "$options": "i"}}, {"_id": 0}))
        if len(prefix) == 1:
            return {"ok": True, "employee": prefix[0]}
        if len(prefix) > 1:
            return {"ok": False, "ambiguous": [e["full_name"] for e in prefix]}
    return {"ok": False, "reason": "not_found"}

# -----------------------
# Leave actions
# -----------------------
def _act_leave_balance(emp: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    b = db.leave_balances.find_one({"emp_id": emp["emp_id"]}, {"_id": 0})
    if not b:
        return {"text": f"{emp['full_name']}, I couldn't find your leave balance."}
    text = (
        f"{emp['full_name']}, you have {b.get('annual', 0)} annual, "
        f"{b.get('sick', 0)} sick, {b.get('casual', 0)} casual days remaining "
        f"(updated {_fmt_date(b.get('updated_at'))})."
    )
    return {"text": text, "meta": {"balance": b}}

# backend/apps/nlp/executor.py

def _act_leave_status(emp: Dict[str, Any], leave_type: Optional[str]) -> Dict[str, Any]:
    db = get_db()
    q: Dict[str, Any] = {"emp_id": emp["emp_id"]}
    if leave_type:
        q["type"] = leave_type

    # Project out _id and select only JSON-safe fields
    req = db.leave_requests.find(
        q,
        {"_id": 0, "type": 1, "status": 1, "start": 1, "end": 1, "created_at": 1}
    ).sort("created_at", -1).limit(1)

    items = list(req)
    if not items:
        return {"text": f"{emp['full_name']}, I couldn't find any leave requests."}

    r = items[0]
    text = (
        f"Your last leave ({_fmt_date(r.get('start'))} to {_fmt_date(r.get('end'))}, {r.get('type','')}) "
        f"is **{r.get('status','Unknown')}**."
    )
    return {
        "text": text,
        "meta": {
            "request": {
                "type": r.get("type"),
                "status": r.get("status"),
                "start": _fmt_date(r.get("start")),
                "end": _fmt_date(r.get("end")),
                "created_at": _fmt_date(r.get("created_at")),
            }
        }
    }


def _act_leave_howto(leave_type: Optional[str]) -> Dict[str, Any]:
    """
    Try to fetch a 'how to apply leave' policy; otherwise return a short canned guide.
    """
    got = _policy_search_text_first(topic="leave application")
    if got:
        title, body = got["title"], got["policy_description"]
        text = _summarize_if_enabled("How to apply leave", title, body)
        return {"text": text, "meta": {"policy": {"title": title, "slug": got.get("slug")}}}
    # fallback
    base = "Apply leave via the HRIS Leave form. Manager approval is required. Submit at least 1 business day in advance."
    if leave_type:
        base = f"For {leave_type} leave: " + base
    return {"text": base}

# -----------------------
# Policy search helpers
# -----------------------
_SEARCH_PATHS = ["title", "policy_description", "tags", "aliases", "category"]

def _policy_search_text_first(topic: str) -> Optional[Dict[str, Any]]:
    """
    Try Atlas Search text+synonyms; fallback to classic $text.
    Returns top doc or None.
    """
    db = get_db()
    col = db.policies
    # 1) Atlas Search (preferred)
    try:
        pipeline = [
            {"$search": {
                "index": ATLAS_SEARCH_INDEX,
                "text": {
                    "query": topic, "path": _SEARCH_PATHS,
                    "synonyms": ATLAS_SYNONYMS, "matchCriteria": "any"
                }
            }},
            {"$limit": 3},
            {"$project": {"_id": 0, "title": 1, "slug": 1, "policy_description": 1,
                          "score": {"$meta": "searchScore"}}}
        ]
        res = list(col.aggregate(pipeline))
        if res:
            return res[0]
    except Exception:
        pass

    # 2) Classic $text fallback
    try:
        cur = col.find(
            {"$text": {"$search": topic}},
            {"score": {"$meta": "textScore"}, "_id": 0, "title": 1, "slug": 1, "policy_description": 1}
        ).sort([("score", {"$meta": "textScore"})]).limit(1)
        res = list(cur)
        if res:
            return res[0]
    except Exception:
        pass
    return None

def _policy_list(topic: Optional[str], limit: int = 10) -> List[Dict[str, Any]]:
    db = get_db()
    col = db.policies
    if topic:
        try:
            pipeline = [
                {"$search": {
                    "index": ATLAS_SEARCH_INDEX,
                    "text": {"query": topic, "path": _SEARCH_PATHS,
                             "synonyms": ATLAS_SYNONYMS, "matchCriteria": "any"}
                }},
                {"$limit": limit},
                {"$project": {"_id": 0, "title": 1, "slug": 1,
                              "score": {"$meta": "searchScore"}}}
            ]
            return list(col.aggregate(pipeline))
        except Exception:
            pass
        try:
            cur = col.find({"$text": {"$search": topic}},
                           {"_id": 0, "title": 1, "slug": 1,
                            "score": {"$meta": "textScore"}}).limit(limit)
            return list(cur)
        except Exception:
            pass
    # no topic → list recent or alphabetical
    return list(col.find({}, {"_id": 0, "title": 1, "slug": 1}).sort("title", 1).limit(limit))

def _policy_count(topic: Optional[str]) -> int:
    db = get_db()
    col = db.policies
    if topic:
        # Use $searchMeta total count when topic provided
        try:
            res = list(col.aggregate([
                {"$searchMeta": {
                    "index": ATLAS_SEARCH_INDEX,
                    "count": {"type": "total"},
                    "text": {"query": topic, "path": _SEARCH_PATHS,
                             "synonyms": ATLAS_SYNONYMS, "matchCriteria": "any"}
                }}
            ]))
            if res and "count" in res[0] and "total" in res[0]["count"]:
                return int(res[0]["count"]["total"])
        except Exception:
            pass
        # fallback rough count with $text
        try:
            return col.count_documents({"$text": {"$search": topic}})
        except Exception:
            pass
    # no topic → total policies
    return col.estimated_document_count()


def _embed_query(text: str):
    """
    Get a query embedding using OpenAI (same model dims as your stored vectors).
    """
    try:
        r = _oa_vec.embeddings.create(model=EMBED_MODEL, input=text)
        return r.data[0].embedding
    except Exception:
        return None

def _policy_search_vector(topic: str) -> Optional[Dict[str, Any]]:
    """
    Atlas vector search fallback on the 'embedding' field.
    """
    vec = _embed_query(topic)
    if not vec:
        return None
    col = get_db().policies
    try:
        pipeline = [
            {"$vectorSearch": {
                "index": VECTOR_INDEX,   # e.g., "default"
                "path": EMBED_FIELD,     # e.g., "embedding"
                "queryVector": vec,
                "numCandidates": 100,
                "limit": 3
            }},
            {"$project": {
                "_id": 0, "title": 1, "slug": 1, "policy_description": 1,
                "score": {"$meta": "vectorSearchScore"}
            }}
        ]
        res = list(col.aggregate(pipeline))
        return res[0] if res else None
    except Exception:
        return None
    
def _count_employees(dept: Optional[str] = None) -> int:
    db = get_db()
    if dept:
        rx = {"$regex": f"^{re.escape(dept)}$", "$options": "i"}
        return db.employees.count_documents({"$or": [{"dept": rx}, {"department": rx}, {"department_name": rx}]})
    # exact count is fine; estimated is also ok for large sets
    return db.employees.count_documents({})


def _count_leave_requests(status: Optional[str] = None) -> int:
    db = get_db()
    q: Dict[str, Any] = {}
    if status:
        # normalize status keywords
        status_map = {
            "pending": "Pending",
            "approved": "Approved",
            "rejected": "Rejected",
        }
        norm = status_map.get(status.lower(), status)
        q["status"] = {"$regex": f"^{re.escape(norm)}$", "$options": "i"}
    return db.leave_requests.count_documents(q)



# -----------------------
# Public entry: execute
# -----------------------
def execute_free_text(user_text: str) -> Dict[str, Any]:
    """
    Orchestrates: route → run action(s) → return a text answer + meta.
    """
    parsed: RouteResult = route(user_text)

    # Handle intents
    if parsed.intent == "leave_balance":
        who = _resolve_employee(parsed.employee.emp_id, parsed.employee.name)
        if not who.get("ok"):
            if "ambiguous" in who:
                names = ", ".join(who["ambiguous"][:5])
                return {"text": f"I found multiple matches: {names}. Please specify the full name or employee ID."}
            return {"text": "I couldn't identify the employee. Please provide your employee ID or full name."}
        return _act_leave_balance(who["employee"])

    if parsed.intent == "leave_status":
        who = _resolve_employee(parsed.employee.emp_id, parsed.employee.name)
        if not who.get("ok"):
            if "ambiguous" in who:
                names = ", ".join(who["ambiguous"][:5])
                return {"text": f"I found multiple matches: {names}. Please specify."}
            return {"text": "I couldn't identify the employee. Please provide your employee ID or full name."}
        return _act_leave_status(who["employee"], parsed.leave_type)

    if parsed.intent == "leave_howto":
        return _act_leave_howto(parsed.leave_type)

    if parsed.intent == "utility_count":
        low = user_text.lower()

        # 1) EMPLOYEES (match employees/staff/headcount/people/workers)
        if re.search(r"\b(employees?|staff|headcount|people|workers)\b", low):
            # optional dept: "in it department", "in engineering dept", "within hr team"
            m = re.search(
                r"\b(?:in|within)\s+(?:the\s+)?([a-z0-9 &/\-]+?)(?:\s+(?:dept|department|team|division)|\?|$)",
                low
            )
            dept = m.group(1).strip() if m else None
            n = _count_employees(dept)
            if dept:
                return {"text": f"There are {n} employees in the {dept.title()} department.", "meta": {"count": n, "dept": dept}}
            return {"text": f"There are {n} employees in the company.", "meta": {"count": n}}

        # 2) LEAVE REQUESTS (total or by status)
        if "leave" in low and ("request" in low or "requests" in low):
            status = None
            for k in ["pending", "approved", "rejected"]:
                if k in low:
                    status = k
                    break
            n = _count_leave_requests(status)
            if status:
                return {"text": f"There are {n} {status} leave requests.", "meta": {"count": n, "status": status}}
            return {"text": f"There are {n} leave requests in total.", "meta": {"count": n}}

        # 3) POLICIES (fallback: existing behavior)
        topic = parsed.policy_topic
        if not topic and "how many" in low:
            after = low.split("how many", 1)[1].strip()
            topic = after.replace("policies", "").strip() or None
        n = _policy_count(topic)
        if topic:
            return {"text": f"There are {n} policies matching “{topic}”.", "meta": {"count": n, "topic": topic}}
        return {"text": f"We have {n} policies.", "meta": {"count": n}}
    
    if parsed.intent == "employee_lookup":
        return _act_employee_lookup(parsed.employee.emp_id, parsed.employee.name, parsed.meta.directory_field)


    if parsed.intent == "utility_list":
        lst = _policy_list(parsed.policy_topic)
        if not lst:
            return {"text": "I couldn't find any matching policies to list."}
        lines = [f"• {x['title']} ({x.get('slug','')})" for x in lst]
        return {"text": "Here are some policies:\n" + "\n".join(lines), "meta": {"items": lst}}
    if parsed.intent == "utility_count":
        low = user_text.lower()

        # 3.1 Employees count (supports optional "in <dept>" phrase)
        if "employee" in low:  # matches "employee" or "employees"
            dept = None
            # capture "in <dept> (department|team)?" e.g., "in engineering department"
            m = re.search(r"in\s+(?:the\s+)?([a-z &/\-]+?)(?:\s+department|\s+team|\?|$)", low)
            if m:
                dept = m.group(1).strip()
            n = _count_employees(dept)
            if dept:
                return {"text": f"There are {n} employees in the {dept.title()} department.", "meta": {"count": n, "dept": dept}}
            return {"text": f"There are {n} employees in the company.", "meta": {"count": n}}

        # 3.2 Leave requests count (supports status: pending/approved/rejected)
        if "leave" in low and ("request" in low or "requests" in low):
            status = None
            for k in ["pending", "approved", "rejected"]:
                if k in low:
                    status = k
                    break
            n = _count_leave_requests(status)
            if status:
                return {"text": f"There are {n} {status} leave requests.", "meta": {"count": n, "status": status}}
            return {"text": f"There are {n} leave requests in total.", "meta": {"count": n}}

        # 3.3 Policies count (existing behavior; optional topic)
        topic = parsed.policy_topic
        if not topic:
            # pull a likely noun after "how many "  e.g., "how many insurance policies"
            if "how many" in low:
                after = low.split("how many", 1)[1].strip()
                topic = after.replace("policies", "").strip() or None
        n = _policy_count(topic)
        if topic:
            return {"text": f"There are {n} policies matching “{topic}”.", "meta": {"count": n, "topic": topic}}
        return {"text": f"We have {n} policies.", "meta": {"count": n}}


# Default: policy_qa (or smalltalk treated as policy_qa attempt)
    topic = parsed.policy_topic or user_text
    doc = _policy_search_text_first(topic)
    if not doc and USE_VECTOR:
        doc = _policy_search_vector(topic)

    if not doc:
        suggestions = _policy_list(topic, limit=5)
        if suggestions:
            s = "\n".join(f"• {x['title']}" for x in suggestions)
            return {"text": f"I couldn't find an exact match. Did you mean:\n{s}"}
        return {"text": "Sorry, I couldn't find a matching policy."}

    title, body = doc["title"], doc.get("policy_description", "")
    answer = _summarize_if_enabled(user_text, title, body)
    if answer == body:
        answer += f"\n\nSource: {title}"
    return {"text": answer, "meta": {"policy": {"title": title, "slug": doc.get("slug")}}}

def _act_employee_lookup(emp_id: Optional[str], name: Optional[str], directory_field: Optional[str]) -> Dict[str, Any]:
    """
    Looks up an employee by emp_id or name and returns the requested field.
    Supports full_name/email/dept/emp_id.
    """
    db = get_db()
    q = {}
    if emp_id:
        q["emp_id"] = emp_id
    elif name:
        q["full_name"] = {"$regex": f"^{name}$", "$options": "i"}
    else:
        return {"text": "Please provide an employee ID or full name."}

    doc = db.employees.find_one(q, {"_id": 0, "emp_id": 1, "full_name": 1, "fullname": 1, "email": 1, "dept": 1})
    if not doc:
        return {"text": "I couldn't find that employee. Check the ID or name."}

    # normalize possible schema variants: full_name vs fullname
    full_name = doc.get("full_name") or doc.get("fullname")

    field = (directory_field or "full_name")
    value = {
        "full_name": full_name,
        "email": doc.get("email"),
        "dept": doc.get("dept"),
        "emp_id": doc.get("emp_id"),
    }.get(field)

    if value is None:
        return {"text": f"I couldn't find {field.replace('_',' ')} for {full_name or doc.get('emp_id') }."}

    # Friendly phrasing
    subject = f"Employee {doc.get('emp_id')}" if emp_id else (full_name or "The employee")
    if field == "full_name":
        return {"text": f"{subject} is {value}."}
    elif field == "email":
        return {"text": f"{subject}'s email is {value}."}
    elif field == "dept":
        return {"text": f"{subject} is in the {value} department."}
    elif field == "emp_id":
        return {"text": f"{full_name}’s employee ID is {value}."}
    return {"text": f"{subject}: {field.replace('_',' ')} = {value}"}
