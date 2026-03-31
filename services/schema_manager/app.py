from fastapi import FastAPI, HTTPException
import os
try:
    from .manager import SchemaManager
except (ImportError, ValueError):
    from manager import SchemaManager

app = FastAPI(
    title="Schema Manager Service",
    description="A service to extract database schema information for LLM use.",
    version="1.0.0"
)

DB_PATH = "project_db.db"

@app.get("/tables", summary="List All Tables", description="Returns a list of all tables currently in the database.")
def list_tables():
    if not os.path.exists(DB_PATH):
        return {"tables": []}
    
    manager = SchemaManager(DB_PATH)
    return {"tables": manager.get_tables()}

@app.get("/schema/{table_name}", summary="Get Table Schema", description="Returns the SQL CREATE statement for a specific table.")
def get_table_schema(table_name: str):
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Database file not found")
    
    manager = SchemaManager(DB_PATH)
    schema = manager.get_table_schema(table_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    
    return {"table": table_name, "schema": schema}

@app.get("/schema", summary="Get Full Database Schema", description="Returns all table schemas as a single string, formatted for LLM ingestion.")
def get_full_schema():
    if not os.path.exists(DB_PATH):
        return {"schema": ""}
    
    manager = SchemaManager(DB_PATH)
    return {"schema": manager.get_full_schema()}

@app.get("/")
def root():
    return {"message": "Schema Manager Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
