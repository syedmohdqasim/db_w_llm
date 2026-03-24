from fastapi import FastAPI
from src.api.data_router import router as data_router

app = FastAPI(
    title="DB with LLM API",
    description="A modular REST API for natural language database querying and management.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register routers
app.include_router(data_router, prefix="/data", tags=["Data"])

@app.get("/")
def root():
    return {"message": "DB with LLM API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
