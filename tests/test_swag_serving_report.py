"""Temporary software fixtures only; these are not real load measurements."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import swag_serving_load as load
import swag_serving_report as reports


class ServingReportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.inputs = [{'id': 'fixture', 'sourceReference': 'fixture-only', 'sourceSha256': 'a' * 64,
                        'messages': [{'role': 'user', 'content': 'Fixture request'}]}]

    def write(self, directory, name, rows):
        data = b''.join(load.encode(row) + b'\n' for row in rows)
        (directory / name).write_bytes(data)
        return load.sha(data)

    def fixture(self, name):
        directory = self.root / name
        directory.mkdir()
        workload_sha = self.write(directory, 'workload.jsonl', self.inputs)
        artifact_sha = self.write(directory, 'artifact-manifest.json', [{'fixture': True}])
        protocol = {'kind': 'swag.serving_load', 'configuration': {'rounds': 1, 'concurrency': [1],
                    'model': 'fixture-only', 'temperature': 0, 'maxTokens': 16},
                    'workloadSha256': workload_sha, 'artifactManifestSha256': artifact_sha,
                    'implementationSha256': 'b' * 64, 'qualityEvaluated': False,
                    'trainingPerformed': False, 'deploymentQualified': False}
        self.write(directory, 'protocol.json', [protocol])
        requests = [{'caseId': 'fixture', 'repeat': 0, 'clientConcurrency': 1, 'httpStatus': 200,
                     'elapsedSeconds': .5, 'requestSha256': load.sha(load.encode(self.inputs[0]['messages'])),
                     'rawOutput': '{"fixture":"response"}'}]
        samples = [{'containerId': name, 'containerStartedAt': 'fixture-time', 'imageId': 'fixture-image',
                    'runtimeConfiguration': {}, 'host': {'MemAvailableBytes': 1000},
                    'gpu': [{'utilizationPercent': 90, 'temperatureC': 65}],
                    'gpuProcesses': [{'reportedBytes': 100, 'owned': True}], 'cgroupMemoryBytes': 70}]
        summary = {**protocol, 'phases': [load.phase_summary(requests, 1, .6)], 'stoppedEarly': False,
                   'samplesSha256': self.write(directory, 'samples.jsonl', samples),
                   'requestsSha256': self.write(directory, 'requests.jsonl', requests),
                   'totalServingMemoryVerified': False, 'totalServingBytes': None}
        self.write(directory, 'summary.json', [summary])
        return directory

    def test_report_retains_unknown_total_and_excludes_content(self):
        directory = self.fixture('baseline')
        result, _ = reports.report(directory)
        self.assertEqual(result['largestOwnedProcessGpuReportedBytes'], 100)
        self.assertEqual(result['maximumCgroupMemoryBytes'], 70)
        self.assertIsNone(result['totalServingBytes'])
        self.assertNotIn('Fixture request', json.dumps(result))
        self.assertNotIn('response', json.dumps(result))

    def test_changed_raw_observations_rejected(self):
        directory = self.fixture('baseline')
        (directory / 'requests.jsonl').write_text('{}\n')
        with self.assertRaisesRegex(ValueError, 'stream changed'):
            reports.report(directory)

    def test_favorable_summary_cannot_override_raw_latency(self):
        directory = self.fixture('baseline')
        summary = json.loads((directory / 'summary.json').read_bytes())
        summary['phases'][0]['p95Seconds'] = .01
        self.write(directory, 'summary.json', [summary])
        with self.assertRaisesRegex(ValueError, 'Phase metrics'):
            reports.report(directory)

    def test_same_outputs_are_not_quality_equivalence(self):
        result = reports.compare(self.fixture('baseline'), self.fixture('candidate'))
        self.assertEqual(result['comparison']['outputAgreement'], 1.)
        self.assertFalse(result['comparison']['qualityEquivalenceEstablished'])

    def test_changed_generation_settings_reject_paired_claim(self):
        baseline, candidate = self.fixture('baseline'), self.fixture('candidate')
        for filename in ('protocol.json', 'summary.json'):
            document = json.loads((candidate / filename).read_bytes())
            document['configuration']['maxTokens'] = 32
            self.write(candidate, filename, [document])
        with self.assertRaisesRegex(ValueError, 'identities'):
            reports.compare(baseline, candidate)


if __name__ == '__main__':
    unittest.main()
