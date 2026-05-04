from fastapi import FastAPI, HTTPException, Body
import os
import httpx
from pydantic import BaseModel
try:
    from .executor import QueryExecutor
except (ImportError, ValueError):
    from executor import QueryExecutor

app = FastAPI(
    title="Query Service",
    description="A service to execute SQL queries against the project database.",
    version="1.1.0"
)

def get_db_path():
    return os.getenv("DB_PATH", "project_db.db")

VALIDATOR_URL = "http://localhost:5002/validate"

class QueryRequest(BaseModel):
    query: str

@app.post("/query", summary="Execute SQL Query", description="Executes a provided SQL query and returns the resulting dataset. Automatically validates query safety first.")
async def run_query(request: QueryRequest = Body(...)):
    # 1. Check if database exists
    if not os.path.exists(get_db_path()):
        raise HTTPException(status_code=404, detail="Database file not found. Have you ingested any data yet?")
    
    # 2. Call Validator Service
    try:
        async with httpx.AsyncClient() as client:
            val_resp = await client.post(VALIDATOR_URL, json={"query": request.query})
            if val_resp.status_code == 403:
                raise HTTPException(status_code=403, detail=f"Security Violation: {val_resp.json().get('detail')}")
            if val_resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Validation Error: {val_resp.json().get('detail')}")
    except httpx.RequestError as e:
        # If validator is down, we fail-safe (don't run the query)
        raise HTTPException(status_code=503, detail=f"Validator service unavailable: {str(e)}")

    # 3. Execute Query
    executor = QueryExecutor(get_db_path())
    result = executor.execute_query(request.query)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=f"SQLite error: {result['error']}")
    
    return result

@app.get("/")
def root():
    return {"message": "Query Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5004)
