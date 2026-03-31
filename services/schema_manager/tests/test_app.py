import unittest
import os
import sqlite3
from fastapi.testclient import TestClient
from ..app import app

class TestSchemaApp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_db = "project_db.db"
        if os.path.exists(self.test_db): os.remove(self.test_db)
        
        # Create test data
        conn = sqlite3.connect(self.test_db)
        conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
        conn.close()

    def tearDown(self):
        if os.path.exists(self.test_db): os.remove(self.test_db)

    def test_list_tables(self):
        response = self.client.get("/tables")
        self.assertEqual(response.status_code, 200)
        self.assertIn("users", response.json()["tables"])

    def test_get_schema_success(self):
        response = self.client.get("/schema/users")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["table"], "users")
        self.assertIn("CREATE TABLE users", response.json()["schema"])

    def test_get_schema_not_found(self):
        response = self.client.get("/schema/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_get_full_schema(self):
        response = self.client.get("/schema")
        self.assertEqual(response.status_code, 200)
        self.assertIn("CREATE TABLE users", response.json()["schema"])

if __name__ == "__main__":
    unittest.main()
