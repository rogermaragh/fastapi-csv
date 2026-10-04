import csv
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from fastapi_csv import FastAPI_CSV


class QueryParameterTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        path = Path(self.directory.name) / 'people.csv'
        with path.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['name', 'age'])
            writer.writerows([["O'Brien", 30], ['Alice', 18], ['Bob', 40]])
        self.app = FastAPI_CSV(path)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.delete_database()
        self.directory.cleanup()

    def names(self, **params):
        response = self.client.get('/people', params=params)
        self.assertEqual(response.status_code, 200)
        return [row['name'] for row in response.json()]

    def test_apostrophe_in_exact_filter(self):
        self.assertEqual(self.names(name="O'Brien"), ["O'Brien"])

    def test_apostrophe_in_substring_filter(self):
        self.assertEqual(self.names(name_contains="'"), ["O'Brien"])

    def test_sql_syntax_is_literal_in_exact_filter(self):
        self.assertEqual(self.names(name="' OR 1=1 --"), [])

    def test_sql_syntax_is_literal_in_substring_filter(self):
        self.assertEqual(self.names(name_contains="') OR 1=1 --"), [])

    def test_numeric_comparisons_and_combined_filters(self):
        self.assertEqual(self.names(age_greaterThan=30), ['Bob'])
        self.assertEqual(self.names(age_greaterThanEqual=30), ["O'Brien", 'Bob'])
        self.assertEqual(self.names(age_lessThan=30), ['Alice'])
        self.assertEqual(self.names(age_lessThanEqual=30), ["O'Brien", 'Alice'])
        self.assertEqual(self.names(name_contains='B', age_lessThan=40), ["O'Brien"])

    def test_unfiltered_query_and_existing_query_database_call(self):
        self.assertEqual(self.names(), ["O'Brien", 'Alice', 'Bob'])
        self.assertEqual(self.app.query_database('SELECT name FROM people WHERE age=18'),
                         [{'name': 'Alice'}])


if __name__ == '__main__':
    unittest.main()
