from fastapi import FastAPI, HTTPException, Body
import sqlite3
from pydantic import BaseModel

app = FastAPI(
    title="DB Validator Service",
    description="A service to validate SQL queries.",
    version="1.0.0"
)

RESTRICTED_KEYWORDS = ["DROP", "DELETE", "TRUNCATE", "UPDATE"]

class QueryRequest(BaseModel):
    query: str

@app.post("/validate")
async def validate_sql(request: QueryRequest = Body(...)):
    query = request.query.upper()
    
    # Simple security check
    for keyword in RESTRICTED_KEYWORDS:
        if keyword in query:
            raise HTTPException(status_code=403, detail=f"Restricted keyword '{keyword}' found")
    
    # Syntax check using sqlite3 (dry run)
    try:
        conn = sqlite3.connect(":memory:")
        # We don't know the table names, so we can't fully validate SELECTs without mocking.
        # But we can at least check if it's a structural failure.
        if query.startswith("SELECT"):
            if "FROM" not in query:
                raise HTTPException(status_code=400, detail="SELECT query missing FROM clause")
        else:
            conn.execute(f"EXPLAIN {request.query}")
        conn.close()
        return {"valid": True, "message": "Syntax is valid"}
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=f"SQLite syntax error: {str(e)}")

@app.get("/")
def root():
    return {"message": "DB Validator Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)
