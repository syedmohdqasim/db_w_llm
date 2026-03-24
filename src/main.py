from fastapi import FastAPI
from src.api.data_router import router as data_router

app = FastAPI(title="DB with LLM API")

# Register routers
app.include_router(data_router, prefix="/data", tags=["Data"])

@app.get("/")
def root():
    return {"message": "DB with LLM API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
