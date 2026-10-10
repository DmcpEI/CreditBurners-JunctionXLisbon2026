import unittest
from ml.decision_rule import apply_half_rule


def record(stock, b, compliance=True):
    answers = {} if b is None else {"stock": {"scores": {"A": 0.0, "B": b, "C": 1 - b, "D": 0.0}}}
    return dict(answers=answers, observed_stock=stock, observed_compliance=compliance, action="ok")


class HalfRuleTests(unittest.TestCase):
    def test_threshold_and_untouched_cases(self):
        self.assertEqual(apply_half_rule(record("full", 0.15), 0.15)["observed_stock"], "half")  # v1 still reproducible
        self.assertEqual(apply_half_rule(record("full", 0.20))["observed_stock"], "half")
        self.assertEqual(apply_half_rule(record("full", 0.20))["action"], "check_stock")
        self.assertEqual(apply_half_rule(record("full", 0.19))["observed_stock"], "full")
        self.assertEqual(apply_half_rule(record("full", 0.3, compliance=None))["action"], "inspect")
        # no stock answer (gated by visibility/presence): decision and fallback unchanged
        self.assertEqual(apply_half_rule(record(None, None)), record(None, None))
        self.assertEqual(apply_half_rule(record("empty", None)), record("empty", None))


if __name__ == "__main__":
    unittest.main()
