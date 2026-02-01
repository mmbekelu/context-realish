# context_realish/engine.py

"""
Engine = deterministic pipeline runner.

Order matters:
1) Schema validation (shape + types)
2) Rules (business logic permissions)
3) Guardrails (safety / banned patterns)
4) Optional AI step (only if everything passed)

This version uses ONLY beginner-friendly Python:
- dicts, lists, loops, if-statements, functions, .get(), imports
"""


def _step_trace(step, ok, info=None):
    """Small helper to keep trace format consistent."""
    if info is None:
        info = {}
    return {"step": step, "ok": ok, "info": info}


def _normalize_errors(raw_errors, default_code, step_name):
    """
    Convert errors into a consistent list of dicts:
    {"code": "...", "message": "...", "details": {...}}
    """
    normalized = []

    if raw_errors is None:
        return normalized

    for e in raw_errors:
        # If it's already a dict error
        if isinstance(e, dict):
            code = e.get("code", default_code)
            message = e.get("message", "Error")
            details = e.get("details", {})

            # allow extra keys too
            if "details" not in e:
                # move other keys into details
                details = {}
                for k, v in e.items():
                    if k not in ["code", "message"]:
                        details[k] = v

            normalized.append({"code": str(code), "message": str(message), "details": details})

        # If it's just a string
        else:
            normalized.append(
                {"code": default_code, "message": str(e), "details": {"step": step_name}}
            )

    return normalized


def _call_layer(module, fn_names, payload):
    """
    Try function names inside a module. If found, call it.

    Allowed returns:
    1) (new_payload, errors_list)
    2) errors_list
    3) new_payload (dict)
    4) None

    Returns: (new_payload_or_None, normalized_errors, meta_info)
    """
    for name in fn_names:
        fn = getattr(module, name, None)
        if callable(fn):
            out = fn(payload)
            meta = {"called": name}

            new_payload = None
            raw_errors = []

            # (payload, errors)
            if isinstance(out, tuple) and len(out) == 2:
                new_payload = out[0]
                raw_errors = out[1]

            # errors list
            elif isinstance(out, list):
                raw_errors = out

            # payload dict
            elif isinstance(out, dict):
                new_payload = out

            # None is fine = no-op
            elif out is None:
                pass

            # unexpected
            else:
                raw_errors = [f"Unexpected return type from {module.__name__}.{name}: {type(out)}"]

            errors = _normalize_errors(raw_errors, default_code="layer_error", step_name=name)
            return new_payload, errors, meta

    return None, [], {"called": None, "note": "no matching function found"}


def run(request, ai_fn=None, config=None):
    """
    Run the pipeline and return a dict result:

    {
      "ok": bool,
      "data": dict,
      "errors": [ {code, message, details}, ... ],
      "trace": [ {step, ok, info}, ... ]
    }

    config (optional dict):
    - enable_ai: bool
    - strict: bool  (if True: rules errors block)
    """
    if config is None:
        config = {}

    enable_ai = config.get("enable_ai", False)
    strict = config.get("strict", True)

    result = {
        "ok": False,
        "data": None,
        "errors": [],
        "trace": [],
    }

    # Import here to reduce circular import problems
    from . import schemas, rules, guardrails

    payload = request.copy()  # don't mutate caller's dict

    # 1) Schema
    new_payload, errors, meta = _call_layer(
        schemas,
        ("validate_request", "validate", "schema_validate"),
        payload,
    )
    if new_payload is not None:
        payload = new_payload

    result["trace"].append(_step_trace("schema", ok=(len(errors) == 0), info=meta))

    if errors:
        # schema errors always block
        for e in errors:
            result["errors"].append({"code": "schema_error", "message": e["message"], "details": e["details"]})
        result["data"] = payload
        return result

    # 2) Rules
    new_payload, errors, meta = _call_layer(
        rules,
        ("check_rules", "apply_rules", "evaluate_rules", "validate_rules"),
        payload,
    )
    if new_payload is not None:
        payload = new_payload

    result["trace"].append(_step_trace("rules", ok=(len(errors) == 0), info=meta))

    if errors and strict:
        for e in errors:
            result["errors"].append({"code": "rule_violation", "message": e["message"], "details": e["details"]})
        result["data"] = payload
        return result

    # 3) Guardrails
    new_payload, errors, meta = _call_layer(
        guardrails,
        ("check_guardrails", "enforce_guardrails", "guardrail_check"),
        payload,
    )
    if new_payload is not None:
        payload = new_payload

    result["trace"].append(_step_trace("guardrails", ok=(len(errors) == 0), info=meta))

    if errors:
        for e in errors:
            result["errors"].append({"code": "guardrail_block", "message": e["message"], "details": e["details"]})
        result["data"] = payload
        return result

    # 4) Optional AI step
    if enable_ai and ai_fn is not None:
        try:
            ai_out = ai_fn(payload)
            if not isinstance(ai_out, dict):
                raise TypeError("ai_fn must return a dict")

            payload = ai_out
            result["trace"].append(_step_trace("ai", ok=True, info={"called": True}))
        except Exception as ex:
            result["trace"].append(_step_trace("ai", ok=False, info={"called": True}))
            result["errors"].append({"code": "ai_error", "message": str(ex), "details": {}})
            result["data"] = payload
            return result
    else:
        result["trace"].append(_step_trace("ai", ok=True, info={"called": False}))

    # Success
    result["ok"] = True
    result["data"] = payload
    return result
