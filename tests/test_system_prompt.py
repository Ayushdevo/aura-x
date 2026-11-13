import unittest
from unittest.mock import Mock
from backend.agent import DigitalTwinAgent


class SystemPromptTests(unittest.TestCase):
    def test_prompt_uses_supplied_context_without_a_stale_hardcoded_bio(self):
        agent = DigitalTwinAgent('test', Mock())
        prompt = agent.get_system_prompt('Education: a verified degree in the current resume')
        self.assertIn('Education: a verified degree in the current resume', prompt)
        self.assertIn('only the retrieved resume context', prompt)
        self.assertNotIn('B.S. Hons.', prompt)
        self.assertNotIn('10x.ai', prompt)


if __name__ == '__main__':
    unittest.main()
