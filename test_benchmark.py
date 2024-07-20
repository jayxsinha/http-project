import unittest
import asynctest
import asyncio
from unittest.mock import patch
from benchmark import fetch, worker, benchmark
import aiohttp

TEST_URL = "http://127.0.0.1:8081"

class TestBenchmark(asynctest.TestCase):
    @asynctest.patch('aiohttp.ClientSession.get')
    async def test_successful_fetch(self, mock_get):
        mock_response = asynctest.Mock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            latency, status, success = await fetch(session, TEST_URL)

        self.assertTrue(success)
        self.assertEqual(status, 200)
        self.assertIsInstance(latency, float)

    @asynctest.patch('aiohttp.ClientSession.get')
    async def test_fetch_with_error(self, mock_get):
        mock_response = asynctest.Mock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            latency, status, success = await fetch(session, TEST_URL)

        self.assertFalse(success)
        self.assertEqual(status, 500)
        self.assertIsInstance(latency, float)

    async def test_benchmark_report(self):
        url = TEST_URL
        qps = 10
        num_workers = 5
        duration = 2

        with patch('benchmark.fetch', new=asynctest.CoroutineMock(return_value=(0.1, 200, True))):
            report = await benchmark(url, qps, num_workers, duration)

        self.assertIn('total_requests', report)
        self.assertIn('errors', report)
        self.assertIn('mean_latency', report)
        self.assertIn('std_latency', report)
        self.assertIn('latency_p50', report)
        self.assertIn('latency_p90', report)
        self.assertIn('latency_p97', report)
        self.assertIn('latency_p99', report)

        self.assertEqual(report['total_requests'], qps * duration)
        self.assertEqual(report['errors'], 0)
        self.assertAlmostEqual(report['mean_latency'], 0.1, delta=0.01)


if __name__ == '__main__':
    unittest.main()