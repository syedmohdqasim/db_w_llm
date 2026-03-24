import unittest
import os
import sqlite3
import io
from fastapi.testclient import TestClient
from ..app import app

class TestDataService(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_db = "project_db.db"
        if os.path.exists(self.test_db): os.remove(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db): os.remove(self.test_db)

    def test_upload_success(self):
        data = {
            'file': ('test.csv', io.BytesIO(b"id,val\n1,test\n2,hello"), 'text/csv'),
        }
        response = self.client.post('/upload?table_name=test_table', files=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully loaded", response.json()['message'])
        
        # Verify DB
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT val FROM test_table WHERE id=1")
        self.assertEqual(cursor.fetchone()[0], "test")
        conn.close()

if __name__ == '__main__':
    unittest.main()
