import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import swag_passive_capture as capture
import swag_routing_contract as contract


def native_fixture(root, supplements=True):
    """Controlled protocol fixtures only; never model outcomes or training data."""
    sha = lambda value: hashlib.sha256(value).hexdigest()
    reported = sha(b'controlled engine-reported identity, not independent attestation')
    scope, task_id = 'instance:fixture-instance', 'task-fixture-native'
    read = {'runtime_manifest_sha256': reported, 'runtime_cursor': 3,
            'schema_revision': 4, 'catalogue_revision': 0}
    source = {'contract_version': 1, 'project_id': 'fixture-project',
              **{key: reported for key in ('captured_snapshot_sha256', 'entry_identity',
                 'path_sha256', 'policy_sha256', 'profile_sha256', 'validated_snapshot_sha256')},
              'content_sha256': sha(b'controlled source bytes'), 'captured_read': read,
              'validated_read': read, 'captured_at_unix_ms': 1, 'validated_at_unix_ms': 2}
    shared = {'contract_version': 1, 'scope': scope, 'task_id': task_id,
              **{key: reported for key in ('task_sha256', 'configuration_sha256',
                 'packet_sha256', 'request_sha256', 'response_sha256')},
              'service_id': 'fixture-service-alias', 'usage': None, 'elapsed_ms': None, 'http_status': 200}
    selector = {**shared, 'attempt_id': 'fixture-selector', 'purpose': 'experimental_proposal',
                'controller_binding_id': 'fixture-controller', 'allowance_sha256': reported,
                'content_sha256': reported,
                'choice': {'kind': 'select', 'binding_id': 'fixture-worker-binding', 'effort': None}}
    worker = {**shared, 'attempt_id': 'fixture-worker', 'selection_attempt_id': 'fixture-selector',
              'selection_sha256': reported, 'binding_id': 'fixture-worker-binding',
              'content': 'controlled output', 'content_sha256': sha(b'controlled output'),
              'read': read, 'source': source, 'context': None}
    task = {'format_version': 1, 'scope': scope, 'task_id': task_id, 'goal': 'controlled task'}
    budget = {'format_version': 1, 'instance_id': 'fixture-instance', 'scope': scope, 'task_id': task_id}
    def envelope(payload):
        return {'protocol': 'rrd', 'protocol_version': 1, 'outcome': {'status': 'ok', 'payload': payload}}
    def attempt(output, kind, ordinal):
        return envelope({'attempt': {'attempt_id': output['attempt_id'], 'ordinal': ordinal,
                                     'status': 'accepted', 'result': None, 'outcome_sha256': reported,
                                     kind: output}})
    documents = {'task': envelope({'task': task}), 'budget': envelope({'budget': budget}),
                 'worker': attempt(worker, 'worker_output', 2),
                 'selector': attempt(selector, 'endpoint_proposal', 1)}
    artifacts = {'source': b'controlled source bytes',
                 **{key: contract.canonical_bytes(value) for key, value in documents.items()}}
    if supplements:
        source_response = sha(b'controlled typed attempt view, not provider response')
        prepared = {'contract_version': 1, 'scope': scope, 'delivery_id': 'fixture-delivery',
                    'event_id': 'fixture-event', 'source_response_sha256': source_response,
                    'payload_sha256': reported, 'configuration_sha256': sha(b'later delivery config'),
                    'source': {'kind': 'task_attempt', 'request': {'scope': scope, 'task_id': task_id,
                               'attempt_id': 'fixture-worker'}, 'expected_status': 'accepted',
                               'expected_outcome_sha256': reported}}
        receiver = {'events': [{'schema': 'rroflow.capture/v1', 'agent': 'rrflow', 'kind': 'engine.observed',
                    'event_id': 'fixture-event', 'operation_id': 'fixture-delivery',
                    'engine': {'instance_id': 'fixture-instance', 'scope': scope, 'task_id': task_id,
                               'attempt_id': 'fixture-worker', 'version': 1, 'operation': 'task-attempt-read',
                               'configuration_sha256': reported, 'response_sha256': source_response,
                               'source_sha256': None}}]}
        review = {'schema': 'clyffy.private-draft-review.v1', 'reviewed_utc': '2026-01-01T00:00:00Z',
                  'identity': {'task_response_sha256': sha(artifacts['task']),
                               'task_goal_utf8_sha256': sha(b'controlled task'),
                               'source_file_sha256': sha(artifacts['source']),
                               'source_file_bytes': len(artifacts['source']),
                               'worker_attempt_response_sha256': sha(artifacts['worker']),
                               'worker_content_utf8_sha256': worker['content_sha256'],
                               'worker_reported_content_sha256': worker['content_sha256'],
                               'worker_reported_source_sha256': sha(artifacts['source']),
                               'attempt_status': 'accepted'}}
        artifacts.update({key: contract.canonical_bytes(value) for key, value in
                          [('prepared_delivery', prepared), ('receiver_readback', receiver), ('prior_review', review)]})
    manifest = {'schema_version': 1, 'artifacts': {}}
    for role, content in artifacts.items():
        path = role + '.data'
        (root / path).write_bytes(content)
        manifest['artifacts'][role] = {'path': path, 'sha256': sha(content)}
    path = root / 'manifest.json'
    path.write_bytes(contract.canonical_bytes(manifest))
    return path


class NativeCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = native_fixture(self.root)

    def load(self):
        return capture.import_native_attempt(self.manifest, self.root)

    def alter(self, role, change):
        manifest = json.loads(self.manifest.read_bytes())
        ref = manifest['artifacts'][role]
        path = self.root / ref['path']
        value = json.loads(path.read_bytes())
        change(value)
        path.write_bytes(contract.canonical_bytes(value))
        ref['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.manifest.write_bytes(contract.canonical_bytes(manifest))

    def test_native_metadata_preserves_unknowns_and_separates_prior_review(self):
        record = self.load()
        contract.validate(record, 'passive_capture.schema.json')
        native = record['native_attempt']
        self.assertNotEqual(record['task_id'], native['identity']['task_id'])
        self.assertEqual(record['selected_question_ids'], [])
        self.assertFalse(record['training_consent'])
        self.assertEqual(record['label_status'], 'unreviewed')
        self.assertTrue(all(value is None for value in record['outcome'].values()))
        for key in ('provider', 'modelId', 'effort', 'accessMode'):
            self.assertIsNone(record['route'][key])
        self.assertEqual(native['prior_review']['relationship'], 'prior_observation_only_not_capture_review')
        self.assertIsNone(native['delivery']['receiver_source_sha256'])
        self.assertNotEqual(native['delivery']['source_response_sha256'], native['worker']['response_sha256'])
        self.assertIsNone(native['model_revision'])
        self.assertIsNone(native['loaded_weights_attestation'])
        serialized = contract.canonical_bytes(record)
        for absent in (b'controlled source bytes', b'controlled output', b'controlled task',
                       str(self.root).encode(), b'.data'):
            self.assertNotIn(absent, serialized)

    def test_replay_noop_conflict_and_new_supplement_preserve_original(self):
        output = self.root / 'capture.jsonl'
        record = self.load()
        self.assertTrue(capture.append_record(output, record, native_dedup=True))
        original = output.read_bytes()
        self.assertFalse(capture.append_record(output, self.load(), native_dedup=True))
        for key, value in [('source_bytes', 1), ('prior_review', None)]:
            changed = copy.deepcopy(record)
            changed['native_attempt'][key] = value
            with self.assertRaisesRegex(ValueError, 'conflict'):
                capture.append_record(output, changed, native_dedup=True)
            self.assertEqual(output.read_bytes(), original)
        self.assertFalse(output.with_name(output.name + '.lock').exists())

    def test_replay_still_validates_remainder_and_partial_tail(self):
        output = self.root / 'capture.jsonl'
        record = self.load()
        capture.append_record(output, record, native_dedup=True)
        for suffix in (b'{"partial":', b'{"invalid":1}\n'):
            before = output.read_bytes()
            output.write_bytes(before + suffix)
            with self.assertRaises((ValueError, capture.ValidationError)):
                capture.append_record(output, record, native_dedup=True)
            self.assertEqual(output.read_bytes(), before + suffix)
            output.write_bytes(before)

    def test_replay_rejects_integral_float_change_in_retained_row(self):
        output = self.root / 'capture.jsonl'
        record = self.load()
        altered = copy.deepcopy(record)
        altered['native_attempt']['worker']['ordinal'] = 2.0
        # JSON Schema permits integral floats; immutable replay compares JSON bytes.
        contract.validate(altered, 'passive_capture.schema.json')
        before = contract.canonical_bytes(altered) + b'\n'
        output.write_bytes(before)
        with self.assertRaisesRegex(ValueError, 'conflict'):
            capture.append_record(output, record, native_dedup=True)
        self.assertEqual(output.read_bytes(), before)

    def test_replay_rejects_preexisting_duplicate_attempts(self):
        output = self.root / 'capture.jsonl'
        record = self.load()
        before = (contract.canonical_bytes(record) + b'\n') * 2
        output.write_bytes(before)
        with self.assertRaisesRegex(ValueError, 'Duplicate native'):
            capture.append_record(output, record, native_dedup=True)
        self.assertEqual(output.read_bytes(), before)

    def test_tampered_missing_and_oversize_artifacts_fail(self):
        source = self.root / 'source.data'
        for data in (b'tampered', b'x' * (capture.NATIVE_ARTIFACT_LIMIT + 1)):
            source.write_bytes(data)
            with self.assertRaises(ValueError):
                self.load()
        source.unlink()
        with self.assertRaises(OSError):
            self.load()

    def test_unsafe_paths_and_links_fail(self):
        original = json.loads(self.manifest.read_bytes())
        for path in ('../escape', '/absolute', 'C:/absolute', 'folder\\source', 'a/../source',
                     'source.data:stream', './source.data', 'https://example.invalid/source'):
            manifest = copy.deepcopy(original)
            manifest['artifacts']['source']['path'] = path
            self.manifest.write_bytes(contract.canonical_bytes(manifest))
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.load()
        self.manifest.write_bytes(contract.canonical_bytes(original))
        with patch.object(capture.stat, 'S_ISLNK', return_value=True):
            with self.assertRaisesRegex(ValueError, 'links'):
                self.load()

    def test_malformed_manifest_is_rejected(self):
        for raw in (b'{"schema_version":1,"schema_version":1,"artifacts":{}}',
                    b'{"schema_version":NaN,"artifacts":{}}',
                    b'{"schema_version":1e999,"artifacts":{}}', b'[]',
                    b'{"schema_version":true,"artifacts":{}}',
                    b'x' * (capture.NATIVE_MANIFEST_LIMIT + 1)):
            self.manifest.write_bytes(raw)
            with self.subTest(raw=raw[:60]), self.assertRaises(ValueError):
                self.load()

    def test_cross_attempt_and_source_identity_mismatches_fail_even_with_fresh_file_hash(self):
        cases = [('worker', 'selection_attempt_id', 'other-selector'),
                 ('worker', 'selection_sha256', '0' * 64),
                 ('worker', 'task_sha256', '0' * 64), ('worker', 'configuration_sha256', '0' * 64),
                 ('worker', 'task_id', 'other-task'), ('worker', 'content', 'tampered output')]
        for role, key, value in cases:
            native_fixture(self.root, supplements=False)
            self.alter(role, lambda d: d['outcome']['payload']['attempt']['worker_output'].__setitem__(key, value))
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.load()
        native_fixture(self.root, supplements=False)
        self.alter('worker', lambda d: d['outcome']['payload']['attempt']['worker_output']['source'].__setitem__('content_sha256', '0' * 64))
        with self.assertRaises(ValueError):
            self.load()

    def test_delivery_correlates_prepared_view_not_provider_response(self):
        for key, value in [('response_sha256', '0' * 64), ('source_sha256', '0' * 64),
                           ('task_id', 'other-task'), ('configuration_sha256', '0' * 64)]:
            native_fixture(self.root)
            self.alter('receiver_readback', lambda d: d['events'][0]['engine'].__setitem__(key, value))
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.load()
        native_fixture(self.root)
        self.alter('receiver_readback', lambda d: d['events'].append(d['events'][0]))
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            self.load()

    def test_prior_review_mismatch_is_not_rebound_to_new_capture(self):
        self.alter('prior_review', lambda d: d['identity'].__setitem__('worker_content_utf8_sha256', '0' * 64))
        with self.assertRaises(ValueError):
            self.load()

    def test_absent_optional_schema_revision_is_preserved(self):
        native_fixture(self.root, supplements=False)
        def remove(d):
            worker = d['outcome']['payload']['attempt']['worker_output']
            worker['read'].pop('schema_revision')
            worker['source']['captured_read'].pop('schema_revision')
            worker['source']['validated_read'].pop('schema_revision')
        self.alter('worker', remove)
        native = self.load()['native_attempt']
        self.assertNotIn('schema_revision', native['worker_read'])
        self.assertNotIn('schema_revision', native['source']['captured_read'])

    def test_output_cannot_alias_selected_inputs_or_use_links(self):
        before = {p: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        for path in (self.manifest, self.root / 'source.data'):
            with self.assertRaisesRegex(ValueError, 'aliases'):
                capture.import_native_attempt(self.manifest, self.root, output=path)
        alias = self.root / 'hardlink.jsonl'
        os.link(self.root / 'source.data', alias)
        with self.assertRaisesRegex(ValueError, 'aliases'):
            capture.import_native_attempt(self.manifest, self.root, output=alias)
        output = self.root / 'capture.jsonl'
        # A lock alias is also protected, even though exclusive creation would fail.
        os.link(self.root / 'source.data', output.with_name(output.name + '.lock'))
        with self.assertRaisesRegex(ValueError, 'aliases'):
            capture.import_native_attempt(self.manifest, self.root, output=output)
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)
        with patch.object(capture.stat, 'S_ISLNK', return_value=True):
            with self.assertRaisesRegex(ValueError, 'links'):
                capture.append_record(output, {}, native_dedup=True)
        self.assertFalse(output.exists())

    def test_native_destination_does_not_mix_legacy_rows(self):
        output = self.root / 'capture.jsonl'
        legacy = copy.deepcopy(self.load())
        legacy.pop('native_attempt')
        legacy['source_provenance']['source_type'] = 'explicit_input_and_git_status'
        capture.append_record(output, legacy)
        before = output.read_bytes()
        with self.assertRaisesRegex(ValueError, 'dedicated'):
            capture.append_record(output, self.load(), native_dedup=True)
        self.assertEqual(output.read_bytes(), before)

    def test_native_cli_requires_explicit_output(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tools/swag_passive_capture.py'),
                                 '--native-manifest', str(self.manifest), '--evidence-root', str(self.root)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--output', result.stderr)

    def test_cli_does_not_echo_rejected_private_content(self):
        self.manifest.write_text('{"PRIVATE BODY":', encoding='utf-8')
        output = self.root / 'capture.jsonl'
        result = subprocess.run([sys.executable, str(ROOT / 'tools/swag_passive_capture.py'),
                                 '--native-manifest', str(self.manifest), '--evidence-root', str(self.root),
                                 '--output', str(output)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('rejected', result.stderr)
        self.assertNotIn('PRIVATE BODY', result.stderr)
        self.assertNotIn(str(self.root), result.stderr)
        self.assertFalse(output.exists())


class CaptureTests(unittest.TestCase):
    def test_git_error_is_unknown_not_clean(self):
        with patch.object(capture.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'failed')):
            self.assertIsNone(capture._collect_changed_files(ROOT, None))

    def test_git_rename_preserves_both_names_and_quotes(self):
        result = subprocess.CompletedProcess([], 0, 'R  new name.py\0old name.py\0 M a\'b.py\0', '')
        with patch.object(capture.subprocess, 'run', return_value=result):
            self.assertEqual(capture._collect_changed_files(ROOT, None), ['new name.py', 'old name.py', "a'b.py"])

    def test_two_captures_preserve_first_record(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'observations.jsonl'
            capture.append_record(output, {'id': 'first'})
            capture.append_record(output, {'id': 'second'})
            self.assertEqual([json.loads(row)['id'] for row in output.read_text().splitlines()],
                             ['first', 'second'])

    def test_partial_tail_is_preserved_and_lock_released(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'observations.jsonl'
            output.write_bytes(b'{"partial":')
            with self.assertRaisesRegex(ValueError, 'Incomplete'):
                capture.append_record(output, {'id': 'second'})
            self.assertEqual(output.read_bytes(), b'{"partial":')
            self.assertFalse(output.with_name(output.name + '.lock').exists())

    def test_busy_writer_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'observations.jsonl'
            lock = output.with_name(output.name + '.lock')
            lock.write_text('owner')
            with self.assertRaises(FileExistsError):
                capture.append_record(output, {'id': 'second'})
            self.assertEqual(lock.read_text(), 'owner')

    def test_unknown_outcomes_are_not_training_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'observations.jsonl'
            result = subprocess.run([sys.executable, str(ROOT / 'tools/swag_passive_capture.py'),
                '--intent-text', 'fixture only', '--selected-question-ids', 'fixture.check',
                '--changed-files', 'fixture.py', '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(output.read_text())
            self.assertIsNone(record['confidence'])
            self.assertIsNone(record['user_acceptance'])
            self.assertTrue(all(value is None for value in record['outcome'].values()))
            self.assertFalse(record['training_consent'])
            self.assertEqual(record['label_status'], 'unreviewed')
            from jsonschema import Draft202012Validator
            validator = Draft202012Validator(json.loads(capture.DEFAULT_SCHEMA.read_text()))
            validator.validate(record)
            for change in ({'label_status':'verified'}, {'training_consent':True},
                           {'route':{**record['route'], 'accessMode':'invented'}}):
                self.assertTrue(list(validator.iter_errors({**record, **change})))


if __name__ == '__main__':
    unittest.main()
