import unittest
import os
import sqlite3
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from ..app import app

class TestQueryApp(unittest.TestCase):
    def setUp(self):
        self.test_db = "query_test.db"
        self.patcher = patch('query_service.app.get_db_path', return_value=self.test_db)
        self.patcher.start()
        self.client = TestClient(app)
        if os.path.exists(self.test_db): os.remove(self.test_db)
        
        # Create test data
        conn = sqlite3.connect(self.test_db)
        conn.execute("CREATE TABLE inventory (id INTEGER, item TEXT, qty INTEGER)")
        conn.execute("INSERT INTO inventory VALUES (1, 'Laptop', 10)")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.test_db): os.remove(self.test_db)

    @patch('httpx.AsyncClient.post')
    def test_run_query_success(self, mock_post):
        # 1. Mock the Validator to return success
        mock_val_resp = MagicMock()
        mock_val_resp.status_code = 200
        
        async def mock_coro(*args, **kwargs):
            return mock_val_resp
        mock_post.side_effect = mock_coro

        # 2. Test execution
        response = self.client.post("/query", json={"query": "SELECT item FROM inventory"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0], ["Laptop"])

    @patch('httpx.AsyncClient.post')
    def test_run_query_blocked_by_validator(self, mock_post):
        # 1. Mock the Validator to return forbidden
        mock_val_resp = MagicMock()
        mock_val_resp.status_code = 403
        mock_val_resp.json.return_value = {"detail": "Restricted keyword 'DROP' found"}
        
        async def mock_coro(*args, **kwargs):
            return mock_val_resp
        mock_post.side_effect = mock_coro

        # 2. Test execution
        response = self.client.post("/query", json={"query": "DROP TABLE inventory"})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Security Violation", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
