import json
import unittest
from unittest.mock import Mock, patch
from backend.agent import DigitalTwinAgent


def response(content):
    result = Mock()
    result.__enter__ = Mock(return_value=result)
    result.__exit__ = Mock(return_value=False)
    result.read.return_value = json.dumps({'choices': [{'message': {'content': content}}]}).encode()
    return result


class ModelReplyTests(unittest.TestCase):
    def test_empty_or_non_text_reply_tries_next_model(self):
        agent = DigitalTwinAgent('test', Mock(), model='primary')
        for invalid in (None, '', '  ', {'unexpected': 'object'}):
            with self.subTest(invalid=invalid), patch('backend.agent.urllib.request.urlopen', side_effect=[response(invalid), response('valid')]) as call:
                self.assertEqual(agent._call_openrouter_with_fallbacks([]), 'valid')
                self.assertEqual(call.call_count, 2)

    def test_all_empty_replies_raise_instead_of_returning_none(self):
        agent = DigitalTwinAgent('test', Mock(), model='primary')
        with patch('backend.agent.urllib.request.urlopen', side_effect=[response(None) for _ in range(5)]):
            with self.assertRaises(ValueError):
                agent._call_openrouter_with_fallbacks([])


if __name__ == '__main__':
    unittest.main()
