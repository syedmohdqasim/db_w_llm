import unittest
from unittest.mock import MagicMock, patch
from ..adapter import LLMAdapter

class TestLLMAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = LLMAdapter(api_key="mock_key")

    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_translate_to_sql_simple(self, mock_generate):
        # Mock the Gemini response
        mock_response = MagicMock()
        mock_response.text = "SELECT * FROM users;"
        mock_generate.return_value = mock_response

        schema = "CREATE TABLE users (id INTEGER, name TEXT);"
        question = "Show me all users"
        
        sql = self.adapter.translate_to_sql(question, schema)
        
        self.assertEqual(sql, "SELECT * FROM users;")
        mock_generate.assert_called_once()

    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_translate_to_sql_with_markdown(self, mock_generate):
        # Mock a response where Gemini accidentally includes markdown code blocks
        mock_response = MagicMock()
        mock_response.text = "```sql\nSELECT name FROM employees;\n```"
        mock_generate.return_value = mock_response

        sql = self.adapter.translate_to_sql("get names", "schema")
        
        # Verify our cleanup logic handles the markdown
        self.assertEqual(sql, "SELECT name FROM employees;")

if __name__ == "__main__":
    unittest.main()
