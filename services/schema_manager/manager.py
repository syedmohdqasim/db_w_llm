import sqlite3

class SchemaManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_tables(self):
        """Returns a list of all table names in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            return tables
        finally:
            conn.close()

    def get_table_schema(self, table_name):
        """Returns the CREATE TABLE statement for a specific table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        finally:
            conn.close()

    def get_full_schema(self):
        """Returns a combined string of all table schemas, useful for LLM context."""
        tables = self.get_tables()
        schemas = []
        for table in tables:
            schema = self.get_table_schema(table)
            if schema:
                schemas.append(schema)
        return "\n\n".join(schemas)

if __name__ == "__main__":
    # Quick test
    import os
    db = "test_schema.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    conn.execute("CREATE TABLE orders (id INTEGER, user_id INTEGER, amount REAL)")
    conn.close()
    
    manager = SchemaManager(db)
    print("Tables:", manager.get_tables())
    print("Full Schema:\n", manager.get_full_schema())
    
    if os.path.exists(db): os.remove(db)
