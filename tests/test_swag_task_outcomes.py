"""Software contract fixtures only. Never export these as research/training data."""
import copy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import os
import tempfile
import threading
import unittest
from unittest.mock import patch

from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from swag_routing_contract import canonical_bytes, digest, strict_json
import swag_task_outcomes as outcomes
import swag_outcome_eval as evaluation
import swag_unsloth_train as training


LIMITS = {'minimumCases': 1, 'maximumInvalidOutputs': 0, 'maximumOrderSensitiveCases': 0,
          'decisionThreshold': .6, 'minimumDecisionAccuracy': 1., 'minimumCoverage': 1.,
          'maximumSelectiveRisk': 0., 'maximumBrierScore': .1, 'maximumP95Seconds': 10.,
          'maximumCustomAccuracyDrop': 0., 'maximumQuantizedAccuracyDrop': 0.,
          'maximumQuantizedServingBytes': 29_000_000_000}


class OutcomeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.records, self.reviews = [], []
        self.policy = {'schemaVersion': 1, 'splits': {}}
        for month, split in enumerate(outcomes.SPLITS, 1):
            self.policy['splits'][split] = {'projects': [split],
                'startInclusive': f'2026-0{month}-01T00:00:00Z',
                'endExclusive': f'2026-0{month+1}-01T00:00:00Z'}
            record = {'schemaVersion': 1, 'caseId': split, 'taskId': 'fixture-' + split,
                      'repositoryId': 'fixture-repo-' + split, 'projectGroup': split,
                      'leakageGroup': split, 'capturedAt': f'2026-0{month}-10T00:00:00Z',
                      'sourceKind': 'real_observation', 'sourceSha256': 'a' * 64,
                      'configurationSha256': 'b' * 64,
                      'request': {'projectIntent': 'Software contract fixture only',
                                  'taskText': 'Fixture behavior ' + split,
                                  'acceptanceCriteria': 'Fixture criterion', 'candidates': []},
                      'attempts': []}
            verdicts = []
            for index in range(2):
                option = f'option-{index}'
                attempt_id = split + '-' + option
                record['request']['candidates'].append({
                    'optionId': option, 'bindingId': 'fixture-' + option, 'modelRevision': 'fixture-revision',
                    'effort': None, 'description': 'Fixture candidate', 'eligible': True,
                    'handoff': 'Fixture handoff'})
                receipt = {'taskId': record['taskId'], 'optionId': option, 'attemptId': attempt_id,
                           'sourceSha256': record['sourceSha256'], 'configurationSha256': record['configurationSha256'],
                           'terminalStatus': 'completed'}
                record['attempts'].append({**{key: value for key, value in receipt.items() if key != 'taskId'},
                    'completedAt': f'2026-0{month}-10T00:01:00Z', 'elapsedMs': 100, 'cost': None,
                    'evidence': {'receipt': self.artifact(attempt_id + '-receipt', receipt),
                                 'output': self.artifact(attempt_id + '-output', {'fixture': 'output'}),
                                 'verification': self.artifact(attempt_id + '-verify', {'fixture': 'verification'})}})
                verdicts.append({'attemptId': attempt_id, 'taskSuccess': 'pass' if index else 'fail',
                                 'handoffValid': 'fail' if index else 'pass', 'rationale': 'Fixture only'})
            self.records.append(record)
            self.reviews.append({'schemaVersion': 1, 'caseId': split, 'observationSha256': digest(record),
                'labelAuthorId': 'fixture-author', 'reviewerId': 'fixture-reviewer',
                'reviewedAt': '2026-04-20T00:00:00Z', 'previouslyUsed': False, 'redactionReviewed': True,
                'consent': {'training': True, 'evaluation': True, 'grantedBy': 'fixture-owner'},
                'evidence': {key: self.artifact(split + '-' + key, {'fixture': key})
                             for key in ('review', 'consent', 'redaction')}, 'verdicts': verdicts})

    def artifact(self, name, value):
        content = canonical_bytes(value)
        (self.root / name).write_bytes(content)
        return {'path': name, 'sha256': hashlib.sha256(content).hexdigest()}

    def admit(self, objective='task_success', name='export'):
        for name_part, rows in [('observations', self.records), ('reviews', self.reviews)]:
            (self.root / name_part).write_bytes(b''.join(canonical_bytes(row) + b'\n' for row in rows))
        (self.root / 'policy').write_bytes(canonical_bytes(self.policy))
        output = self.root / name
        outcomes.admit(self.root / 'observations', self.root / 'reviews', self.root / 'policy',
                       self.root, objective, output)
        return output

    def refresh(self, index):
        self.reviews[index]['observationSha256'] = digest(self.records[index])

    def freeze(self):
        directory = self.admit()
        path = self.root / 'protocol.json'
        protocol = evaluation.freeze(directory, 'acceptance', LIMITS, path)
        return path, protocol

    def rows(self, protocol, prediction=None):
        prediction = prediction or {'probabilities': {'option-0': .1, 'option-1': .9}}
        rows = []
        for case in protocol['cases']:
            for variant in protocol['variants']:
                request = case['request']
                if variant == 'reversed':
                    request = {**request, 'candidates': list(reversed(request['candidates']))}
                rows.append({'caseId': case['caseId'], 'variant': variant, 'elapsedSeconds': .1,
                             'requestSha256': digest(outcomes.messages(request, protocol['objective'])),
                             'rawOutput': canonical_bytes(prediction).decode()})
        return rows

    def test_objectives_are_separate_and_never_use_supplied_quality_scores(self):
        task = self.admit()
        handoff = self.admit('handoff_valid', 'handoff')
        task_case = strict_json((task / 'train.cases.jsonl').read_bytes())
        handoff_case = strict_json((handoff / 'train.cases.jsonl').read_bytes())
        self.assertEqual(task_case['outcomes'], {'option-0': False, 'option-1': True})
        self.assertEqual(handoff_case['outcomes'], {'option-0': True, 'option-1': False})
        chat = strict_json((task / 'train.chat.jsonl').read_bytes())['messages']
        self.assertNotIn('verification', chat[1]['content'])
        self.assertNotIn('handoff', chat[1]['content'])
        self.assertNotIn('quality', chat[1]['content'])
        self.assertEqual(len(chat), 3)
        self.assertFalse((task / 'acceptance.chat.jsonl').exists())
        training._validate_admitted_inputs(task, task / 'train.chat.jsonl', task / 'development.chat.jsonl')
        with self.assertRaisesRegex(ValueError, 'never acceptance'):
            training._validate_admitted_inputs(task, task / 'train.chat.jsonl', task / 'acceptance.cases.jsonl')

    def test_missing_review_and_unknown_are_withheld_not_invented(self):
        self.reviews.pop()
        self.reviews[0]['verdicts'][0]['taskSuccess'] = 'unknown'
        directory = self.admit()
        manifest = outcomes.verify_dataset(directory)
        self.assertEqual(manifest['counts'], {'train': 0, 'development': 1, 'acceptance': 0})
        self.assertEqual(len(manifest['withheld']), 2)
        with self.assertRaisesRegex(ValueError, 'no training rows'):
            training._validate_admitted_inputs(directory, directory / 'train.chat.jsonl', None)

    def test_no_reviews_produces_no_dataset(self):
        self.reviews = []
        with self.assertRaisesRegex(ValueError, 'No independently reviewed'):
            self.admit()
        self.assertFalse((self.root / 'export').exists())

    def test_source_change_single_option_or_receipt_tamper_rejected(self):
        for mutation in ('source', 'single', 'receipt'):
            with self.subTest(mutation=mutation):
                records = copy.deepcopy(self.records)
                if mutation == 'source':
                    records[0]['attempts'][0]['sourceSha256'] = 'c' * 64
                elif mutation == 'single':
                    records[0]['attempts'].pop()
                else:
                    records[0]['attempts'][0]['evidence']['receipt']['sha256'] = 'c' * 64
                with self.assertRaises((ValueError, ValidationError)):
                    outcomes.admitted_cases(records, self.reviews, self.policy, self.root, 'task_success')

    def test_consent_independence_and_unseen_constraints(self):
        for field in ('consent', 'reviewer', 'previouslyUsed'):
            with self.subTest(field=field):
                reviews = copy.deepcopy(self.reviews)
                if field == 'consent':
                    reviews[0]['consent']['training'] = False
                elif field == 'reviewer':
                    reviews[0]['reviewerId'] = ' FIXTURE-AUTHOR '
                else:
                    reviews[-1]['previouslyUsed'] = True
                with self.assertRaises(ValueError):
                    outcomes.admitted_cases(self.records, reviews, self.policy, self.root, 'task_success')

    def test_repository_cannot_cross_split_under_different_project_name(self):
        self.records[1]['repositoryId'] = self.records[0]['repositoryId']
        self.refresh(1)
        with self.assertRaisesRegex(ValueError, 'Cross-split'):
            self.admit()

    def test_changed_labels_and_resealed_consent_are_rejected_at_training(self):
        directory = self.admit()
        path = directory / 'train.cases.jsonl'
        case = strict_json(path.read_bytes())
        case['review']['consent']['training'] = False
        case['reviewSha256'] = digest(case['review'])
        path.write_bytes(canonical_bytes(case) + b'\n')
        manifest_path = directory / 'manifest.json'
        manifest = strict_json(manifest_path.read_bytes())
        manifest['files'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_bytes(canonical_bytes(manifest))
        with self.assertRaisesRegex(ValueError, 'consent'):
            training._validate_admitted_inputs(directory, directory / 'train.chat.jsonl', None)

    def test_freeze_requires_limits_and_is_immutable(self):
        directory = self.admit()
        path = self.root / 'protocol'
        with self.assertRaises(ValueError):
            evaluation.freeze(directory, 'acceptance', {}, path)
        evaluation.freeze(directory, 'acceptance', LIMITS, path)
        with self.assertRaises(FileExistsError):
            evaluation.freeze(directory, 'acceptance', LIMITS, path)

    def test_metrics_count_failures_and_order_variants_without_doubling_cases(self):
        _, protocol = self.freeze()
        rows = self.rows(protocol)
        summary = evaluation.summarize(protocol, rows)
        self.assertTrue(summary['protocolPassed'])
        self.assertEqual(summary['cases'], 1)
        self.assertAlmostEqual(summary['brierScore'], .01)
        rows[1]['errorClass'] = 'TimeoutError'
        summary = evaluation.summarize(protocol, rows)
        self.assertFalse(summary['protocolPassed'])
        self.assertEqual(summary['invalidOutputs'], 1)
        with self.assertRaisesRegex(ValueError, 'Every case'):
            evaluation.summarize(protocol, rows[:1])

    def test_ties_abstain_and_boolean_probabilities_are_invalid(self):
        _, protocol = self.freeze()
        case = protocol['cases'][0]
        tied = evaluation.score('{"probabilities":{"option-0":0.9,"option-1":0.9}}', case, .6)
        self.assertIsNone(tied['selectedOption'])
        self.assertFalse(tied['decisionCorrect'])
        invalid = evaluation.score('{"probabilities":{"option-0":false,"option-1":true}}', case, .6)
        self.assertFalse(invalid['validOutput'])

    def test_empty_comparison_reports_all_missing_arms_and_no_promotion(self):
        path, _ = self.freeze()
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        report = evaluation.compare({}, path, sha, LIMITS['maximumQuantizedServingBytes'])
        self.assertEqual(len(report['reasons']), 4)
        self.assertFalse(report['comparisonEvidencePassed'])
        self.assertFalse(report['promotionAuthorized'])
        with self.assertRaisesRegex(ValueError, 'frozen protocol'):
            evaluation.compare({}, path, sha, 42)

    def test_status_exposes_outcome_scope_without_task_or_review_content(self):
        import swag_dev_status as dev
        directory = self.admit()
        with patch.dict(os.environ, {'SWAG_ADMITTED_DATASET_DIR': str(directory)}):
            status = dev.dataset_status()
        self.assertEqual(status['objective'], 'task_success')
        self.assertEqual(status['scope'], outcomes.SCOPE)
        self.assertEqual(status['state'], 'verified_export')
        self.assertNotIn('taskText', str(status))

    def comparison_runs(self, protocol_path, protocol):
        """Fabricated contract artifacts confined to TemporaryDirectory, never research evidence."""
        runs, hashes = {}, {}
        protocol_sha = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
        for arm in evaluation.ARMS:
            directory = self.root / arm
            directory.mkdir()
            runs[arm] = directory
            (directory / 'protocol.json').write_bytes(protocol_path.read_bytes())
            artifact = {'custom_checkpoint': arm in ('custom_bf16', 'custom_quantized'),
                        'precision': 'int8' if arm == 'custom_quantized' else 'bf16',
                        'files': {'fixture-weight': {'bytes': 1, 'sha256': 'a' * 64}}}
            if arm == 'custom_bf16':
                artifact['baseManifestSha256'] = hashes['base_bf16']
            if arm == 'custom_quantized':
                artifact.update({'parentManifestSha256': hashes['custom_bf16'], 'quantizationMethod': 'fixture-only'})
            artifact_bytes = canonical_bytes(artifact)
            (directory / 'artifact-manifest.json').write_bytes(artifact_bytes)
            hashes[arm] = hashlib.sha256(artifact_bytes).hexdigest()
            results = b''.join(canonical_bytes(row) + b'\n' for row in self.rows(protocol))
            (directory / 'results.jsonl').write_bytes(results)
            summary = {'arm': arm, 'protocolSha256': protocol_sha,
                       'artifactManifestSha256': hashes[arm], 'resultsSha256': hashlib.sha256(results).hexdigest(),
                       'serverIdentityAttested': True}
            (directory / 'summary.json').write_bytes(canonical_bytes(summary))
            evidence = b'Contract fixture only; not hardware evidence'
            identity = {'scope': 'observed_serving_process', 'artifactManifestSha256': hashes[arm],
                        'protocolSha256': protocol_sha, 'verifiedArtifactFiles': {'fixture-weight': 'a' * 64},
                        'processIdentity': 'fixture-process', 'runtimeIdentity': 'fixture-runtime',
                        'rawEvidenceSha256': hashlib.sha256(evidence).hexdigest()}
            (directory / 'serving-identity.json').write_bytes(canonical_bytes(identity))
            (directory / 'serving-identity.raw').write_bytes(evidence)
            memory = {'scope': 'total_serving', 'artifactManifestSha256': hashes[arm],
                      'protocolSha256': protocol_sha, 'processIdentity': 'fixture-process', 'bytes': 100,
                      'method': 'fixture-only', 'rawEvidenceSha256': hashlib.sha256(evidence).hexdigest()}
            (directory / 'serving-memory.json').write_bytes(canonical_bytes(memory))
            (directory / 'serving-memory.raw').write_bytes(evidence)
        return runs, protocol_sha

    def test_comparison_checks_memory_lineage_and_recomputes_instead_of_trusting_summary(self):
        path, protocol = self.freeze()
        runs, sha = self.comparison_runs(path, protocol)
        report = evaluation.compare(runs, path, sha, LIMITS['maximumQuantizedServingBytes'])
        self.assertTrue(report['comparisonEvidencePassed'])
        self.assertFalse(report['deploymentQualified'])
        memory_path = runs['custom_quantized'] / 'serving-memory.json'
        memory = strict_json(memory_path.read_bytes())
        memory['bytes'] = LIMITS['maximumQuantizedServingBytes'] + 1
        memory_path.write_bytes(canonical_bytes(memory))
        report = evaluation.compare(runs, path, sha, LIMITS['maximumQuantizedServingBytes'])
        self.assertIn('Quantized total serving memory exceeds the frozen target', report['reasons'])
        memory['bytes'] = 100
        memory_path.write_bytes(canonical_bytes(memory))
        # A false success in summary cannot hide wrong retained predictions.
        directory = runs['custom_bf16']
        rows = self.rows(protocol, {'probabilities': {'option-0': .9, 'option-1': .1}})
        data = b''.join(canonical_bytes(row) + b'\n' for row in rows)
        (directory / 'results.jsonl').write_bytes(data)
        summary_path = directory / 'summary.json'
        summary = strict_json(summary_path.read_bytes())
        summary.update({'protocolPassed': True, 'decisionAccuracy': 1, 'resultsSha256': hashlib.sha256(data).hexdigest()})
        summary_path.write_bytes(canonical_bytes(summary))
        report = evaluation.compare(runs, path, sha, LIMITS['maximumQuantizedServingBytes'])
        self.assertFalse(report['comparisonEvidencePassed'])
        self.assertEqual(report['arms']['custom_bf16']['decisionAccuracy'], 0)
        self.assertIn('Quality regression exceeds frozen margin', report['reasons'])

    def test_comparison_rejects_wrong_quantized_parent_and_different_memory_process(self):
        path, protocol = self.freeze()
        runs, sha = self.comparison_runs(path, protocol)
        directory = runs['custom_quantized']
        artifact_path = directory / 'artifact-manifest.json'
        artifact = strict_json(artifact_path.read_bytes())
        artifact['parentManifestSha256'] = 'f' * 64
        artifact_path.write_bytes(canonical_bytes(artifact))
        summary_path = directory / 'summary.json'
        summary = strict_json(summary_path.read_bytes())
        summary['artifactManifestSha256'] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        summary_path.write_bytes(canonical_bytes(summary))
        report = evaluation.compare(runs, path, sha, LIMITS['maximumQuantizedServingBytes'])
        self.assertIn('Quantized arm must derive from exactly the custom BF16 artifact', report['reasons'])
        memory_path = runs['small_baseline'] / 'serving-memory.json'
        memory = strict_json(memory_path.read_bytes())
        memory['processIdentity'] = 'different-fixture-process'
        memory_path.write_bytes(canonical_bytes(memory))
        report = evaluation.compare(runs, path, sha, LIMITS['maximumQuantizedServingBytes'])
        self.assertIn('small_baseline: memory and serving identity refer to different processes', report['reasons'])

    def test_runner_sends_no_labels_and_retains_endpoint_failures(self):
        path, protocol = self.freeze()
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = strict_json(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append(payload)
                if len(requests) == 2:
                    self.send_response(503)
                    self.end_headers()
                    return
                body = canonical_bytes({'model': 'fixture-model', 'choices': [{'message': {'content':
                    '{"probabilities":{"option-0":0.1,"option-1":0.9}}'}}]})
                self.send_response(200)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        artifact, key = self.root / 'artifact.json', self.root / 'key.env'
        artifact.write_bytes(canonical_bytes({'files': {'fixture-weight': {'bytes': 1, 'sha256': 'a' * 64}}}))
        key.write_text('VLLM_API_KEY=fixture-not-a-credential', encoding='utf-8')
        result = evaluation.run(path, hashlib.sha256(path.read_bytes()).hexdigest(), artifact, 'base_bf16',
                                f'http://127.0.0.1:{server.server_port}', 'fixture-model', key, self.root / 'run')
        self.assertFalse(result['protocolPassed'])
        self.assertEqual(result['invalidOutputs'], 1)
        self.assertEqual(len(requests), 2)
        self.assertTrue(all(len(row['messages']) == 2 for row in requests))
        self.assertNotIn('reviewer', str(requests))
        first = strict_json(requests[0]['messages'][1]['content'])
        second = strict_json(requests[1]['messages'][1]['content'])
        self.assertEqual(first['candidates'], list(reversed(second['candidates'])))


if __name__ == '__main__':
    unittest.main()
