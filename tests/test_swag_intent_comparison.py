from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from swag_intent_comparison import metrics


class IntentMetricTests(unittest.TestCase):
    def test_majority_cannot_hide_missing_minor_classes(self):
        expected = ['implementation'] * 14 + ['documentation'] * 3 + ['build_release'] * 4
        result = metrics(expected, ['implementation'] * 21)
        self.assertEqual(result['matched'], 14)
        self.assertAlmostEqual(result['balancedAccuracy'], 1 / 3)
        self.assertEqual(result['recallByClass']['documentation'], 0)

    def test_invalid_predictions_count_as_failures(self):
        result = metrics(['documentation', 'implementation'], ['documentation', None])
        self.assertEqual(result['matched'], 1)
        self.assertEqual(result['confusionMatrix']['implementation']['invalid'], 1)
        with self.assertRaisesRegex(ValueError, 'complete'):
            metrics(['implementation'], [])


if __name__ == '__main__':
    unittest.main()
