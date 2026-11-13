import asyncio
import threading
import unittest
from unittest.mock import patch
import httpx

with patch('backend.vector_db.LightweightVectorDB.build_index'):
    from backend import main


class NonblockingTests(unittest.IsolatedAsyncioTestCase):
    async def test_chat_does_not_block_config_request(self):
        started, release = threading.Event(), threading.Event()
        def slow_chat(*args):
            started.set()
            release.wait(timeout=3)
            return 'reply'
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
            with patch.object(main.agent, 'chat', side_effect=slow_chat):
                task = asyncio.create_task(client.post('/api/chat', json={'session_id': 's', 'message': 'hello'}))
                try:
                    self.assertTrue(await asyncio.to_thread(started.wait, 2))
                    self.assertFalse(task.done(), 'chat blocked the event loop until it finished')
                    response = await asyncio.wait_for(client.get('/api/config'), timeout=1)
                    self.assertEqual(response.status_code, 200)
                finally:
                    release.set()
                    await task

    async def test_compatibility_endpoint_is_dispatched_as_sync(self):
        import inspect
        self.assertFalse(inspect.iscoroutinefunction(main.post_analyze_compatibility))


class SessionLockTests(unittest.TestCase):
    def test_same_session_turns_are_serialized(self):
        from concurrent.futures import ThreadPoolExecutor
        from backend.agent import DigitalTwinAgent, sessions
        from unittest.mock import Mock
        sessions.clear()
        self.addCleanup(sessions.clear)
        db = Mock()
        db.search.return_value = []
        agent = DigitalTwinAgent('test', db)
        first_started, release, second_started = threading.Event(), threading.Event(), threading.Event()
        def provider(messages, **kwargs):
            if messages[-1]['content'] == 'first':
                first_started.set()
                release.wait(timeout=3)
            else:
                second_started.set()
            return 'ok'
        agent._call_openrouter_with_fallbacks = provider
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(agent.chat, 'same-session', 'first')
            self.assertTrue(first_started.wait(timeout=1))
            second = pool.submit(agent.chat, 'same-session', 'second')
            try:
                self.assertFalse(second_started.wait(timeout=0.1))
            finally:
                release.set()
            self.assertEqual(first.result(timeout=2), 'ok')
            self.assertEqual(second.result(timeout=2), 'ok')
        self.assertEqual([m['content'] for m in sessions['same-session']], ['first', 'ok', 'second', 'ok'])


if __name__ == '__main__':
    unittest.main()
