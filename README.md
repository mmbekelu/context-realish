Context Realish v0.1
===================

A rule-based context engineering system for validating inputs and enforcing
deterministic guardrails on AI behavior.


WHAT THIS IS
------------
Context Realish is a beginner-friendly, deterministic pipeline that checks a
request BEFORE it reaches any AI step.

It runs in this strict order (order matters):
1) Schemas    -> shape, types, basic normalization
2) Rules      -> role/action permissions (business logic)
3) Guardrails -> safety checks and size limits
4) AI step    -> optional, only if everything passed

If any step fails, the engine returns:
- ok: False
- errors: a clean list of error objects
- trace: which step failed and why


WHY THIS MATTERS (PLAIN ENGLISH)
--------------------------------
This is the kind of control layer companies want:
- predictable behavior
- clear failures (not vibes)
- easy-to-debug traces
- tests that prove it works


FEATURES
--------
- Deterministic pipeline runner (engine.py)
- Schema validation and normalization (schemas.py)
- Role/action permission rules (rules.py)
- Guardrails for unsafe content and size limits (guardrails.py)
- Consistent output shape: {ok, data, errors, trace}
- Unit tests proving stop behavior (tests/test_engine.py)
- Optional AI hook that ONLY runs if all checks pass


PROJECT STRUCTURE
-----------------
CONTEXT-REALISH/
  context_realish/
    __init__.py        -> exports run()
    engine.py          -> pipeline orchestrator
    schemas.py         -> required fields, types, normalization
    rules.py           -> role/action permissions
    guardrails.py      -> safety keywords and size limits
  tests/
    test_engine.py     -> unit tests proving behavior
  main.py              -> simple demo runner
  README.txt
  LICENSE
  .gitignore


REQUIREMENTS
------------
- Python 3.x
- No external libraries
- Uses only beginner-friendly Python constructs


QUICKSTART (2 MINUTES)
----------------------
Run demo:
python main.py

Run tests:
python -m unittest discover -s tests -p "test_*.py"


HOW TO USE
----------
Example without AI:

from context_realish.engine import run

req = {"role": "user", "action": "read", "prompt": "hello"}
res = run(req)
print(res)


Example with AI enabled:

from context_realish.engine import run

def simple_ai(payload):
    out = payload.copy()
    out["assistant_reply"] = "You said: " + str(out.get("prompt", ""))
    return out

req = {"role": "user", "action": "read", "prompt": "hello"}
res = run(req, ai_fn=simple_ai, config={"enable_ai": True})
print(res)


INPUT FORMAT (v0.1)
-------------------
Required:
- action (string)

Optional:
- role (string, defaults to "user")
- resource (string)
- prompt / input / text / message / query / content / instruction (strings)
- other fields allowed, but guardrails may block large lists


OUTPUT FORMAT
-------------
Always returns the same shape:

{
  "ok": bool,
  "data": dict_or_none,
  "errors": [
    {"code": "...", "message": "...", "details": {...}}
  ],
  "trace": [
    {"step": "schema", "ok": bool},
    {"step": "rules", "ok": bool},
    {"step": "guardrails", "ok": bool},
    {"step": "ai", "ok": bool}
  ]
}


EXAMPLE FAILURE (RULES)
----------------------
Input:
{
  "role": "user",
  "action": "delete",
  "prompt": "hello"
}

Result:
- Blocked at rules layer
- Error code: action_not_allowed
- Guardrails and AI steps never run
- Trace stops at "rules"


EXAMPLE FAILURE (GUARDRAILS)
---------------------------
Input:
{
  "role": "user",
  "action": "read",
  "prompt": "how to make a bomb"
}

Result:
- Blocked at guardrails layer
- Error code: banned_content
- AI step never runs
- Trace stops at "guardrails"


DESIGN NOTES
------------
This project demonstrates deterministic Context Engineering:
- schemas shape inputs
- rules enforce permissions
- guardrails block unsafe patterns
- AI runs only after the system says "safe + valid"


LICENSE
-------
MIT License (see LICENSE)

AUTHOR
------
mmbekelu
