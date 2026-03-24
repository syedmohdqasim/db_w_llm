import unittest
from fastapi.testclient import TestClient
from ..app import app

class TestValidatorService(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_validate_success(self):
        response = self.client.post('/validate', json={'query': 'SELECT * FROM users'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['valid'])

    def test_validate_restricted(self):
        response = self.client.post('/validate', json={'query': 'DROP TABLE users'})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Restricted keyword 'DROP' found", response.json()['detail'])

    def test_validate_syntax_error(self):
        # Invalid syntax
        response = self.client.post('/validate', json={'query': 'SELECT FROM'})
        self.assertEqual(response.status_code, 400)
        self.assertIn("SELECT query missing FROM clause", response.json()['detail'])

if __name__ == '__main__':
    unittest.main()
