import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from fastapi_csv import FastAPI_CSV


class QueryValueTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        csv = Path(self.directory.name) / 'people.csv'
        csv.write_text("name,age\nO'Brien,32\nAlice,18\n", encoding='utf-8')
        self.app = FastAPI_CSV(csv)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.delete_database()
        self.directory.cleanup()

    def test_exact_match_with_apostrophe(self):
        response = self.client.get('/people', params={'name': "O'Brien"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['name'] for row in response.json()], ["O'Brien"])

    def test_contains_with_apostrophe(self):
        response = self.client.get('/people', params={'name_contains': "O'"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['name'] for row in response.json()], ["O'Brien"])

    def test_sql_expression_is_treated_as_a_literal(self):
        response = self.client.get('/people', params={'name': "' OR 1=1 --"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_numeric_comparison_and_combined_filters(self):
        response = self.client.get('/people', params={'age_greaterThan': 20, 'name_contains': 'Brien'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['name'] for row in response.json()], ["O'Brien"])


if __name__ == '__main__':
    unittest.main()
