import unittest
from ml.infer_sample import answer_tokens, inspect_stages


class AnswerTokenTests(unittest.TestCase):
    def test_visibility_and_presence_gate_later_questions(self):
        cases = [
            ("B", ["visibility"], "inspect", None),
            ("C", ["visibility"], "inspect", None),
            ("AB", ["visibility", "presence"], "restock", "empty"),
            ("AC", ["visibility", "presence"], "inspect", None),
            ("AAAA", ["visibility", "presence", "stock", "compliance"], "check_stock", "half"),
            ("AABA", ["visibility", "presence", "stock", "compliance"], "ok", "full"),
            ("AABB", ["visibility", "presence", "stock", "compliance"], "check_product", "full"),
            ("AACC", ["visibility", "presence", "stock", "compliance"], "inspect", None),
        ]
        for codes, expected_calls, action, stock in cases:
            with self.subTest(codes=codes):
                calls = []
                def ask(name):
                    calls.append(name)
                    return {"choice": codes[len(calls)-1]}
                result = inspect_stages(ask)
                self.assertEqual(calls, expected_calls)
                self.assertEqual(result["action"], action)
                self.assertEqual(result["observed_stock"], stock)
                if len(codes) < 4:
                    self.assertIsNone(result["observed_compliance"])

    def test_multitoken_variants_excluded_and_collisions_rejected(self):
        class Tokenizer:
            def encode(self, text, **kwargs):
                return [0, ord(text[-1])] if text.startswith(" ") else [ord(text)]
        self.assertEqual(answer_tokens(Tokenizer()), [[65], [66], [67]])

        class CollidingTokenizer:
            def encode(self, text, **kwargs):
                return [1]
        with self.assertRaises(ValueError):
            answer_tokens(CollidingTokenizer())
