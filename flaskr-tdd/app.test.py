import os
import unittest

from app import app

class BasicTestCase(unittest.TestCase):

    def test_index(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 404)

    def test_database(self):
        databaseExist = os.path.exists('flaskr.db')
        self.assertTrue(databaseExist)

if __name__ == '__main__':
    unittest.main()