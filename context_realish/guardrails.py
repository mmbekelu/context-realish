# context_realish/guardrails.py

# Guardrails = safety/policy checks (deterministic)
# Return: (payload_with_metadata, errors_list)

MAX_TEXT_LEN = 2000
MAX_LIST_ITEMS = 50

# Phrases (multi-word)
BANNED_PHRASES = [
    # self-harm / suicide
    "kill myself",
    "end my life",
    "hurt myself",
    "self harm",
    "self-harm",
    "suicide",

    # weapons / violence instructions
    "make a bomb",
    "build a bomb",
    "how to make a bomb",
    "how to build a bomb",
    "homemade explosive",

    # hacking / malware
    "steal password",
    "steal my password",
    "hack an account",
    "bypass login",
    "phishing link",
    "credential stuffing",
    "sql injection",
    "cross site scripting",
    "xss attack",
    "write malware",
    "make malware",
    "ransomware",
    "keylogger",
]

# Single words (one-token)
BANNED_WORDS = {
    # self-harm / suicide
    "suicide", "selfharm",

    # weapons / violence
    "bomb", "explosive", "weapon", "gun", "ammo",

    # hacking / cyber abuse
    "phishing", "keylogger", "malware", "ransomware", "ddos", "botnet", "backdoor",
    "hack", "hacking", "crack", "cracker",

    # fraud/abuse
    "scam", "fraud",
}


def _err(code, message, details=None):
    """Create a consistent error dict."""
    if details is None:
        details = {}
    return {"code": code, "message": message, "details": details}


def _collect_text(payload):
    """Collect text from common fields safely."""
    fields = ["prompt", "input", "text", "message", "query", "content", "instruction"]
    parts = []

    for f in fields:
        value = payload.get(f)
        if value is not None:
            parts.append(str(value))

    return "\n".join(parts).strip()


def _to_words(text):
    """
    Very simple tokenizer (no regex):
    - lowercases
    - replaces common punctuation with spaces
    - splits on whitespace
    """
    text = text.lower()

    for ch in [".", ",", "!", "?", ":", ";", "(", ")", "[", "]", "{", "}", "\"", "'", "/", "\\", "-", "_"]:
        text = text.replace(ch, " ")

    return text.split()


def check_guardrails(payload):
    errors = []
    combined_text = _collect_text(payload).lower()

    # 1) Length guardrail
    if len(combined_text) > MAX_TEXT_LEN:
        errors.append(
            _err(
                "too_long",
                f"Input text is too long (max {MAX_TEXT_LEN} chars).",
                {"length": len(combined_text), "max_len": MAX_TEXT_LEN},
            )
        )

    # 2A) Banned phrase scan (multi-word)
    for phrase in BANNED_PHRASES:
        if phrase in combined_text:
            errors.append(
                _err(
                    "banned_content",
                    "Request appears to include disallowed/unsafe content.",
                    {"matched": phrase, "type": "phrase"},
                )
            )
            break  # deterministic: stop on first match

    # 2B) Banned word scan (single tokens)
    if not errors:
        words = _to_words(combined_text)
        for w in words:
            if w in BANNED_WORDS:
                errors.append(
                    _err(
                        "banned_content",
                        "Request appears to include disallowed/unsafe content.",
                        {"matched": w, "type": "word"},
                    )
                )
                break

    # 3) Large list fields check
    for key, value in payload.items():
        if isinstance(value, list) and len(value) > MAX_LIST_ITEMS:
            errors.append(
                _err(
                    "too_many_items",
                    f"Field '{key}' has too many items (max {MAX_LIST_ITEMS}).",
                    {"field": key, "count": len(value), "max_items": MAX_LIST_ITEMS},
                )
            )

    # Add metadata for debugging/observability
    guarded_payload = payload.copy()
    guarded_payload["_guardrails"] = {
        "scanned_chars": len(combined_text),
        "errors": len(errors),
    }

    return guarded_payload, errors


# Alias so engine can find it
enforce_guardrails = check_guardrails
