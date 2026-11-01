from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from swag_intent_baseline import fit, predict, tokenize
from swag_routing_contract import canonical_bytes, strict_json


class IntentBaselineTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{'taskFamily': label, 'taskText': text} for label, text in (
            ('documentation', 'document manual guide'), ('build_release', 'package build release'),
            ('implementation', 'repair user behavior'), ('implementation', 'implement user feature'))]

    def test_class_evidence_and_unknown_word_prior(self):
        model = fit(self.rows)
        self.assertEqual(predict(model, 'document guide')[0], 'documentation')
        self.assertEqual(predict(model, 'package release')[0], 'build_release')
        self.assertEqual(predict(model, 'never_seen_vocabulary')[0], 'implementation')

    def test_serialized_model_preserves_predictions_and_train_only_vocabulary(self):
        model = fit(self.rows)
        loaded = strict_json(canonical_bytes(model))
        before = canonical_bytes(loaded)
        for text in ('DOCUMENT guide', 'new_development_token', ''):
            self.assertEqual(predict(model, text), predict(loaded, text))
        self.assertEqual(canonical_bytes(loaded), before)
        self.assertNotIn('new_development_token', loaded['vocabulary'])
        self.assertEqual(tokenize('CI: Fix-Builder'), ['ci', 'fix', 'builder'])

    def test_missing_classes_or_empty_vocabulary_reject(self):
        with self.assertRaises(ValueError):
            fit(self.rows[:1])
        with self.assertRaises(ValueError):
            fit([{**row, 'taskText': '!!!'} for row in self.rows])


if __name__ == '__main__':
    unittest.main()
