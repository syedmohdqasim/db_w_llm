import unittest
import os
import sqlite3
import io
from fastapi.testclient import TestClient
from unittest.mock import patch
from ..app import app

class TestDataService(unittest.TestCase):
    def setUp(self):
        self.test_db = "csv_test.db"
        self.patcher = patch('csv_ingestor.app.get_db_path', return_value=self.test_db)
        self.patcher.start()
        self.client = TestClient(app)
        if os.path.exists(self.test_db): os.remove(self.test_db)

    def tearDown(self):
        self.patcher.stop()
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
