import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

with patch('backend.vector_db.LightweightVectorDB.build_index'):
    from backend import main


class ErrorResponseTests(unittest.TestCase):
    def test_internal_exceptions_are_not_exposed(self):
        client = TestClient(main.app, raise_server_exceptions=False)
        for endpoint, method, payload in [
            ('/api/chat', 'chat', {'session_id': 's', 'message': 'hello'}),
            ('/api/analyze-compatibility', 'analyze_compatibility', {'job_description': 'job'}),
        ]:
            with self.subTest(endpoint=endpoint), patch.object(main.agent, method, side_effect=RuntimeError('secret diagnostic')):
                response = client.post(endpoint, json=payload)
                self.assertEqual(response.status_code, 500)
                self.assertNotIn('secret diagnostic', response.text)
                self.assertEqual(response.json()['detail'], 'Request processing failed')


if __name__ == '__main__':
    unittest.main()
