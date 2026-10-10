import unittest
from ml.infer_sample import answer_tokens


class AnswerTokenTests(unittest.TestCase):
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
