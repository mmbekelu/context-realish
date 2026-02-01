
# context_realish/rules.py

"""
Rules = business logic permissions (NOT safety keywords, that's guardrails).

Goal:
- Decide what actions are allowed based on role + action + context
- Return explainable errors
- Stay deterministic and simple (v0.1)

Expected return shape (matches engine.py):
    (payload_or_same, errors_list)

errors_list items look like:
    {"code": "...", "message": "...", "details": {...}}
"""


# ---- Config (v0.1) ----

ALLOWED_ROLES = ["user", "admin", "system"]

# What each role is allowed to do (example actions)
ROLE_ACTIONS = {
    "user": ["read", "ask", "summarize"],
    "admin": ["read", "ask", "summarize", "write", "delete"],
    "system": ["read", "ask", "summarize"],  # keep system limited in v0.1
}


def _err(code, message, details=None):
    if details is None:
        details = {}
    return {"code": code, "message": message, "details": details}


def check_rules(payload):
    """
    Main rule check.

    Looks for these fields (if missing, rules can still run safely):
      - role: "user" | "admin" | "system"
      - action: e.g. "read", "write", "delete"
      - resource: optional (what is being acted on)
    """
    errors = []

    role = payload.get("role")
    action = payload.get("action")
    resource = payload.get("resource")  # optional

    # 1) Unknown role
    if role is not None and role not in ALLOWED_ROLES:
        errors.append(
            _err(
                "invalid_role",
                "Role is not allowed.",
                {"role": role, "allowed_roles": ALLOWED_ROLES},
            )
        )
        return payload, errors  # stop early (deterministic)

    # If role is missing, treat it as "user" in v0.1 (safe default)
    if role is None:
        role = "user"

    # 2) Missing action (rules can't decide)
    if action is None:
        errors.append(
            _err(
                "missing_action",
                "Missing required field: action",
                {"required": ["action"], "example": "read"},
            )
        )
        return payload, errors

    # 3) Action not allowed for role
    allowed_actions = ROLE_ACTIONS.get(role, [])
    if action not in allowed_actions:
        errors.append(
            _err(
                "action_not_allowed",
                "Action is not allowed for this role.",
                {"role": role, "action": action, "allowed_actions": allowed_actions},
            )
        )
        return payload, errors

    # 4) Example extra rule: only admin can delete anything
    if action == "delete" and role != "admin":
        errors.append(
            _err(
                "delete_requires_admin",
                "Only admin can perform delete actions.",
                {"role": role, "action": action},
            )
        )
        return payload, errors

    # 5) Example resource rule: user cannot write to "system_config"
    if action == "write" and role == "user" and resource == "system_config":
        errors.append(
            _err(
                "protected_resource",
                "Users cannot write to protected resources.",
                {"role": role, "action": action, "resource": resource},
            )
        )
        return payload, errors

    # If passed, return payload (optionally normalized)
    normalized = payload.copy()
    normalized["role"] = role  # ensure default applied consistently
    normalized["_rules"] = {"checked": True, "role": role, "action": action}

    return normalized, errors


# Alias so engine can find it if you rename later
apply_rules = check_rules
