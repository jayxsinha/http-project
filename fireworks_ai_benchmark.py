import asyncio
import aiohttp
import time
import numpy as np
import argparse
async def fetch(session, url, payload, headers, timeout=2):
    start_time = time.time()
    time_to_first_token = None
    try:
        async with session.post(url, json=payload, headers=headers, timeout=timeout) as response:
            if payload['stream']:
                async for chunk in response.content.iter_chunked(1024):
                    if time_to_first_token is None:
                        time_to_first_token = time.time() - start_time

            latency = time.time() - start_time
            if response.status != 200:
                return latency, time_to_first_token, response.status, False
            return latency, time_to_first_token, response.status, True
    except Exception as e:
        print(e)
        return time.time() - start_time, None, None, False

async def fireworks_ai_worker(url, qps, payload, headers, results, errors, ttft, timeout):
    async with aiohttp.ClientSession() as session:
        while True:
            latency, time_to_first_token, status, success = await fetch(session, url, payload, headers, timeout)
            results.append(latency)

            if payload['stream']:
                if time_to_first_token:
                    ttft.append(time_to_first_token)

            if not success:
                errors.append(status)
            await asyncio.sleep(1 / qps)

async def benchmark(url, model, prompt, max_tokens, token, stream, qps, duration, num_workers, timeout):
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "logprobs": 2,
        "echo": True,
        "temperature": 1,
        "top_p": 1,
        "top_k": 50,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "n": 1,
        "stop": "<string>",
        "stream": stream,
        "context_length_exceeded_behavior": "truncate",
        "user": "<string>"
    }

    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }

    results = []
    errors = []
    tasks = []
    ttft = []
    # Number of concurrent workers based on QPS
    # num_workers = qps
    for _ in range(num_workers):
        task = asyncio.create_task(fireworks_ai_worker(url, qps // num_workers, payload, headers, results, errors, ttft, timeout))
        tasks.append(task)

    # Create an additional worker when qps % num_workers > 0
    if qps % num_workers > 0:
        task = asyncio.create_task(
            fireworks_ai_worker(url, qps % num_workers, payload, headers, results, errors, ttft, timeout))
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
          "fireworks_payload": payload,
          "qps": qps,
          "duration": duration,
          "url": url,
          "num_workers": num_workers
        },
        "total_requests": len(results),
        "errors": len(errors),
        "mean_latency": np.mean(results) if len(results) > 0 else None,
        "std_latency": np.std(results) if len(results) > 1 else None,
        "latency_p50": percentile_50,
        "latency_p90": percentile_90,
        "latency_p97": percentile_97,
        "latency_p99": percentile_99,
    }
    if stream:
        report["mean_time_to_first_token"] = np.mean(ttft) if len(ttft) > 0 else None
        report["std_time_to_first_token"] = np.std(ttft) if len(ttft) > 1 else None
        report["time_to_first_token_p50"] = np.percentile(ttft, 50) if len(ttft) > 1 else None
        report["time_to_first_token_p90"] = np.percentile(ttft, 90) if len(ttft) > 1 else None
        report["time_to_first_token_p97"] = np.percentile(ttft, 97) if len(ttft) > 1 else None
        report["time_to_first_token_p99"] = np.percentile(ttft, 99) if len(ttft) > 1 else None


    print(report)

    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FireworksAI API Load Testing Tool')
    parser.add_argument('--url',default="https://api.fireworks.ai/inference/v1/completions" ,type=str, help='The HTTP address to test')
    parser.add_argument('--model', default="accounts/fireworks/models/llama-v3-8b-instruct-hf", type=str, help='The model to be used')
    parser.add_argument('--prompt', default="The snow is white because ", type=str, help='The prompt to be used')
    parser.add_argument('--token', required=True, type=str, help='Fireworks AI Token')
    parser.add_argument('--max_tokens', default=25, type=int, help='Max Tokens to be generated')
    parser.add_argument('--stream', default=False, type=bool, help='If streaming is to be enabled')
    parser.add_argument('--qps', type=int, default=1, help='Queries per second')
    parser.add_argument('--timeout', type=int, default=2, help='Timeout duration in seconds')
    parser.add_argument('--num_workers', type=int, required=True, help='Number of workers')
    parser.add_argument('--duration', type=int, default=1, help='Duration of the test in seconds')

    args = parser.parse_args()
    asyncio.run(benchmark(args.url, args.model, args.prompt, args.max_tokens,
                          args.token, args.stream, args.qps, args.duration, args.num_workers, args.timeout))