import json
import unittest
from unittest.mock import Mock
from backend.agent import AnalysisUnavailable, DigitalTwinAgent


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        db = Mock()
        db.search.return_value = []
        self.agent = DigitalTwinAgent('test', db)
        self.valid = {'compatibility_score': 0, 'matching_skills': [], 'skills_to_learn': [],
                      'strengths': [], 'gaps_analysis': 'gap', 'fit_verdict': 'verdict'}

    def test_valid_zero_score_is_distinct_from_provider_failure(self):
        self.agent._call_openrouter_with_fallbacks = Mock(return_value=json.dumps(self.valid))
        self.assertEqual(self.agent.analyze_compatibility('job'), self.valid)
        self.agent._call_openrouter_with_fallbacks.side_effect = RuntimeError('offline')
        with self.assertRaises(AnalysisUnavailable):
            self.agent.analyze_compatibility('job')

    def test_rejects_invalid_json_and_malformed_fields(self):
        cases = ['not json', '[]'] + [json.dumps({**self.valid, **change}) for change in (
            {'compatibility_score': True}, {'compatibility_score': 101},
            {'matching_skills': 'Python'}, {'strengths': [1]}, {'fit_verdict': None})]
        for raw in cases:
            self.agent._call_openrouter_with_fallbacks = Mock(return_value=raw)
            with self.subTest(raw=raw), self.assertRaises(AnalysisUnavailable):
                self.agent.analyze_compatibility('job')

class CompatibilityEndpointTests(unittest.TestCase):
    def test_provider_failure_is_503(self):
        from unittest.mock import patch
        from fastapi import HTTPException
        with patch('backend.vector_db.LightweightVectorDB.build_index'):
            from backend import main
        with patch.object(main.agent, 'analyze_compatibility', side_effect=AnalysisUnavailable('offline')):
            with self.assertRaises(HTTPException) as raised:
                main.post_analyze_compatibility(main.CompatibilityRequest(job_description='job'))
        self.assertEqual(raised.exception.status_code, 503)


if __name__ == '__main__':
    unittest.main()
