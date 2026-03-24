import unittest
import os
import sqlite3
from fastapi.testclient import TestClient
from src.main import app

class TestDataAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_db = "project_db.db"
        self.test_csv = "api_test.csv"
        # Ensure DB is clean
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)

    def test_upload_csv_endpoint(self):
        # Create dummy CSV
        with open(self.test_csv, "w") as f:
            f.write("id,name,score\n1,Alice,95.5\n2,Bob,88.0")

        # Test POST /data/upload
        with open(self.test_csv, "rb") as f:
            response = self.client.post(
                "/data/upload?table_name=students",
                files={"file": (self.test_csv, f, "text/csv")}
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully loaded", response.json()["message"])

        # Verify side effect in DB
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, score FROM students WHERE id=1")
        row = cursor.fetchone()
        self.assertEqual(row[0], "Alice")
        self.assertEqual(row[1], 95.5)
        conn.close()

    def test_upload_non_csv_fails(self):
        response = self.client.post(
            "/data/upload?table_name=fail",
            files={"file": ("test.txt", b"not a csv", "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Only CSV files are allowed")

if __name__ == "__main__":
    unittest.main()
