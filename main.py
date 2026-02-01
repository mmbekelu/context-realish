from context_realish.engine import run

def simple_ai(payload):
    new_payload = payload.copy()
    prompt = new_payload.get("prompt", "")
    new_payload["assistant_reply"] = "You said: " + str(prompt)
    return new_payload

req = {"role": "user", "action": "read", "prompt": "hello"}

res = run(req, ai_fn=simple_ai, config={"enable_ai": True})
print(res)
