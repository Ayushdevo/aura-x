import unittest
from backend.vector_db import LightweightVectorDB


class KeywordSearchTests(unittest.TestCase):
    def setUp(self):
        self.db = LightweightVectorDB.__new__(LightweightVectorDB)

    def test_punctuation_only_and_stopwords_do_not_create_matches(self):
        self.assertEqual(self.db.keyword_overlap_score('the, and? !!!', 'the, and? !!!'), 0.0)
        self.assertEqual(self.db.keyword_overlap_score('!!!', 'Python !!!'), 0.0)

    def test_case_and_surrounding_punctuation_are_normalized(self):
        self.assertEqual(self.db.keyword_overlap_score('Python, SQL!', 'Python SQL.'), 1.0)
        self.assertEqual(self.db.keyword_overlap_score('THE Python', 'python'), 1.0)


if __name__ == '__main__':
    unittest.main()
