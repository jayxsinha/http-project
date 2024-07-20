from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import asyncio

from benchmark import benchmark
from fireworks_ai_benchmark import benchmark as fireworks_benchmark
class LoadTestRequest(BaseModel):
    qps: int
    url: HttpUrl
    duration: int
    num_workers: int
    timeout: int

class FireworksLoadTestRequest(BaseModel):
    token: str
    qps: int
    duration: int
    model: str
    max_tokens: int
    prompt: str
    url: HttpUrl
    stream: bool
    num_workers: int
    timeout: int
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/benchmark")
async def perform_load_test(request: LoadTestRequest):
    if request.qps <= 0 or request.duration <= 0 or request.timeout <=0:
        raise HTTPException(status_code=400, detail="QPS, duration and timeout must be positive integers")
    report = await benchmark(str(request.url), request.qps, request.num_workers, request.duration, request.timeout)
    return report

@app.post("/fireworks_benchmark")
async def perform_fireworks_load_test(request: FireworksLoadTestRequest):
    if request.qps <= 0 or request.duration <= 0:
        raise HTTPException(status_code=400, detail="QPS and duration must be positive integers")

    if len(request.token) == 0:
        raise HTTPException(status_code=400, detail="Please pass an auth token for FireworksAI API request")

    if request.max_tokens == 0:
        raise HTTPException(status_code=400, detail="Max tokens should be > 0")

    if len(request.prompt) == 0:
        raise HTTPException(status_code=400, detail="Please enter a prompt with length > 0")

    report = await fireworks_benchmark(str(request.url), request.model, request.prompt,
                                       request.max_tokens, request.token, request.stream, request.qps, request.duration,
                                       request.num_workers, request.timeout)

    return report