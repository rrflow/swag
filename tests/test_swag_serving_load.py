"""Contract fixtures for the observer, never model-training examples."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import swag_serving_load as load


class ServingLoadTests(unittest.TestCase):
    def test_memory_units_and_overlapping_counters_are_not_combined(self):
        observed = load.proc_memory('MemTotal: 1000 kB\nMemAvailable: 200 kB\nVmRSS: 50 kB\n')
        self.assertEqual(observed['MemAvailableBytes'], 204800)
        self.assertEqual(observed['VmRSSBytes'], 51200)
        self.assertNotIn('totalServingBytes', observed)

    def test_resource_stops_fail_closed(self):
        config = {'minimumAvailableBytes': 100, 'maximumTemperatureC': 80}
        sample = {'host': {'MemAvailableBytes': 101}, 'gpu': [{'temperatureC': 70}]}
        self.assertIsNone(load.stop_reason(sample, config))
        sample['gpu'][0]['temperatureC'] = 80
        self.assertEqual(load.stop_reason(sample, config), 'temperature_limit')
        sample['host']['MemAvailableBytes'] = 99
        self.assertEqual(load.stop_reason(sample, config), 'available_memory_limit')

    def test_errors_and_undispatched_requests_remain_visible(self):
        rows = [{'httpStatus': 200, 'elapsedSeconds': 1.},
                {'httpStatus': 503, 'errorClass': 'HTTPError', 'elapsedSeconds': 2.},
                {'notDispatched': True}]
        report = load.phase_summary(rows, 2, 3.)
        self.assertEqual((report['attempted'], report['completed'], report['notDispatched']), (2, 1, 1))
        self.assertEqual(report['p95Seconds'], 2.)
        self.assertFalse(report['qualityEvaluated'])

    def test_assistant_targets_and_labels_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.jsonl'
            row = {'id': 'fixture', 'sourceReference': 'fixture-only', 'sourceSha256': 'a' * 64,
                   'messages': [{'role': 'user', 'content': 'Fixture input'}]}
            path.write_text(json.dumps(row) + '\n')
            self.assertEqual(len(load.read_workload(path)[0]), 1)
            row['messages'].append({'role': 'assistant', 'content': 'Fixture target'})
            path.write_text(json.dumps(row) + '\n')
            with self.assertRaisesRegex(ValueError, 'system/user'):
                load.read_workload(path)
            row['messages'].pop()
            row['expected'] = 'fictional target'
            path.write_text(json.dumps(row) + '\n')
            with self.assertRaisesRegex(ValueError, 'never outcome labels'):
                load.read_workload(path)


if __name__ == '__main__':
    unittest.main()
