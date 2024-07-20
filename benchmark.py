import asyncio
import aiohttp
import argparse
import time
from statistics import mean, stdev
import numpy as np
async def fetch(session, url):
    start_time = time.time()
    try:
        async with session.get(url) as response:
            # print(response)
            latency = time.time() - start_time
            if response.status != 200:
                return latency, response.status, False
            return latency, response.status, True
    except Exception as e:
        print(e)
        return time.time() - start_time, None, False


async def worker(url, qps, results, errors):
    # print("URL: ", url)
    async with aiohttp.ClientSession() as session:
        while True:
            latency, status, success = await fetch(session, url)
            results.append(latency)

            if not success:
                errors.append(status)
            await asyncio.sleep(1 / qps)




async def benchmark(url, qps, num_workers, duration):
    results = []
    errors = []
    tasks = []

    # Number of concurrent workers based on QPS
    # num_workers = qps
    for _ in range(num_workers):
        task = asyncio.create_task(worker(url, qps // num_workers, results, errors))
        tasks.append(task)

    await asyncio.sleep(duration)

    for task in tasks:
        task.cancel()

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:

        pass

    percentile_50 = np.percentile(results, 50)
    percentile_90 = np.percentile(results, 90)
    percentile_97 = np.percentile(results, 97)
    percentile_99 = np.percentile(results, 99)

    report = {
        "config": {
            "url": url,
            "qps": qps,
            "duration": duration,
            "num_workers": num_workers
        },
        "total_requests": len(results),
        "errors": len(errors),
        "mean_latency": mean(results) if results else None,
        "std_latency": stdev(results) if len(results) > 1 else None,
        "latency_p50": percentile_50,
        "latency_p90": percentile_90,
        "latency_p97": percentile_97,
        "latency_p99": percentile_99,
    }

    print(report)

    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP Load Testing Tool')
    parser.add_argument('--url', type=str, help='The HTTP address to test')
    parser.add_argument('--qps', type=int, required=True, help='Queries per second')
    parser.add_argument('--duration', type=int, default=10, help='Duration of the test in seconds')
    parser.add_argument('--num_workers', type=int, required=True, help='Number of workers')
    args = parser.parse_args()
    asyncio.run(benchmark(args.url, args.qps, args.duration))
