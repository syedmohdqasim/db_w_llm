import unittest
import os
import sqlite3
from ..executor import QueryExecutor

class TestQueryExecutor(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_executor.db"
        if os.path.exists(self.test_db): os.remove(self.test_db)
        
        # Create test table
        conn = sqlite3.connect(self.test_db)
        conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob')")
        conn.commit()
        conn.close()
        
        self.executor = QueryExecutor(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db): os.remove(self.test_db)

    def test_execute_query_select(self):
        result = self.executor.execute_query("SELECT * FROM users")
        self.assertEqual(result["columns"], ["id", "name"])
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["data"][0], (1, "Alice"))

    def test_execute_query_invalid(self):
        result = self.executor.execute_query("SELECT * FROM nonexistent")
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()
