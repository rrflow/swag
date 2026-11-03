"""Contract tests use software fixtures, never training labels or model evidence."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import swag_knowledge as knowledge
import swag_mcp_server as mcp
from jsonschema import Draft202012Validator


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.config = self.root / 'binding.json'
        self.binding = {'schemaVersion': 1, 'projectId': 'contract-fixture', 'repo': '.',
                        'template': 'python_delivery_review', 'inputs': {}}
        for slot in ('packaging', 'tests', 'ci'):
            (self.root / f'{slot}.txt').write_text(f'Software fixture for {slot}')
            self.binding['inputs'][slot] = [f'{slot}.txt']
        self.write_binding()
        env = patch.dict(os.environ, {'SWAG_KNOWLEDGE_BINDING_FILE': str(self.config),
                                     'SWAG_TRACE_DIR': str(self.root / 'traces')})
        env.start()
        self.addCleanup(env.stop)

    def write_binding(self):
        self.config.write_text(json.dumps(self.binding))

    def preview(self):
        return knowledge.preview(self.config)

    def answer(self, row, value, status='answered'):
        return {'schema': 'swag.decision-answer/v1', 'inputSha256': row['inputSha256'],
                'mode': row['decision']['mode'], 'status': status, 'value': value,
                'references': [row['practice']['sha256']]}

    def test_real_questions_all_modes_and_no_completion_claim(self):
        result = self.preview()
        self.assertEqual({r['decision']['mode'] for r in result['requirements']}, {'choice', 'score', 'binary'})
        for row in result['requirements']:
            self.assertTrue(row['practice']['question']['id'].startswith('python.'))
            self.assertEqual(row['practice']['freshness'], 'not_reverified')
            self.assertEqual(row['fulfillment'], 'unassessed')
        self.assertFalse(result['executionAvailable'])
        self.assertNotIn(str(self.root), json.dumps(result))
        self.assertNotIn('Software fixture', json.dumps(result))

    def test_typed_answers_validate_structure_without_attesting_truth(self):
        schema = json.loads((ROOT / 'config/knowledge/decision_answer.schema.json').read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        for row, value in zip(self.preview()['requirements'], (False, 'explicit_groups', 2)):
            answer = self.answer(row, value)
            validator.validate(answer)
            result = knowledge.validate_decision(row['id'], answer, self.config)
            self.assertTrue(result['contractValid'])
            self.assertFalse(result['correctnessVerified'])
            self.assertFalse(result['executionAuthorized'])
            self.assertEqual(result['fulfillment'], 'unassessed')

    def test_ordinary_edit_invalidates_only_affected_requirements_and_refresh_recovers(self):
        before = self.preview()
        first = before['requirements'][0]
        old = self.answer(first, False)
        (self.root / 'packaging.txt').write_text('Ordinary fixture edit')
        after = self.preview()
        self.assertNotEqual(first['inputSha256'], after['requirements'][0]['inputSha256'])
        self.assertEqual(before['requirements'][1:], after['requirements'][1:])
        with self.assertRaisesRegex(ValueError, 'Stale'):
            knowledge.validate_decision(first['id'], old, self.config)
        refreshed = after['requirements'][0]
        self.assertTrue(knowledge.validate_decision(refreshed['id'], self.answer(refreshed, None, 'abstained'), self.config)['contractValid'])
        (self.root / 'unrelated.txt').write_text('Unrelated fixture edit')
        self.assertEqual(after, self.preview())

    def test_missing_inputs_remain_unknown_and_allow_abstention(self):
        (self.root / 'packaging.txt').unlink()
        row = self.preview()['requirements'][0]
        self.assertEqual(row['state'], 'missing_inputs')
        with self.assertRaisesRegex(ValueError, 'bound inputs'):
            knowledge.validate_decision(row['id'], self.answer(row, True), self.config)
        self.assertTrue(knowledge.validate_decision(row['id'], self.answer(row, None, 'abstained'), self.config)['contractValid'])

    def test_rejects_wrong_types_ranges_options_and_nonfinite_scores(self):
        rows = self.preview()['requirements']
        for row, values in zip(rows, ([1, 'yes', None], ['invented_option', True], [True, -1, 5, float('nan'), float('inf')])):
            for value in values:
                with self.subTest(mode=row['decision']['mode'], value=value), self.assertRaises(ValueError):
                    knowledge.validate_decision(row['id'], self.answer(row, value), self.config)

    def test_unbound_references_and_fulfillment_claim_are_rejected(self):
        row = self.preview()['requirements'][0]
        answer = self.answer(row, False)
        answer['references'] = ['0' * 64]
        with self.assertRaisesRegex(ValueError, 'Unbound'):
            knowledge.validate_decision(row['id'], answer, self.config)
        answer = self.answer(row, False)
        answer['fulfilled'] = True
        with self.assertRaisesRegex(ValueError, 'fields'):
            knowledge.validate_decision(row['id'], answer, self.config)

    def test_paths_cannot_escape_selected_project(self):
        for path in ('../outside', '/absolute', 'C:/outside', 'folder/../../outside'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                knowledge.under(self.root, path)
        self.binding['inputs']['packaging'] = ['../outside']
        self.write_binding()
        with self.assertRaises(ValueError):
            self.preview()

    def test_unknown_slots_practices_and_duplicate_options_are_rejected(self):
        self.binding['inputs']['invented_slot'] = []
        self.write_binding()
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            self.preview()
        with self.assertRaisesRegex(ValueError, 'missing'):
            knowledge.practice({'questionSet': 'python', 'questionId': 'does_not_exist'})
        contract = copy.deepcopy(knowledge.template('python_delivery_review')['requirements'][1]['decision'])
        contract['options'][1]['id'] = contract['options'][0]['id']
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            knowledge.mode_contract(contract)

    def test_mcp_reads_same_projection_and_rejects_stale_answer_with_trace(self):
        def call(name, arguments):
            return mcp._handle_message({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                                       'params': {'name': name, 'arguments': arguments}})['result']
        response = call('knowledge_preview', {})
        self.assertEqual(json.loads(response['content'][0]['text']), self.preview())
        row = self.preview()['requirements'][0]
        answer = self.answer(row, False)
        (self.root / 'packaging.txt').write_text('Changed fixture')
        result = call('validate_template_decision', {'requirementId': row['id'], 'answer': answer})
        self.assertTrue(result['isError'])
        self.assertIn('swag/traceId', result['_meta'])


if __name__ == '__main__':
    unittest.main()
