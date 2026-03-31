import sqlite3

class QueryExecutor:
    def __init__(self, db_path):
        self.db_path = db_path

    def execute_query(self, query):
        """Executes a SQL query and returns the column names and result rows."""
        conn = sqlite3.connect(self.db_path)
        # Use Row factory to get dictionary-like access if needed, 
        # but for a generic service, returning columns + tuples is often cleaner.
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            
            # Fetch column names from cursor description
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Fetch all results
            results = cursor.fetchall()
            
            # Commit if it's a modifying query (though validator should ideally block these for this service)
            conn.commit()
            
            return {
                "columns": columns,
                "data": results,
                "row_count": len(results)
            }
        except sqlite3.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()

if __name__ == "__main__":
    # Quick test
    import os
    db = "test_query.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO test VALUES (1, 'Alice'), (2, 'Bob')")
    conn.commit()
    conn.close()
    
    executor = QueryExecutor(db)
    print("Select All:", executor.execute_query("SELECT * FROM test"))
    
    if os.path.exists(db): os.remove(db)
