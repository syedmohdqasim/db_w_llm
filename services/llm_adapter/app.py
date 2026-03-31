from fastapi import FastAPI, HTTPException, Body
import os
import httpx
from pydantic import BaseModel
from dotenv import load_dotenv
try:
    from .adapter import LLMAdapter
except (ImportError, ValueError):
    from adapter import LLMAdapter

# Load environment variables from .env if present
load_dotenv()

app = FastAPI(
    title="LLM Adapter Service",
    description="A service to translate natural language to SQL using Gemini.",
    version="1.0.0"
)

SCHEMA_SERVICE_URL = "http://localhost:5003/schema"

class TranslationRequest(BaseModel):
    question: str

def get_adapter(api_key: str):
    return LLMAdapter(api_key)

@app.post("/translate", summary="Translate NL to SQL", description="Converts a natural language question into a SQL query based on the current database schema.")
async def translate(request: TranslationRequest = Body(...)):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server")
    
    # 1. Get schema from Schema Manager
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(SCHEMA_SERVICE_URL)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Could not retrieve schema from Schema Manager")
            schema = response.json().get("schema", "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Schema Manager: {str(e)}")

    if not schema:
        raise HTTPException(status_code=400, detail="Database schema is empty. Please ingest some data first.")

    # 2. Translate using LLM
    try:
        adapter = get_adapter(api_key)
        sql = adapter.translate_to_sql(request.question, schema)
        return {"question": request.question, "sql": sql}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM translation error: {str(e)}")

@app.get("/")
def root():
    return {"message": "LLM Adapter Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5005)
