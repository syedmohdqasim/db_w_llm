from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
try:
    from .csv_loader import CSVLoader
except (ImportError, ValueError):
    from csv_loader import CSVLoader

app = FastAPI(
    title="CSV Ingestor Service",
    description="A service to upload CSV files and load them into SQLite.",
    version="1.0.0"
)

def get_db_path():
    return os.getenv("DB_PATH", "project_db.db")

@app.post("/upload", summary="Upload and Load CSV to SQLite", description="Ingests a CSV file, infers its schema, and loads it into a specified SQLite table.")
async def upload_csv(table_name: str, file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Save file temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        loader = CSVLoader(get_db_path())
        loader.load_csv(temp_path, table_name)
        return {"message": f"Successfully loaded {file.filename} into table {table_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/")
def root():
    return {"message": "CSV Ingestor Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
