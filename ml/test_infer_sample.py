import unittest
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from ml.infer_sample import answer_tokens, inspect_stages, question_input, question_fingerprint


class AnswerTokenTests(unittest.TestCase):
    def test_stage_inputs_and_cache_identity(self):
        keys, prompt = question_input("presence", "SECRET_PRODUCT")
        self.assertEqual(keys, ("crop", "mask"))
        self.assertNotIn("SECRET_PRODUCT", prompt)
        self.assertEqual(question_input("visibility", "SECRET_PRODUCT")[0], ("context", "crop", "mask"))
        self.assertNotIn("SECRET_PRODUCT", question_input("visibility", "SECRET_PRODUCT")[1])
        self.assertIn("SECRET_PRODUCT", question_input("compliance", "SECRET_PRODUCT")[1])
        self.assertEqual(question_input("compliance", "apple", True)[0], ("crop", "mask"))
        self.assertEqual(question_input("compliance", "apple", False)[0], ("context", "crop", "mask"))
        self.assertIn("apple", question_input("compliance", "apple", True)[1])
        self.assertEqual(question_input("compliance", "apple")[0], ("crop", "mask"))
        # stock prompt variants change only the stock question; v1 stays the default so old caches still match
        self.assertEqual(question_input("stock", "x"), question_input("stock", "x", stock_prompt="v1"))
        self.assertNotEqual(question_input("stock", "x")[1], question_input("stock", "x", stock_prompt="v2")[1])
        self.assertEqual(question_input("presence", "x"), question_input("presence", "x", stock_prompt="v2"))
        self.assertEqual(question_input("stock", "x", stock_crop_only=True)[0], ("crop", "mask"))
        self.assertEqual(question_input("stock", "x")[0], ("context", "crop", "mask"))
        # skipped stages: asked only presence+stock, compliance assumed true
        asked = []
        out = inspect_stages(lambda n: asked.append(n) or {"choice": "C" if n == "stock" else "A"}, ("presence", "stock"))
        self.assertEqual(asked, ["presence", "stock"])
        self.assertEqual((out["visibility"], out["observed_stock"], out["observed_compliance"]), ("clear", "full", True))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image"
            path.write_bytes(b"original")
            first = question_fingerprint("model", prompt, [path])
            self.assertEqual(first, question_fingerprint("model", prompt, [path]))
            self.assertNotEqual(first, question_fingerprint("other-model", prompt, [path]))
            path.write_bytes(b"changed")
            self.assertNotEqual(first, question_fingerprint("model", prompt, [path]))

    def test_presence_ablation_empty_input_and_missing_mask(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "sample.json"
            manifest.write_text("[]")
            command = [sys.executable, "-m", "ml.infer_sample", str(manifest),
                       "--model", "nonexistent-model", "--output", str(root / "out.json"),
                       "--crop-presence-only"]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("no model loaded", result.stdout)
            (root / "crop.png").write_bytes(b"not decoded before input validation")
            manifest.write_text(json.dumps([dict(sample_id="test", crop="crop.png", mask="missing-mask.png")]))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing-mask.png", result.stderr)
            self.assertFalse((root / "out.json").exists())

    def test_visibility_and_presence_gate_later_questions(self):
        cases = [
            ("B", ["visibility"], "inspect", None),
            ("C", ["visibility"], "inspect", None),
            ("AB", ["visibility", "presence"], "restock", "empty"),
            ("AC", ["visibility", "presence"], "inspect", None),
            ("AABA", ["visibility", "presence", "stock", "compliance"], "check_stock", "half"),
            ("AACA", ["visibility", "presence", "stock", "compliance"], "ok", "full"),
            ("AACB", ["visibility", "presence", "stock", "compliance"], "check_product", "full"),
            ("AADC", ["visibility", "presence", "stock", "compliance"], "inspect", None),
            ("AAAA", ["visibility", "presence", "stock", "compliance"], "restock", "empty"),
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
                if codes == "AB":
                    self.assertIs(result["observed_compliance"], True)
                elif len(codes) < 4:
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
