"""Developer read-model boundary checks without fabricated training observations."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import swag_dev_status as dev
import swag_rrflow as rrflow


class DeveloperStatusTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        environment = {key: value for key, value in os.environ.items() if not key.startswith('SWAG_')}
        environment['SWAG_TRACE_DIR'] = str(self.directory / 'traces')
        context = patch.dict(os.environ, environment, clear=True)
        context.start()
        self.addCleanup(context.stop)

    def test_unconfigured_is_unknown_and_has_no_execution_authority(self):
        value = dev.status()
        self.assertEqual(value['engine']['state'], 'not_configured')
        self.assertEqual(value['training']['dataset']['state'], 'not_configured')
        self.assertEqual(value['training']['runs'], [])
        self.assertFalse(value['training']['launchAvailable'])
        self.assertFalse(value['optimization']['automaticPromotionAvailable'])
        self.assertTrue(all(flag is False for flag in value['integration'].values()))

    def test_invalid_registry_does_not_hide_engine_or_trace_status(self):
        path = self.directory / 'registry.json'
        path.write_text('[]')
        os.environ['SWAG_TRAINING_RUNS_FILE'] = str(path)
        result = dev.status()
        self.assertEqual(result['training']['registryState'], 'invalid_registry')
        self.assertEqual(result['observability']['invalidFiles'], 0)

    def test_unavailable_artifact_is_not_a_live_or_completed_run(self):
        path = self.directory / 'registry.json'
        path.write_text(json.dumps({'schemaVersion': 1, 'runs': [{'id': 'missing', 'directory': str(self.directory / 'missing')}]}))
        os.environ['SWAG_TRAINING_RUNS_FILE'] = str(path)
        run = dev.training_runs()[0]
        self.assertEqual(run['state'], 'unavailable')
        self.assertEqual(run['metrics'], {})
        self.assertFalse(run['promotionAuthorized'])

    def test_engine_failure_is_visible_without_exception_content(self):
        os.environ['SWAG_RRFLOW_CONNECTION_FILE'] = 'configured'
        with patch('swag_rrflow.status', side_effect=ValueError('private server credentials')):
            value = dev.status()
        self.assertEqual(value['engine']['state'], 'unavailable')
        self.assertNotIn('private server credentials', json.dumps(value))

    def test_connection_rejects_remote_plaintext_before_reading_credential(self):
        config = self.directory / 'connection.json'
        config.write_text(json.dumps({'schemaVersion': 1, 'baseUrl': 'http://example.com',
                                     'instanceId': 'test', 'credentialFile': 'absent.json'}))
        os.environ['SWAG_RRFLOW_CONNECTION_FILE'] = str(config)
        with self.assertRaisesRegex(rrflow.RRFlowError, 'HTTPS'):
            rrflow.connection()

    def test_redirect_handler_never_forwards_credentials(self):
        self.assertIsNone(rrflow.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.com'))


if __name__ == '__main__':
    unittest.main()
