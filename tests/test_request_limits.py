import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

with patch('backend.vector_db.LightweightVectorDB.build_index'):
    from backend import main


class RequestLimitsTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_empty_and_oversized_session_ids_are_rejected(self):
        for session in ('', '   ', 'x' * 129):
            with self.subTest(session=session), patch.object(main.agent, 'chat') as chat:
                response = self.client.post('/api/chat', json={'session_id': session, 'message': 'hello'})
                self.assertEqual(response.status_code, 422)
                chat.assert_not_called()
        self.assertEqual(self.client.post('/api/reset-session', json={'session_id': ' '}).status_code, 422)

    def test_large_inputs_are_rejected_before_calling_provider(self):
        with patch.object(main.agent, 'chat') as chat, patch.object(main.agent, 'analyze_compatibility') as analyze:
            self.assertEqual(self.client.post('/api/chat', json={'session_id': 's', 'message': 'x' * 4001}).status_code, 422)
            self.assertEqual(self.client.post('/api/analyze-compatibility', json={'job_description': 'x' * 16001}).status_code, 422)
            chat.assert_not_called()
            analyze.assert_not_called()

    def test_limits_allow_boundary_values(self):
        with patch.object(main.agent, 'chat', return_value='ok'):
            response = self.client.post('/api/chat', json={'session_id': 's' * 128, 'message': 'x' * 4000})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'reply': 'ok'})


if __name__ == '__main__':
    unittest.main()
