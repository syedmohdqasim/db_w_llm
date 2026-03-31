import unittest
import os
import sqlite3
from ..manager import SchemaManager

class TestSchemaManager(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_manager.db"
        if os.path.exists(self.test_db): os.remove(self.test_db)
        
        # Create test tables
        conn = sqlite3.connect(self.test_db)
        conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
        conn.execute("CREATE TABLE posts (id INTEGER, content TEXT, user_id INTEGER)")
        conn.close()
        
        self.manager = SchemaManager(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db): os.remove(self.test_db)

    def test_get_tables(self):
        tables = self.manager.get_tables()
        self.assertIn("users", tables)
        self.assertIn("posts", tables)
        self.assertEqual(len(tables), 2)

    def test_get_table_schema(self):
        schema = self.manager.get_table_schema("users")
        self.assertIn("CREATE TABLE users", schema)
        self.assertIn("id INTEGER", schema)
        self.assertIn("name TEXT", schema)

    def test_get_full_schema(self):
        full_schema = self.manager.get_full_schema()
        self.assertIn("CREATE TABLE users", full_schema)
        self.assertIn("CREATE TABLE posts", full_schema)

if __name__ == "__main__":
    unittest.main()
