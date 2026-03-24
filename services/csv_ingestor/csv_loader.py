import pandas as pd
import sqlite3
import os

class CSVLoader:
    def __init__(self, db_path):
        self.db_path = db_path

    def load_csv(self, csv_path, table_name):
        # Read CSV using pandas
        df = pd.read_csv(csv_path)
        
        # Inspect data and infer schema
        columns = []
        for col_name, dtype in df.dtypes.items():
            if "int" in str(dtype):
                sql_type = "INTEGER"
            elif "float" in str(dtype):
                sql_type = "REAL"
            else:
                sql_type = "TEXT"
            columns.append(f'"{col_name}" {sql_type}')
        
        schema = ", ".join(columns)
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        
        # Insert logic
        placeholders = ", ".join(["?"] * len(df.columns))
        insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
        
        # Connect and execute
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(create_table_sql)
            # Convert dataframe to list of tuples for insertion
            data = [tuple(x) for x in df.values]
            cursor.executemany(insert_sql, data)
            conn.commit()
            print(f"Successfully loaded {len(data)} rows into {table_name}")
        except Exception as e:
            conn.rollback()
            print(f"Error loading CSV: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    # Quick test if run directly
    test_csv = "test.csv"
    with open(test_csv, "w") as f:
        f.write("id,name,age\n1,Alice,30\n2,Bob,25")
    
    loader = CSVLoader("test.db")
    loader.load_csv(test_csv, "users")
    
    # Cleanup
    if os.path.exists(test_csv): os.remove(test_csv)
    # if os.path.exists("test.db"): os.remove("test.db")
