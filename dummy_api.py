from fastapi import FastAPI, HTTPException
import random
random.seed(42)
app = FastAPI()

@app.get("/")
async def root():
    if random.choice([True, False]):
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return {"message": "Hello, World!"}