# HTTP Load Testing API

This is an HTTP load testing tool built using Python's `asyncio` and `aiohttp` libraries. It allows you to benchmark the performance of a given URL by specifying the queries per second (QPS), number of workers, duration, and timeout.

## Features

### Basic HTTP API Testing
- Asynchronous HTTP requests using `aiohttp`.
- Customizable duration, number of workers, timeout and QPS.
- Statistical reporting of API Response Time, including percentiles (50th, 90th, 97th, 99th), mean, and standard deviation.
- Error tracking for non-200 HTTP responses.
- If errors are encountered, a set of small descriptions of obtained exception as `errors_status`.
- Returns metrics on API Response Time: means the time taken to return the complete response to the request.

### Testing Fireworks AI Text Completion API
- All the above for `response_time` and `Time-to-First-Token`
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

## Running Tests:
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
      "url": "http://localhost:8081",
      "qps": 20,
      "duration": 5,
      "num_workers": 5,
      "timeout": 2
      }'
  ```
- To test on Fireworks AI API, use the following `cURL` command:
    - [NOTE] Field `token` needs to be passed to the request which contains API key from [FireworksAI](https://fireworks.ai/api-keys)
    ```bash
    curl --location 'http://localhost:8000/fireworks_benchmark' \
    --header 'Content-Type: application/json' \
    --data '{
      "qps": 20,
      "duration": 15,
      "token": "<TOKEN>",
      "model": "accounts/fireworks/models/llama-v3-8b-instruct-hf",
      "max_tokens": 25,
      "prompt": "Snow is white",
      "url": "https://api.fireworks.ai/inference/v1/completions",
      "stream": "True",
      "num_workers": 10,
      "timeout": 3
      }'
    ```