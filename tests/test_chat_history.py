import unittest
from unittest.mock import Mock
from backend.agent import DigitalTwinAgent, sessions


class ChatHistoryTests(unittest.TestCase):
    def setUp(self):
        sessions.clear()
        self.addCleanup(sessions.clear)
        db = Mock()
        db.search.return_value = []
        self.agent = DigitalTwinAgent('test-key', db)

    def test_failed_turn_does_not_leave_an_orphaned_user_message(self):
        self.agent._call_openrouter_with_fallbacks = Mock(side_effect=[RuntimeError('offline'), 'OK'])
        self.agent.chat('session', 'first attempt')
        self.assertEqual(sessions['session'], [])
        self.agent.chat('session', 'second attempt')
        self.assertEqual(sessions['session'], [
            {'role': 'user', 'content': 'second attempt'},
            {'role': 'assistant', 'content': 'OK'},
        ])
        sent = self.agent._call_openrouter_with_fallbacks.call_args.args[0]
        self.assertNotIn('first attempt', [message['content'] for message in sent])

    def test_provider_receives_bounded_history_before_call(self):
        sessions['session'] = [message for i in range(20) for message in (
            {'role': 'user', 'content': f'q{i}'}, {'role': 'assistant', 'content': f'a{i}'})]
        self.agent._call_openrouter_with_fallbacks = Mock(return_value='answer')
        self.agent.chat('session', 'new question')
        sent = self.agent._call_openrouter_with_fallbacks.call_args.args[0]
        self.assertEqual(len(sent), 30)  # system + 14 prior pairs + current user
        self.assertEqual(sent[1]['content'], 'q6')
        self.assertEqual(len(sessions['session']), 30)


if __name__ == '__main__':
    unittest.main()
