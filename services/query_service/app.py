from fastapi import FastAPI, HTTPException, Body
import os
from pydantic import BaseModel
try:
    from .executor import QueryExecutor
except (ImportError, ValueError):
    from executor import QueryExecutor

app = FastAPI(
    title="Query Service",
    description="A service to execute SQL queries against the project database.",
    version="1.0.0"
)

DB_PATH = "project_db.db"

class QueryRequest(BaseModel):
    query: str

@app.post("/query", summary="Execute SQL Query", description="Executes a provided SQL query and returns the resulting dataset.")
async def run_query(request: QueryRequest = Body(...)):
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Database file not found. Have you ingested any data yet?")
    
    executor = QueryExecutor(DB_PATH)
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
