from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import swag_signal_sink as sink


class SignalSinkTests(unittest.TestCase):
    def publish(self, replies):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sink, 'project_run', return_value={}), \
                    patch.object(sink, 'report_record', return_value={'event_id': 'fixture'}), \
                    patch.object(sink, 'exchange', side_effect=replies) as exchange:
                result = sink.publish_and_verify(Path('unused'), 'http://127.0.0.1:8892',
                                                'fixture-secret', 'swag', 'expected', Path(directory) / 'out')
                return result, exchange.call_args_list

    def test_retry_and_exact_readback(self):
        result, calls = self.publish([{'devspace': 'expected'},
            {'devspace': 'expected', 'accepted': 1, 'new': 1, 'replaced': 0},
            {'devspace': 'expected', 'accepted': 1, 'new': 0, 'replaced': 1},
            {'devspace': 'expected', 'turns': [{'event_id': 'fixture'}]}])
        self.assertTrue(result['storedMatches'])
        self.assertFalse(result['engineIntegrated'])
        self.assertEqual(calls[1], calls[2])
        self.assertNotIn('fixture-secret', str(result))

    def test_wrong_identity_blocks_post(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sink, 'project_run', return_value={}), \
                    patch.object(sink, 'report_record', return_value={'event_id': 'fixture'}), \
                    patch.object(sink, 'exchange', return_value={'devspace': 'wrong'}) as exchange:
                with self.assertRaisesRegex(ValueError, 'unexpected devspace'):
                    sink.publish_and_verify(Path('unused'), 'http://127.0.0.1:8892', 'secret',
                                            'swag', 'expected', Path(directory) / 'out')
                self.assertEqual(exchange.call_count, 1)

    def test_duplicate_creation_not_idempotent(self):
        ack = {'devspace': 'expected', 'accepted': 1, 'new': 1, 'replaced': 0}
        with self.assertRaisesRegex(ValueError, 'Retry'):
            self.publish([{'devspace': 'expected'}, ack, ack])

    def test_changed_readback_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Stored event differs'):
            self.publish([{'devspace': 'expected'},
                {'devspace': 'expected', 'accepted': 1, 'new': 1, 'replaced': 0},
                {'devspace': 'expected', 'accepted': 1, 'new': 0, 'replaced': 1},
                {'devspace': 'expected', 'turns': [{'event_id': 'fixture', 'content': 'unexpected'}]}])

    def test_nonlocal_cleartext_endpoint_rejected(self):
        with self.assertRaisesRegex(ValueError, 'HTTPS'):
            sink.publish_and_verify(Path('unused'), 'http://example.test', 'secret', 'swag', 'expected', Path('unused'))

    def test_verify_only_never_posts(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sink, 'project_run', return_value={}), \
                    patch.object(sink, 'report_record', return_value={'event_id': 'fixture'}), \
                    patch.object(sink, 'exchange', side_effect=[{'devspace': 'expected'},
                        {'devspace': 'expected', 'turns': [{'event_id': 'fixture'}]}]) as exchange:
                receipt = sink.publish_and_verify(Path('unused'), 'http://127.0.0.1:8892', 'secret',
                    'swag', 'expected', Path(directory) / 'out', verify_only=True)
                self.assertEqual(receipt['scope'], 'signal_sink_readback')
                self.assertEqual(receipt['acknowledgements'], [])
                self.assertTrue(all(len(call.args) == 2 for call in exchange.call_args_list))


if __name__ == '__main__':
    unittest.main()
