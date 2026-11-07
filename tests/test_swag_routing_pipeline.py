"""Admission, leakage and evaluator failure tests; fixtures are not training data."""
import copy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import swag_passive_capture as capture
import swag_routing_contract as contract
import swag_routing_dataset as admission
import swag_routing_eval as evaluation
import swag_unsloth_train as training

LIMITS = {'minimumCases': 1, 'minimumAccuracy': 1.0, 'maximumPolicyViolations': 0,
          'maximumInvalidOutputs': 0, 'maximumP95Seconds': 20}


def request_fixture(text='Review a bounded change'):
    return {'projectIntent': 'Build a useful app', 'taskText': text,
            'minimumQuality': 2, 'maxCost': 1, 'requestedEffort': 'low', 'localOnly': False,
            'candidates': [
                {'bindingId': 'eligible', 'provider': 'fixture', 'modelId': 'fictional',
                 'accessMode': 'local', 'authorized': True, 'healthy': True,
                 'quotaAvailable': True, 'location': 'local', 'quality': 2,
                 'cost': 1, 'efforts': ['low']},
                {'bindingId': 'denied', 'provider': 'fixture', 'modelId': 'fictional',
                 'accessMode': 'subscription', 'authorized': False, 'healthy': True,
                 'quotaAvailable': True, 'location': 'cloud', 'quality': 9,
                 'cost': 0, 'efforts': ['low', 'high']} ]}


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'export'
        self.observations, self.reviews = [], []
        self.policy = {'schemaVersion': 1, 'splits': {}}
        for index, split in enumerate(admission.SPLITS, 1):
            self.policy['splits'][split] = {
                'projects': [split], 'startInclusive': f'2026-0{index}-01T00:00:00Z',
                'endExclusive': f'2026-0{index+1}-01T00:00:00Z'}
            observation = capture.build_capture_record(
                project_root=self.root / split, task_type='fixture', issue_title='fixture',
                issue_id=split, intent_text='Fixture request ' + split,
                selected_question_ids=['fixture.check'], route_target_tier=None,
                stack=[], domain='', changed_files=[], user_override=None,
                user_acceptance=None, confidence=None, rationale='', outcome=None,
                source_url=None, reviewer='fixture-author')
            observation['captured_at'] = f'2026-0{index}-10T00:00:00Z'
            request = request_fixture(observation['intent_text'])
            evidence = {}
            for kind in ('consent', 'label', 'redaction', 'candidateSnapshot'):
                content = (contract.canonical_bytes(request['candidates'])
                           if kind == 'candidateSnapshot' else b'Test fixture attestation only')
                name = split + '-' + kind + '.json'
                (self.root / name).write_bytes(content)
                evidence[kind] = {'path': name, 'sha256': hashlib.sha256(content).hexdigest()}
            review = {
                'schemaVersion': 1, 'recordId': observation['record_id'],
                'observationSha256': contract.digest(observation), 'projectGroup': split,
                'leakageGroup': split, 'reviewerId': 'fixture-reviewer', 'labelAuthorId': 'fixture-author',
                'reviewedAt': '2026-04-01T00:00:00Z',
                'consent': {'training': True, 'evaluation': True, 'grantedBy': 'fixture-owner'},
                'redactionReviewed': True, 'sourceKind': 'real_observation', 'previouslyUsed': False,
                'evidence': evidence, 'request': request, 'expected': {'bindingId': 'eligible', 'effort': 'low'}}
            self.observations.append(observation)
            self.reviews.append(review)

    def export(self):
        for name, rows in [('observations.jsonl', self.observations), ('reviews.jsonl', self.reviews)]:
            (self.root / name).write_bytes(b''.join(contract.canonical_bytes(row) + b'\n' for row in rows))
        (self.root / 'policy.json').write_bytes(contract.canonical_bytes(self.policy))
        return admission.admit(self.root / 'observations.jsonl', self.root / 'reviews.jsonl',
                               self.root / 'policy.json', self.root, self.output)

    def test_export_separates_targets_preserves_sources_and_prevents_overwrite(self):
        before = copy.deepcopy(self.observations)
        manifest = self.export()
        self.assertEqual(manifest['counts'], dict.fromkeys(admission.SPLITS, 1))
        self.assertFalse((self.output / 'acceptance.chat.jsonl').exists())
        self.assertEqual(self.observations, before)
        self.assertFalse(manifest['deploymentQualified'])
        training._validate_admitted_inputs(self.output, self.output / 'train.chat.jsonl',
                                           self.output / 'development.chat.jsonl')
        with self.assertRaisesRegex(ValueError, 'never acceptance'):
            training._validate_admitted_inputs(self.output, self.output / 'train.chat.jsonl',
                                               self.output / 'acceptance.cases.jsonl')
        with self.assertRaises(FileExistsError):
            self.export()

    def test_changed_observation_rejected_before_output(self):
        self.observations[0]['intent_text'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'changed after review'):
            self.export()
        self.assertFalse(self.output.exists())

    def test_consent_and_independent_review_required(self):
        self.reviews[0]['consent']['training'] = False
        with self.assertRaisesRegex(ValueError, 'consent'):
            self.export()
        self.reviews[0]['consent']['training'] = True
        self.reviews[0]['reviewerId'] = ' FIXTURE-AUTHOR '
        with self.assertRaisesRegex(ValueError, 'independent'):
            self.export()

    def test_no_reviews_cannot_admit_raw_captures(self):
        self.reviews = []
        with self.assertRaisesRegex(ValueError, 'No reviewed'):
            self.export()

    def test_native_attempt_and_prior_review_do_not_create_admission_authority(self):
        from test_swag_passive_capture import native_fixture
        manifest = native_fixture(self.root)
        observation = capture.import_native_attempt(manifest, self.root)
        self.observations = [observation]
        self.reviews = []
        with self.assertRaisesRegex(ValueError, 'No reviewed'):
            self.export()
        self.assertFalse(self.output.exists())
        self.assertFalse(observation['training_consent'])
        self.assertEqual(observation['label_status'], 'unreviewed')
        self.assertEqual(observation['native_attempt']['prior_review']['relationship'],
                         'prior_observation_only_not_capture_review')

    def test_changed_or_escaping_evidence_rejected(self):
        ref = self.reviews[0]['evidence']['label']
        (self.root / ref['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            self.export()
        ref['path'] = '../outside'
        with self.assertRaisesRegex(ValueError, 'relative path'):
            self.export()

    def test_policy_conflicting_label_rejected(self):
        self.reviews[0]['expected']['bindingId'] = 'denied'
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            self.export()

    def test_project_time_and_leakage_overlap_rejected(self):
        self.reviews[1]['leakageGroup'] = 'train'
        with self.assertRaisesRegex(ValueError, 'Cross-split'):
            self.export()
        self.reviews[1]['leakageGroup'] = 'development'
        self.policy['splits']['development']['startInclusive'] = '2026-01-15T00:00:00Z'
        with self.assertRaisesRegex(ValueError, 'ordered and disjoint'):
            self.export()

    def test_duplicate_task_text_cannot_cross_splits(self):
        self.observations[1]['intent_text'] = self.observations[0]['intent_text'].upper()
        self.reviews[1]['observationSha256'] = contract.digest(self.observations[1])
        self.reviews[1]['request']['taskText'] = self.observations[1]['intent_text']
        with self.assertRaisesRegex(ValueError, 'Cross-split'):
            self.export()

    def test_exposed_or_synthetic_acceptance_rejected(self):
        self.reviews[2]['previouslyUsed'] = True
        with self.assertRaisesRegex(ValueError, 'unseen real'):
            self.export()
        self.assertFalse(self.output.exists())
        self.reviews[2]['previouslyUsed'] = False
        for review in self.reviews:
            review['sourceKind'] = 'synthetic_development'
            with self.subTest(project=review['projectGroup']), self.assertRaisesRegex(ValueError, 'reviewed real observations'):
                self.export()
            self.assertFalse(self.output.exists())
            review['sourceKind'] = 'real_observation'

    def test_export_tampering_rejected_by_trainer(self):
        self.export()
        (self.output / 'train.chat.jsonl').write_bytes(b'{"messages":[]}\n')
        with self.assertRaisesRegex(ValueError, 'changed after admission'):
            training._validate_admitted_inputs(self.output, self.output / 'train.chat.jsonl', None)

    def test_incomplete_manifest_cannot_bypass_hash_verification(self):
        manifest = self.export()
        manifest['files'].pop('train.chat.jsonl')
        (self.output / 'manifest.json').write_bytes(contract.canonical_bytes(manifest))
        with self.assertRaisesRegex(ValueError, 'Incomplete admission manifest'):
            training._validate_admitted_inputs(self.output, self.output / 'train.chat.jsonl', None)


class EvaluationTests(unittest.TestCase):
    def test_strict_output_distinguishes_violations_and_abstention(self):
        request = request_fixture()
        expected = contract.expected_route(request)
        for raw in ('{"bindingId":"eligible","bindingId":"denied","effort":"low"}',
                    '{"bindingId":"eligible","effort":"low","extra":true}',
                    '{"bindingId":null,"effort":"low"}', 'NaN', '[]'):
            self.assertFalse(contract.score_output(raw, request, expected)['validOutput'])
        self.assertTrue(contract.score_output('{"bindingId":"denied","effort":"low"}',
                                              request, expected)['policyViolation'])
        abstention = contract.score_output('{"bindingId":null,"effort":null}', request, expected)
        self.assertTrue(abstention['falseAbstention'])
        self.assertFalse(evaluation.summarize([{**abstention, 'elapsedSeconds': 1}], LIMITS)['protocolPassed'])

    def test_unknown_and_duplicate_candidates_do_not_get_silent_defaults(self):
        request = request_fixture()
        request['candidates'].append(copy.deepcopy(request['candidates'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate binding'):
            contract.validate_request(request)
        request['candidates'].pop()
        request['candidates'][0]['authorized'] = None
        with self.assertRaises(Exception):
            contract.validate_request(request)

    def test_freeze_rejects_duplicate_cases_and_missing_limits(self):
        case = {'caseId': 'one', 'request': request_fixture(), 'expected': {'bindingId': 'eligible', 'effort': 'low'}}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'protocol.json'
            with self.assertRaisesRegex(ValueError, 'Duplicate case'):
                evaluation.freeze([case, case], 'development', {}, LIMITS, target)
            with self.assertRaisesRegex(ValueError, 'thresholds'):
                evaluation.freeze([case], 'development', {}, {}, target)
            self.assertFalse(target.exists())

    def test_endpoint_rejects_cleartext_remote_and_embedded_credentials(self):
        for url in ('http://example.com', 'https://user:secret@example.com',
                    'https://example.com?key=secret', 'file:///tmp/socket'):
            with self.assertRaises(ValueError):
                evaluation.endpoint_url(url)
        self.assertEqual(evaluation.endpoint_url('http://127.0.0.1:8083/v1'),
                         'http://127.0.0.1:8083/v1/chat/completions')

    def test_actual_loopback_transport_pins_protocol_and_rejects_redirects(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            redirect = False
            def log_message(self, *args):
                pass
            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                if self.redirect:
                    self.send_response(307)
                    self.send_header('Location', '/stolen')
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'model': 'fixture-model', 'choices': [{'message': {
                    'content': '{"bindingId":"eligible","effort":"low"}'}}]}).encode())
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                case = {'caseId': 'fixture', 'request': request_fixture(),
                        'expected': {'bindingId': 'eligible', 'effort': 'low'}}
                protocol = root / 'protocol.json'
                evaluation.freeze([case], 'development', {}, LIMITS, protocol)
                sha = hashlib.sha256(protocol.read_bytes()).hexdigest()
                artifact, key = root / 'artifact.json', root / 'private.env'
                artifact.write_text('{"identity":"test_fixture_only"}')
                key.write_text('VLLM_API_KEY=test-secret\n')
                args = (protocol, sha, artifact, 'base_bf16',
                        f'http://127.0.0.1:{server.server_port}', 'fixture-model', key)
                result = evaluation.run(*args, root / 'run')
                self.assertTrue(result['protocolPassed'])
                self.assertFalse(result['deploymentQualified'])
                self.assertFalse(result['serverIdentityAttested'])
                self.assertNotIn('test-secret', (root / 'run/summary.json').read_text())
                self.assertEqual(len(received[0]['messages']), 2)  # No gold target in request.
                Handler.redirect = True
                failed = evaluation.run(*args, root / 'redirect')
                self.assertEqual(failed['invalidOutputs'], 1)
                self.assertEqual(len(received), 2)  # Redirect was never followed.
                protocol.write_bytes(protocol.read_bytes() + b' ')
                with self.assertRaisesRegex(ValueError, 'caller-pinned'):
                    evaluation.run(*args, root / 'changed')
                self.assertFalse((root / 'changed').exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
