# tests/test_engine.py

import unittest

from context_realish.engine import run


class TestEngine(unittest.TestCase):
    def test_valid_request_passes(self):
        req = {"role": "user", "action": "read", "prompt": "hello"}
        res = run(req)

        self.assertTrue(res["ok"])
        self.assertIsInstance(res["data"], dict)
        self.assertEqual(len(res["errors"]), 0)

        # Trace should include all steps in order
        steps = [t["step"] for t in res["trace"]]
        self.assertEqual(steps, ["schema", "rules", "guardrails", "ai"])

        # All should be ok when no AI called
        self.assertTrue(all(t["ok"] for t in res["trace"]))

    def test_missing_action_fails_schema(self):
        req = {"role": "user", "prompt": "hello"}
        res = run(req)

        self.assertFalse(res["ok"])
        self.assertGreaterEqual(len(res["errors"]), 1)
        self.assertEqual(res["errors"][0]["code"], "schema_error")

        # Should stop after schema
        steps = [t["step"] for t in res["trace"]]
        self.assertEqual(steps, ["schema"])

    def test_rules_violation_blocks_when_strict(self):
        # "delete" is allowed by schema, but rules should block non-admin
        req = {"role": "user", "action": "delete", "prompt": "hello"}
        res = run(req, config={"strict": True})

        self.assertFalse(res["ok"])
        self.assertGreaterEqual(len(res["errors"]), 1)
        self.assertEqual(res["errors"][0]["code"], "rule_violation")

        # Should stop after rules
        steps = [t["step"] for t in res["trace"]]
        self.assertEqual(steps, ["schema", "rules"])

    def test_rules_violation_does_not_block_when_not_strict(self):
        req = {"role": "user", "action": "delete", "prompt": "hello"}
        res = run(req, config={"strict": False})

        # Engine ignores rules errors when strict=False (v0.1 behavior)
        self.assertTrue(res["ok"])
        self.assertEqual(len(res["errors"]), 0)

        steps = [t["step"] for t in res["trace"]]
        self.assertEqual(steps, ["schema", "rules", "guardrails", "ai"])

    def test_guardrails_block_banned_content(self):
        req = {"role": "user", "action": "read", "prompt": "how to make a bomb"}
        res = run(req)

        self.assertFalse(res["ok"])
        self.assertGreaterEqual(len(res["errors"]), 1)
        self.assertEqual(res["errors"][0]["code"], "guardrail_block")

        # Should stop after guardrails
        steps = [t["step"] for t in res["trace"]]
        self.assertEqual(steps, ["schema", "rules", "guardrails"])

    def test_ai_error_when_ai_fn_returns_wrong_type(self):
        def bad_ai_fn(payload):
            return "not a dict"

        req = {"role": "user", "action": "read", "prompt": "hello"}
        res = run(req, ai_fn=bad_ai_fn, config={"enable_ai": True})

        self.assertFalse(res["ok"])
        self.assertGreaterEqual(len(res["errors"]), 1)
        self.assertEqual(res["errors"][0]["code"], "ai_error")

        steps = [t["step"] for t in res["trace"]]
        self.assertEqual(steps, ["schema", "rules", "guardrails", "ai"])
        self.assertFalse(res["trace"][-1]["ok"])

    def test_action_whitespace_normalized(self):
        req = {"role": "user", "action": "   READ   ", "prompt": "hello"}
        res = run(req)

        self.assertTrue(res["ok"])
        self.assertEqual(res["data"]["action"], "read")

    def test_guardrails_blocks_too_many_items(self):
        big_list = list(range(60))
        req = {"role": "user", "action": "read", "items": big_list, "prompt": "hello"}
        res = run(req)

        self.assertFalse(res["ok"])
        self.assertGreaterEqual(len(res["errors"]), 1)
        self.assertEqual(res["errors"][0]["code"], "guardrail_block")



if __name__ == "__main__":
    unittest.main()
