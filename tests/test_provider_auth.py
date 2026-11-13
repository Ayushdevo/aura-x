import io
import json
import unittest
import urllib.error
from unittest.mock import Mock, patch
from backend.agent import DigitalTwinAgent


def http_error(status):
    return urllib.error.HTTPError('https://provider.invalid', status, 'error', {}, io.BytesIO(b'error'))


class ProviderRetryTests(unittest.TestCase):
    def setUp(self):
        self.agent = DigitalTwinAgent('test', Mock(), model='primary')

    def test_unauthorized_response_is_not_retried_for_each_model(self):
        with patch('backend.agent.urllib.request.urlopen', side_effect=http_error(401)) as call:
            with self.assertRaises(urllib.error.HTTPError):
                self.agent._call_openrouter_with_fallbacks([])
        self.assertEqual(call.call_count, 1)

    def test_temporary_server_failure_still_tries_a_fallback(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps({'choices': [{'message': {'content': 'ok'}}]}).encode()
        with patch('backend.agent.urllib.request.urlopen', side_effect=[http_error(503), response]) as call:
            self.assertEqual(self.agent._call_openrouter_with_fallbacks([]), 'ok')
        self.assertEqual(call.call_count, 2)


if __name__ == '__main__':
    unittest.main()
