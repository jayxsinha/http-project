# HTTP Load Testing API

This is an HTTP load testing tool built using Python's `asyncio` and `aiohttp` libraries. It allows you to benchmark the performance of a given URL by specifying the queries per second (QPS), number of workers, duration, and timeout.

---
## Updates: [08/03/2024]

1. The fixed `--qps` logic was incorrect. It was working fine for local APIs; however, when used with FireworksAI API or any other public URL like [this one](https://httpbin.org/get"), the total numbers of requested would not equal `qps * duration`.
  - **Core Issue:** The worker had a logic to timeout with `await asyncio.sleep(duration)` followed by `task.cancel()` which made the worker quit even if there were outgoing requests still waiting to be completed. 
  - **Fix:** Use `await asyncio.gather()` function to wait for all the requests to complete and then do the final processing for results. There is also now a `stop_flag` added as an `asyncio.Event()` which will help terminate the worker process gracefully.
2. Previous logic indicated that we would need to create an extra worker in case `qps % num_workers > 0`; however, this has been changed to the default implementation where we assign the last worker with the extra `qps % num_workers`.

---

## Features

### Basic HTTP API Testing
- Asynchronous HTTP requests using `aiohttp`.
- Customizable duration, number of workers, timeout and QPS.
- Statistical reporting of API Response Time, including percentiles (50th, 90th, 97th, 99th), mean, and standard deviation.
- Error tracking for non-200 HTTP responses.
- If errors are encountered, a set of small descriptions of obtained exception as `errors_status`.
- Returns metrics on API Response Time: means the time taken to return the complete response to the request.
- Returns metrics on Latency: means the time taken to transfer data between the client and the server.

### Testing Fireworks AI Text Completion API
- All the above for `response_time`, `latency` and `Time-to-First-Token`
- If `stream=True`, then check `Time-to-First-Token` in the text completion API. (Made possible since `BOS_TOKEN` returned as first response)
- Configure specific details like:
  - `model`
  - `prompt`
  - `max_tokens`

## Requirements

- Python 3.8+
- Docker

## Installation & Setup
- Installation with Docker
    ```bash
    docker build -t http-project .
    ``` 
  - The above will install `pip` dependencies and run the API on port `80` within the container.
  - To start the container on the image on port `8000` on your device: 
    ```bash
    docker run -p 8000:80 http-project 
    ```

- Local Installation 
  - Install the required libraries using pip:
    ```bash
    python -m pip install -r requirements.txt
    ```
  - Simply use one of  `benchmark.py` or `fireworks_ai_benchmark.py` files:
    ```bash
    python <file_name.py> <args> 
    ```

## Running Unit Tests:
Simply run:
```bash
 python -m unittest test_benchmark.py 
```

## Using the API

- To test on Basic HTTP API, use the following `cURL` command:
  ```bash
    curl --location 'http://localhost:8000/benchmark' \
    --header 'Content-Type: application/json' \
    --data '{
        "url": "https://httpbin.org/get",
        "qps": 20,
        "duration": 5,
        "num_workers": 20,
        "timeout": 0.25
    }'
  ```
  - Use the `dummy_api.py` to test the below by running: `uvicorn dummy_api:app --port 8081 --reload`
    - Sample Response:
      ```JSON
      {
        "config": {
          "url": "https://httpbin.org/get",
          "qps": 20,
          "duration": 5,
          "num_workers": 20,
          "timeout": 0.25
      },
      "total_requests": 100,
      "errors": 10,
      "mean_response_time": 0.09689875602722169,
      "std_response_time": 0.08430709021882068,
      "response_time_p50": 0.03715097904205322,
      "response_time_p90": 0.2193705320358277,
      "response_time_p97": 0.2523853826522827,
      "response_time_p99": 0.25324128866195683,
      "mean_latency": 0.08327518597893092,
      "std_latency": 0.07355851797061785,
      "latency_p50": 0.036652207374572754,
      "latency_p90": 0.21138486862182618,
      "latency_p97": 0.21849927425384522,
      "latency_p99": 0.22762411594390872,
      "errors_status": [
          "",
          "Request not completed"
      ]
      }
      ```
      - To test on Fireworks AI API, use the following `cURL` command:
          - [NOTE] Field `token` needs to be passed to the request which contains API key from [FireworksAI](https://fireworks.ai/api-keys)
          ```bash
          curl --location 'http://localhost:8000/fireworks_benchmark' \
          --header 'Content-Type: application/json' \
          --data '{
              "qps": 10,
              "duration":5,
              "token": "KbtMA1I6TV35O6xjb9zOXRB8vDjI8iNUPFRKq6lESDuOTWJN",
              "model": "accounts/fireworks/models/llama-v3-8b-instruct-hf",
              "max_tokens": 25,
              "prompt": "Snow is white",
              "url": "https://api.fireworks.ai/inference/v1/completions",
              "stream": "True",
              "num_workers": 10,
              "timeout": 1.5
          }'
          ```
          - Sample Response:
            ```JSON
              {
              "config": {
                  "fireworks_payload": {
                      "model": "accounts/fireworks/models/llama-v3-8b-instruct-hf",
                      "prompt": "Snow is white",
                      "max_tokens": 25,
                      "logprobs": 2,
                      "echo": true,
                      "temperature": 1,
                      "top_p": 1,
                      "top_k": 50,
                      "frequency_penalty": 0,
                      "presence_penalty": 0,
                      "n": 1,
                      "stop": "<string>",
                      "stream": true,
                      "context_length_exceeded_behavior": "truncate",
                      "user": "<string>"
                  },
                  "qps": 10,
                  "duration": 5,
                  "url": "https://api.fireworks.ai/inference/v1/completions",
                  "num_workers": 10,
                  "timeout": 1.5
              },
              "total_requests": 50,
              "errors": 17,
              "mean_response_time": 1.256036820411682,
              "std_response_time": 0.24853412813865153,
              "response_time_p50": 1.35898756980896,
              "response_time_p90": 1.5038734197616577,
              "response_time_p97": 1.5060858416557312,
              "response_time_p99": 1.506537208557129,
              "mean_latency": 0.46938368853400736,
              "std_latency": 0.2533548911879965,
              "latency_p50": 0.4923844337463379,
              "latency_p90": 0.8658977508544922,
              "latency_p97": 0.8710399532318115,
              "latency_p99": 0.8713918018341065,
              "mean_time_to_first_token": 0.4694188061882468,
              "std_time_to_first_token": 0.25335066457698385,
              "time_to_first_token_p50": 0.49241387844085693,
              "time_to_first_token_p90": 0.8659332036972046,
              "time_to_first_token_p97": 0.8710464000701904,
              "time_to_first_token_p99": 0.8713988780975341,
              "errors_status": [
                  "",
                  "Request not completed"
              ]
            }