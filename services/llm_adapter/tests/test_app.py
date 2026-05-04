import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import os
import services.llm_adapter.app as llm_app

class TestLLMApp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(llm_app.app)
        self.env_patcher = patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch('httpx.AsyncClient.get')
    @patch('services.llm_adapter.app.get_adapter')
    def test_translate_endpoint_success(self, mock_get_adapter, mock_get):
        # 1. Mock Schema Manager response
        mock_schema_resp = MagicMock()
        mock_schema_resp.status_code = 200
        mock_schema_resp.json.return_value = {"schema": "CREATE TABLE test (id INT);"}
        
        async def mock_coro(*args, **kwargs):
            return mock_schema_resp
        mock_get.side_effect = mock_coro

        # 2. Mock LLM translation via the instance
        mock_adapter_instance = MagicMock()
        mock_adapter_instance.translate_to_sql.return_value = "SELECT * FROM test;"
        mock_get_adapter.return_value = mock_adapter_instance

        response = self.client.post("/translate", json={"question": "show test"})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sql"], "SELECT * FROM test;")

    @patch('httpx.AsyncClient.get')
    def test_translate_endpoint_no_schema(self, mock_get):
        # Mock Schema Manager returning empty schema
        mock_schema_resp = MagicMock()
        mock_schema_resp.status_code = 200
        mock_schema_resp.json.return_value = {"schema": ""}
        
        async def mock_coro(*args, **kwargs):
            return mock_schema_resp
        mock_get.side_effect = mock_coro

        response = self.client.post("/translate", json={"question": "show test"})
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("schema is empty", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
