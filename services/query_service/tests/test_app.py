import unittest
import os
import sqlite3
from fastapi.testclient import TestClient
from ..app import app

class TestQueryApp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_db = "project_db.db"
        if os.path.exists(self.test_db): os.remove(self.test_db)
        
        # Create test data
        conn = sqlite3.connect(self.test_db)
        conn.execute("CREATE TABLE inventory (id INTEGER, item TEXT, qty INTEGER)")
        conn.execute("INSERT INTO inventory VALUES (1, 'Laptop', 10), (2, 'Mouse', 50)")
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.test_db): os.remove(self.test_db)

    def test_run_query_success(self):
        response = self.client.post("/query", json={"query": "SELECT item, qty FROM inventory WHERE qty > 20"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["columns"], ["item", "qty"])
        self.assertEqual(data["data"][0], ["Mouse", 50])

    def test_run_query_not_found(self):
        if os.path.exists(self.test_db): os.remove(self.test_db)
        response = self.client.post("/query", json={"query": "SELECT * FROM inventory"})
        self.assertEqual(response.status_code, 404)

    def test_run_query_invalid_sql(self):
        response = self.client.post("/query", json={"query": "SELECT FROM inventory"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("SQLite error", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
