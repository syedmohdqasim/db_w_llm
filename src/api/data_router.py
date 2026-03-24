from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from src.data.csv_loader import CSVLoader

router = APIRouter()
DB_PATH = "project_db.db"

@router.post("/upload", summary="Upload and Load CSV to SQLite", description="Ingests a CSV file, infers its schema, and loads it into a specified SQLite table.")
async def upload_csv(table_name: str, file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Save file temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        loader = CSVLoader(DB_PATH)
        loader.load_csv(temp_path, table_name)
        return {"message": f"Successfully loaded {file.filename} into table {table_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
