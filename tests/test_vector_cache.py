import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from backend.vector_db import LightweightVectorDB


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'cache.json'
        self.db = LightweightVectorDB.__new__(LightweightVectorDB)
        self.db.chunks = [{'category': 'summary', 'content': 'Current resume'}]
        self.db.model = 'embedding-v2'
        self.db.embeddings = []
        self.db.fetch_embedding_remote = Mock(return_value=[0.25, 0.75])
        self.patcher = patch('backend.vector_db.CACHE_FILE', str(self.path))
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_rebuilds_stale_content_even_when_chunk_count_matches(self):
        self.path.write_text(json.dumps({'model': self.db.model, 'chunks': [{'category': 'summary', 'content': 'Old resume'}], 'embeddings': [[1, 0]]}))
        self.db.build_index()
        self.db.fetch_embedding_remote.assert_called_once_with('Current resume')
        self.assertEqual(self.db.chunks[0]['content'], 'Current resume')
        self.assertEqual(json.loads(self.path.read_text())['model'], self.db.model)

    def test_reuses_exact_cache_and_rebuilds_wrong_model_or_bad_vectors(self):
        valid = {'model': self.db.model, 'chunks': self.db.chunks, 'embeddings': [[1, 0]]}
        self.path.write_text(json.dumps(valid))
        self.db.build_index()
        self.db.fetch_embedding_remote.assert_not_called()
        self.assertEqual(self.db.embeddings, [[1, 0]])
        for change in ({'model': 'old'}, {'embeddings': []}, {'embeddings': [[float('nan'), 0]]}):
            self.db.fetch_embedding_remote.reset_mock()
            self.path.write_text(json.dumps({**valid, **change}))
            self.db.build_index()
            self.db.fetch_embedding_remote.assert_called_once()


if __name__ == '__main__':
    unittest.main()
