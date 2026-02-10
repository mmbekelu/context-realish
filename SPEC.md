# Context Realish v0.1 — Spec

## Purpose
Context Realish validates and controls a request **before** any AI step.
It returns a deterministic decision with traceable failure reasons.

## Pipeline Order (must stay in this order)
1. Schemas (shape, types, normalization)
2. Rules (role/action permissions)
3. Guardrails (safety + size limits)
4. AI step (optional, only if all prior checks pass)

## Inputs
### Required fields
- action: string

### Optional fields
- role: string (default: "user")
- resource: string
- prompt/input/text/message/query/content/instruction: string
- other fields allowed (but guardrails may block large lists)

## Output Contract (always same shape)
- ok: bool
- data: dict or None
- errors: list of error objects
- trace: list of step results

### Error object shape
- code: string
- message: string
- details: dict (optional)

### Trace shape
Each step adds:
- step: "schema" | "rules" | "guardrails" | "ai"
- ok: bool

## Stop Behavior
If a step fails:
- The engine stops immediately
- Later steps do not run
- trace ends at the failing step

## Error Codes (v0.1)
### Schema
- missing_required_field
- invalid_type

### Rules
- action_not_allowed
- role_not_allowed (if you have it)

### Guardrails
- banned_content
- input_too_large (or whatever your code calls it)

## Guardrails Policy (high level)
- Blocks requests containing banned keywords/patterns
- Blocks oversized inputs (length/size limits)
- Keeps output deterministic (no guessing)
