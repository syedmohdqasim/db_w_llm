import unittest
import os
import sqlite3
import pandas as pd
from src.data.csv_loader import CSVLoader

class TestCSVLoader(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_run.db"
        self.test_csv = "test_data.csv"
        self.loader = CSVLoader(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)

    def create_csv(self, content):
        with open(self.test_csv, "w") as f:
            f.write(content)

    def test_load_csv_success(self):
        self.create_csv("name,age,height\nAlice,30,5.5\nBob,25,6.0")
        self.loader.load_csv(self.test_csv, "users")
        
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        # Verify row count
        cursor.execute("SELECT COUNT(*) FROM users")
        self.assertEqual(cursor.fetchone()[0], 2)
        
        # Verify schema
        cursor.execute("PRAGMA table_info(users)")
        cols = cursor.fetchall()
        self.assertEqual(cols[0][1], "name")
        self.assertEqual(cols[0][2], "TEXT")
        self.assertEqual(cols[1][1], "age")
        self.assertEqual(cols[1][2], "INTEGER")
        self.assertEqual(cols[2][1], "height")
        self.assertEqual(cols[2][2], "REAL")
        
        conn.close()

    def test_load_csv_empty_file(self):
        self.create_csv("id,data\n")
        self.loader.load_csv(self.test_csv, "empty_table")
        
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM empty_table")
        self.assertEqual(cursor.fetchone()[0], 0)
        conn.close()

if __name__ == "__main__":
    unittest.main()
