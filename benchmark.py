import asyncio
import aiohttp
import argparse
import time
from statistics import mean, stdev
import numpy as np
async def fetch(session, url, timeout=2):
    start_time = time.time()
    try:
        async with session.get(url, timeout=timeout) as response:
            latency = time.time() - start_time
            await response.text()
            response_time = time.time() - start_time
            if response.status != 200:
                return latency, response_time, response.status, False
            return latency, response_time, response.status, True
    except Exception as e:
        return None, time.time() - start_time, str(e), False


async def worker(url, qps, duration, results, latencies, errors, timeout, stop_flag):
    total_reqs = qps * duration
    x = 0
    async with aiohttp.ClientSession() as session:
        while not stop_flag.is_set():
            latency, response_time, status, success = await fetch(session, url, timeout)
            results.append(response_time)

            if latency:
                latencies.append(latency)

            if not success:
                errors.append(status)

            next_request_time = time.time() + 1 / qps
            sleep_time = max(0, next_request_time - time.time())
            await asyncio.sleep(sleep_time)
            x += 1
            if x == total_reqs:
                stop_flag.set()
        # After stop flag is set, any incomplete request should be considered an error
        while time.time() < next_request_time:
            errors.append('Request not completed')
            await asyncio.sleep(0.01)  # Slight delay to prevent a tight loop


async def benchmark(url, qps, num_workers, duration, timeout):
    results = []
    errors = []
    tasks = []
    latencies = []
    stop_flag = asyncio.Event()  # Use an Event to signal workers to stop
    start_time = time.time()
    # Create and start workers
    for _ in range(num_workers-1):
        assigned_qps = qps // num_workers
        task = asyncio.create_task(worker(url, assigned_qps, duration, results, latencies, errors, timeout, stop_flag))
        tasks.append(task)


    assigned_qps = qps // num_workers + qps % num_workers
    task = asyncio.create_task(worker(url, assigned_qps, duration, results, latencies, errors, timeout, stop_flag))
    tasks.append(task)

    # Run the benchmark for the specified duration
    # await asyncio.sleep(duration)
    # stop_flag.set()  # Signal workers to stop

    # Allow tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)
    await  asyncio.sleep(0.05)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time}")


    percentile_50 = np.percentile(results, 50) if len(results) > 1 else None
    percentile_90 = np.percentile(results, 90) if len(results) > 1 else None
    percentile_97 = np.percentile(results, 97) if len(results) > 1 else None
    percentile_99 = np.percentile(results, 99) if len(results) > 1 else None

    latency_percentile_50 = np.percentile(latencies, 50) if len(latencies) > 1 else None
    latency_percentile_90 = np.percentile(latencies, 90) if len(latencies) > 1 else None
    latency_percentile_97 = np.percentile(latencies, 97) if len(latencies) > 1 else None
    latency_percentile_99 = np.percentile(latencies, 99) if len(latencies) > 1 else None

    report = {
        "config": {
            "url": url,
            "qps": qps,
            "duration": duration,
            "num_workers": num_workers,
            "timeout": timeout
        },
        "total_requests": len(results),
        "errors": len(errors),
        "mean_response_time": mean(results) if results else None,
        "std_response_time": stdev(results) if len(results) > 1 else None,
        "response_time_p50": percentile_50,
        "response_time_p90": percentile_90,
        "response_time_p97": percentile_97,
        "response_time_p99": percentile_99,
        "mean_latency": mean(latencies) if latencies else None,
        "std_latency": stdev(latencies) if len(latencies) > 1 else None,
        "latency_p50": latency_percentile_50,
        "latency_p90": latency_percentile_90,
        "latency_p97": latency_percentile_97,
        "latency_p99": latency_percentile_99,

    }

    if len(errors) > 0:
        report['errors_status'] = list(set(errors))

    print(report)

    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP Load Testing Tool')
    parser.add_argument('--url', type=str, help='The HTTP address to test')
    parser.add_argument('--qps', type=int, required=True, help='Queries per second')
    parser.add_argument('--duration', type=int, default=10, help='Duration of the test in seconds')
    parser.add_argument('--timeout', type=float, default=2, help='Duration of the timeout in seconds')
    parser.add_argument('--num_workers', type=int, required=True, help='Number of workers')
    args = parser.parse_args()
    asyncio.run(benchmark(args.url, args.qps, args.num_workers, args.duration, args.timeout))

