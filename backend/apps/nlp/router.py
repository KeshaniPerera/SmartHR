# C:\SmartHR\backend\apps\nlp\router.py
import json, os, re
from typing import Optional, Literal
from pydantic import BaseModel, Field

# OpenAI client (new SDK). We'll use Responses API and fall back to Chat Completions.
from openai import OpenAI

# Toggle to bypass OpenAI and use rules only (useful while debugging)
USE_OPENAI_ROUTER = os.getenv("USE_OPENAI_ROUTER", "1") == "1"

# --------------------------
# Intents & data models
# --------------------------
INTENTS = [
    "policy_qa",       # general policy questions
    "leave_balance",   # "how many leaves left"
    "leave_status",    # latest leave request status
    "leave_howto",     # how to apply leave
    "utility_count",   # "how many policies"
    "utility_list",    # "list policies/categories"
    "employee_lookup", # NEW: directory lookups (full name/email/dept/emp_id)
    "smalltalk",
]

LeaveType = Optional[Literal["annual", "sick", "casual"]]

class EmployeeSlot(BaseModel):
    name: Optional[str] = None
    emp_id: Optional[str] = None

class DateRange(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None

class MetaSlot(BaseModel):
    wants_count: bool = False
    wants_list: bool = False
    list_target: Optional[Literal["policies", "categories"]] = None
    directory_field: Optional[Literal["full_name", "email", "dept", "emp_id"]] = None  # NEW

class RouteResult(BaseModel):
    intent: Literal[
        "policy_qa",
        "leave_balance",
        "leave_status",
        "leave_howto",
        "utility_count",
        "utility_list",
        "employee_lookup",   # NEW
        "smalltalk",
    ]
    employee: EmployeeSlot = EmployeeSlot()
    leave_type: LeaveType = None
    date_range: DateRange = DateRange()
    policy_topic: Optional[str] = None
    meta: MetaSlot = MetaSlot()
    confidence: float = 0.0

# JSON schema the model must follow (kept strict)
_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "intent": {"type": "string", "enum": list(INTENTS)},
        "employee": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {"type": ["string", "null"]},
                "emp_id": {"type": ["string", "null"]},
            },
            "required": ["name", "emp_id"]
        },
        "leave_type": {"type": ["string", "null"], "enum": ["annual", "sick", "casual", None]},
        "date_range": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "start": {"type": ["string", "null"]},
                "end": {"type": ["string", "null"]},
            },
            "required": ["start", "end"]
        },
        "policy_topic": {"type": ["string", "null"]},
        "meta": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "wants_count": {"type": "boolean"},
                "wants_list": {"type": "boolean"},
                "list_target": {"type": ["string", "null"], "enum": ["policies", "categories", None]},
                "directory_field": {"type": ["string", "null"], "enum": ["full_name", "email", "dept", "emp_id", None]}
            },
            "required": ["wants_count", "wants_list", "list_target"]
        }
    },
    "required": ["intent", "employee", "leave_type", "date_range", "policy_topic", "meta"]
}

_SYSTEM = (
    "You are an HR NLU router. Output ONLY valid JSON that matches the given schema. "
    "Supported intents: policy_qa, leave_balance, leave_status, leave_howto, utility_count, utility_list, employee_lookup, smalltalk. "
    "If user self-identifies (e.g., 'I am Bob'), set employee.name. If they give an employee ID (e.g., E002), set employee.emp_id. "
    "For 'how many' questions about policies, set intent=utility_count and meta.wants_count=true. "
    "For 'list policies/categories', set intent=utility_list and meta.wants_list=true with list_target. "
    "For directory questions like 'full name of employee id E002' or 'email of Bob', set intent=employee_lookup and meta.directory_field accordingly. "
    "For policy questions, use intent=policy_qa and put a short policy_topic phrase."
)

_EXAMPLES = [
    ("Hi I am Bob, how many leaves I have left?",
     {"intent":"leave_balance","employee":{"name":"Bob","emp_id":None},
      "leave_type":None,"date_range":{"start":None,"end":None},
      "policy_topic":None,
      "meta":{"wants_count":False,"wants_list":False,"list_target":None,"directory_field":None}}),

    ("Any policies in leaving the company?",
     {"intent":"policy_qa","employee":{"name":None,"emp_id":None},
      "leave_type":None,"date_range":{"start":None,"end":None},
      "policy_topic":"leaving the company",
      "meta":{"wants_count":False,"wants_list":False,"list_target":None,"directory_field":None}}),

    ("How many policies do we have?",
     {"intent":"utility_count","employee":{"name":None,"emp_id":None},
      "leave_type":None,"date_range":{"start":None,"end":None},
      "policy_topic":None,
      "meta":{"wants_count":True,"wants_list":False,"list_target":None,"directory_field":None}}),

    ("List policies under workplace rules",
     {"intent":"utility_list","employee":{"name":None,"emp_id":None},
      "leave_type":None,"date_range":{"start":None,"end":None},
      "policy_topic":None,
      "meta":{"wants_count":False,"wants_list":True,"list_target":"policies","directory_field":None}}),

    ("How to apply for annual leave?",
     {"intent":"leave_howto","employee":{"name":None,"emp_id":None},
      "leave_type":"annual","date_range":{"start":None,"end":None},
      "policy_topic":None,
      "meta":{"wants_count":False,"wants_list":False,"list_target":None,"directory_field":None}}),

    # NEW: directory lookups
    ("what is the full name of employee id E002?",
     {"intent":"employee_lookup","employee":{"name":None,"emp_id":"E002"},
      "leave_type":None,"date_range":{"start":None,"end":None},
      "policy_topic":None,
      "meta":{"wants_count":False,"wants_list":False,"list_target":None,"directory_field":"full_name"}}),

    ("email of bob please",
     {"intent":"employee_lookup","employee":{"name":"bob","emp_id":None},
      "leave_type":None,"date_range":{"start":None,"end":None},
      "policy_topic":None,
      "meta":{"wants_count":False,"wants_list":False,"list_target":None,"directory_field":"email"}}),
]

def _messages(user_text: str):
    fewshot = "\n".join(f"User: {u}\nJSON: {json.dumps(j, ensure_ascii=False)}" for u,j in _EXAMPLES)
    return [
        {"role":"system","content": _SYSTEM},
        {"role":"user","content": fewshot + f"\nUser: {user_text}\nJSON:"}
    ]

# Simple heuristics if OpenAI is disabled/unavailable
def _rule_fallback(t: str) -> RouteResult:
    tl = t.lower().strip()

    # employee directory patterns
    if "employee id" in tl or "emp id" in tl or re.search(r"\bid\s*[:=]\s*\w+", tl):
        field = "full_name"
        if "email" in tl: field = "email"
        if "department" in tl or "dept" in tl: field = "dept"
        m = re.search(r"\b([a-z]\d{2,}|e\d+)\b", tl)
        emp_id = m.group(1).upper() if m else None
        return RouteResult(intent="employee_lookup",
                           employee=EmployeeSlot(emp_id=emp_id),
                           meta=MetaSlot(directory_field=field),
                           confidence=0.6)

    if ("full name" in tl and ("employee" in tl or "id" in tl)) or ("email of" in tl):
        return RouteResult(intent="employee_lookup", confidence=0.55)

    # utility
    if any(k in tl for k in ["how many policies", "number of policies", "count policies"]):
        return RouteResult(intent="utility_count", confidence=0.5)
    if ("list" in tl and "policy" in tl) or "show policies" in tl:
        return RouteResult(intent="utility_list", meta=MetaSlot(wants_list=True, list_target="policies"), confidence=0.5)

    # leave
    if "how to apply" in tl and "leave" in tl:
        return RouteResult(intent="leave_howto", confidence=0.5)
    if "status" in tl and "leave" in tl:
        return RouteResult(intent="leave_status", confidence=0.5)
    if "leave" in tl and any(x in tl for x in ["how many", "balance", "left"]):
        m = re.search(r"\bi am ([a-z ]+)\b", tl)
        name = m.group(1).title().strip() if m else None
        return RouteResult(intent="leave_balance", employee=EmployeeSlot(name=name), confidence=0.5)

    # default policy
    return RouteResult(intent="policy_qa", policy_topic=t, confidence=0.4)

def route(user_text: str) -> RouteResult:
    """
    Main entry: returns structured intent/slots.
    If USE_OPENAI_ROUTER=0 or OpenAI fails, falls back to rules.
    """
    if not USE_OPENAI_ROUTER:
        return _rule_fallback(user_text)

    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            timeout=8.0,  # keep UI snappy
        )
        model = os.getenv("ROUTER_MODEL", "gpt-4o-mini")

        # Prefer Responses API with JSON schema
        try:
            resp = client.responses.create(
                model=model,
                input=_messages(user_text),
                response_format={"type":"json_schema","json_schema":{"name":"router_schema","schema":_SCHEMA,"strict":True}},
            )
            raw = resp.output_text
            data = json.loads(raw)
            return RouteResult(**data, confidence=0.85)
        except Exception:
            # Fallback: Chat Completions with JSON mode
            chat = client.chat.completions.create(
                model=model,
                messages=_messages(user_text),
                temperature=0,
                response_format={"type":"json_object"}
            )
            raw = chat.choices[0].message.content
            data = json.loads(raw)
            return RouteResult(**data, confidence=0.75)
    except Exception:
        return _rule_fallback(user_text)
