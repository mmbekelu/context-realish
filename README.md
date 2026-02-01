Context Realish v0.1
===================

# Context Realish
A rule-based context engineering system for validating inputs and enforcing deterministic guardrails on AI behavior.

What this is
------------
Context Realish is a beginner-friendly, deterministic pipeline that checks a request BEFORE it reaches any AI step.

It runs in this order (order matters):
1) Schemas   -> shape + types + basic normalization
2) Rules     -> role/action permissions (business logic)
3) Guardrails-> safety checks + size limits
4) AI step   -> optional, only if everything passed

If any step fails, the engine returns:
- ok: False
- errors: a clean list of error objects
- trace: which step failed and why

Why this matters (in plain English)
-----------------------------------
This is the kind of "control layer" that companies want:
- predictable behavior
- clear failures (not vibes)
- easy-to-debug traces
- test coverage to prove it works

Features
--------
- Deterministic pipeline runner (engine.py)
- Schema validation + normalization (schemas.py)
- Role/action permission rules (rules.py)
- Guardrails for unsafe/disallowed content + size limits (guardrails.py)
- Consistent result shape: {ok, data, errors, trace}
- Unit tests (tests/test_engine.py)
- Optional AI hook (ai_fn) that ONLY runs if checks pass

Project structure
-----------------
CONTEXT-REALISH/
  context_realish/
    __init__.py        -> exports run()
    engine.py          -> pipeline orchestrator (schema -> rules -> guardrails -> ai)
    schemas.py         -> required fields, types, normalization
    rules.py           -> role/action permissions + deterministic rule errors
    guardrails.py      -> safety keyword checks + max length + max list items
  tests/
    test_engine.py     -> unit tests proving behavior
  main.py              -> simple demo runner (optional AI example)
  README.md            -> (you can replace this with README.txt if you want)
  LICENSE
  .gitignore

Requirements
------------
- Python 3.x (no external libraries)
- Works with beginner-friendly Python (dicts, lists, loops, if-statements, functions, imports)

Quickstart (2 minutes)
----------------------
From the project root folder:

1) Run the demo:
   python main.py

2) Run tests:
   python -m unittest discover -s tests -p "test_*.py"

How to use it
-------------
Import and run the engine:

Example (no AI step):
  from context_realish.engine import run

  req = {"role": "user", "action": "read", "prompt": "hello"}
  res = run(req)

  print(res)

Example (with AI step enabled):
  from context_realish.engine import run

  def simple_ai(payload):
      out = payload.copy()
      out["assistant_reply"] = "You said: " + str(out.get("prompt", ""))
      return out

  req = {"role": "user", "action": "read", "prompt": "hello"}
  res = run(req, ai_fn=simple_ai, config={"enable_ai": True})

  print(res)

Input format (v0.1)
-------------------
Minimum required field:
- action (string)

Optional fields:
- role (string)         -> if missing, defaults to "user" in rules.py
- resource (string)
- prompt/input/text/message/query/content/instruction (strings)
- any other fields are allowed, but guardrails may block huge lists

Output format (always the same shape)
-------------------------------------
The engine returns a dict like:

{
  "ok": bool,
  "data": dict_or_none,
  "errors": [
    {"code": "...", "message": "...", "details": {...}},
    ...
  ],
  "trace": [
    {"step": "schema", "ok": bool, "info": {...}},
    {"step": "rules", "ok": bool, "info": {...}},
    {"step": "guardrails", "ok": bool, "info": {...}},
    {"step": "ai", "ok": bool, "info": {...}},
  ]
}

What each file does (simple)
----------------------------
context_realish/engine.py
- Runs the pipeline in a strict order.
- Normalizes errors.
- Produces a consistent result with trace.

context_realish/schemas.py
- Checks REQUIRED_FIELDS (v0.1: action).
- Validates types for action/role if provided.
- Normalizes whitespace + lowercases action/role.
- Adds _schema metadata.

context_realish/rules.py
- Business logic permissions (NOT safety scanning).
- Checks role/action combos.
- Adds _rules metadata (checked, role, action).
- Defaults missing role to "user".

context_realish/guardrails.py
- Safety/policy checks + size limits.
- Checks max text length and max list items.
- Scans common text fields for disallowed content.
- Adds _guardrails metadata (scanned_chars, errors).

tests/test_engine.py
- Proves pipeline order and stop behavior:
  - schema fails stop early
  - rules fail can block (strict=True) or not block (strict=False)
  - guardrails fail stop before AI
  - AI step must return a dict or it fails

Configuration (v0.1)
--------------------
config is optional. Supported keys:
- enable_ai (bool): default False
  If True and ai_fn is provided, AI step runs after guardrails pass.

- strict (bool): default True
  If True, rules violations block.
  If False, rules errors are recorded in trace but do not block (v0.1 behavior).

Design notes (why this is "Context Engineering")
------------------------------------------------
This repo is a "deterministic control layer" that sits before AI:
- Schemas keep inputs shaped and consistent
- Rules enforce permissions and business logic
- Guardrails block unsafe/disallowed patterns and abuse
- AI only runs after the system says "safe + valid"

Roadmap ideas (optional next upgrades)
--------------------------------------
- Add more schema rules (type checks for more fields)
- Expand ROLE_ACTIONS into config-driven rules
- Add better text scanning (still deterministic)
- Add more tests (edge cases, fuzz-like cases, performance checks)
- Add examples/ folder with sample requests + outputs

License
-------
MIT License (see LICENSE)

Author
------
mmbekelu
