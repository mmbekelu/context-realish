
# context_realish/schemas.py

"""
Schemas = "shape validation" (required fields, types, basic formats).

Goal:
- Make sure incoming request has the fields we expect
- Normalize small things (trim strings, default values)
- Return (normalized_payload, errors)

This file should NOT:
- Decide permissions (that's rules.py)
- Block unsafe topics (that's guardrails.py)
"""


# ---- Config (v0.1) ----

ALLOWED_ROLES = ["user", "admin", "system"]
ALLOWED_ACTIONS = ["read", "ask", "summarize", "write", "delete", "export"]

# For v0.1 we treat these fields as the "main" request fields.
# You can expand later as your project grows.
REQUIRED_FIELDS = ["action"]  # role is optional (we default it later in rules.py)


def _err(code, message, details=None):
    if details is None:
        details = {}
    return {"code": code, "message": message, "details": details}


def _is_nonempty_string(x):
    return isinstance(x, str) and x.strip() != ""


def validate_request(payload):
    """
    Validate shape + types.

    Returns:
      (normalized_payload, errors_list)

    Expected payload fields (v0.1):
      - role: optional str
      - action: required str
      - resource: optional str
      - prompt/text/message/etc: optional str (guardrails scans these)
    """
    errors = []
    normalized = payload.copy()

    # 1) Required fields present
    for field in REQUIRED_FIELDS:
        if field not in normalized:
            errors.append(
                _err(
                    "missing_field",
                    f"Missing required field: {field}",
                    {"field": field, "required_fields": REQUIRED_FIELDS},
                )
            )

    # If required fields are missing, we can return early
    if errors:
        return normalized, errors

    # 2) Validate "action"
    action = normalized.get("action")

    if not _is_nonempty_string(action):
        errors.append(
            _err(
                "invalid_action_type",
                "Field 'action' must be a non-empty string.",
                {"action": action},
            )
        )
    else:
        action_clean = action.strip().lower()
        normalized["action"] = action_clean

        # optional allow-list for actions (schema-level)
        if action_clean not in ALLOWED_ACTIONS:
            errors.append(
                _err(
                    "unknown_action",
                    "Action is not recognized.",
                    {"action": action_clean, "allowed_actions": ALLOWED_ACTIONS},
                )
            )

    # 3) Validate "role" if provided (optional)
    role = normalized.get("role")

    if role is not None:
        if not _is_nonempty_string(role):
            errors.append(
                _err(
                    "invalid_role_type",
                    "Field 'role' must be a non-empty string if provided.",
                    {"role": role},
                )
            )
        else:
            role_clean = role.strip().lower()
            normalized["role"] = role_clean

            # schema checks it exists; rules decides what it can do
            if role_clean not in ALLOWED_ROLES:
                errors.append(
                    _err(
                        "unknown_role",
                        "Role is not recognized.",
                        {"role": role_clean, "allowed_roles": ALLOWED_ROLES},
                    )
                )

    # 4) Optional string fields: normalize whitespace
    # Keep this small + predictable: only normalize if field exists and is a string
    for field in ["resource", "prompt", "input", "text", "message", "query", "content", "instruction"]:
        if field in normalized and isinstance(normalized[field], str):
            normalized[field] = normalized[field].strip()

    # 5) Add schema metadata for observability
    normalized["_schema"] = {
        "validated": True,
        "required_fields": REQUIRED_FIELDS,
    }

    return normalized, errors


# Alias so engine can find it if you rename later
validate = validate_request
schema_validate = validate_request
