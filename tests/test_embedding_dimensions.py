import unittest
from unittest.mock import Mock
from backend.vector_db import LightweightVectorDB


class EmbeddingDimensionsTests(unittest.TestCase):
    def setUp(self):
        self.db = LightweightVectorDB.__new__(LightweightVectorDB)
        self.db.api_key = 'test'
        self.db.chunks = [{'category': 'skill', 'content': 'Python expertise'}]
        self.db.embeddings = [[1.0, 0.0]]

    def test_mismatched_or_invalid_query_vectors_use_keyword_fallback(self):
        for vector in ([1.0], [float('nan'), 0.0], []):
            self.db.fetch_embedding_remote = Mock(return_value=vector)
            self.assertEqual(self.db.search('Python'), self.db.chunks)
            self.assertEqual(self.db.search('Rust'), [])

    def test_invalid_stored_vectors_use_keyword_fallback(self):
        self.db.fetch_embedding_remote = Mock(return_value=[1.0, 0.0])
        for vector in ([1.0], [float('inf'), 0.0], []):
            self.db.embeddings = [vector]
            self.assertEqual(self.db.search('Python'), self.db.chunks)
            self.assertEqual(self.db.search('Rust'), [])

    def test_cosine_rejects_incompatible_vectors(self):
        for left, right in [([1.0], [1.0, 0.0]), ([float('nan')], [1.0]), ([], [])]:
            with self.assertRaises(ValueError):
                self.db.cosine_similarity(left, right)
        self.assertAlmostEqual(self.db.cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)


if __name__ == '__main__':
    unittest.main()
