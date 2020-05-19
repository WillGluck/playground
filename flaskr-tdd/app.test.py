import os
import unittest
import tempfile
import json

import app

class BasicTestCase(unittest.TestCase):

    def test_index(self):
        """ Initial test: Ensure flask was set up correctly."""
        tester = app.app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    def test_database(self):
        """Initial test: Ensure that the database exists."""
        databaseExist = os.path.exists('flaskr.db')
        self.assertTrue(databaseExist)

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        """Set up a blank temp database before each test."""
        self.db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
        app.init_db()

    def tearDown(self):
        """Destroy blank temp database after each test."""
        os.close(self.db_fd)
        os.unlink(app.app.config['DATABASE'])

    def login(self, username, password):
        """Login helper function."""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        """Logou helper function."""
        return self.client.post('/logout', follow_redirects=True)
    
    def test_empty_db(self):
        """Ensure database is blank."""
        response = self.client.get('/')
        assert b'No entries yet. Add some!' in response.data

    def test_login_logout(self):
        """Test login and logout using helper functions."""
        response = self.login(
            app.app.config['USERNAME'],
            app.app.config['PASSWORD']
        )
        assert b'You were logged in'in response.data
        response = self.logout()
        assert b'You were logged out' in response.data
        response = self.login(
            app.app.config['USERNAME'] + 'x',
            app.app.config['PASSWORD']
        )
        assert b'Invalid username' in response.data
        response = self.login(
            app.app.config['USERNAME'],
            app.app.config['PASSWORD'] + 'x'
        )
        assert b'Invalid password' in response.data

    def test_messages(self):
        """Ensure that a user can post messages."""
        self.login(
            app.app.config['USERNAME'],
            app.app.config['PASSWORD']
        )
        response = self.client.post('/add', data=dict(
            title='<Hello>',
            text='<strong>HTML</string> allowed here'
        ), follow_redirects=True)
        assert b'No entries yet. Add some!' not in response.data
        self.assertIn(b'&lt;Hello&gt;', response.data)
        assert b'<strong>HTML</string> allowed here' in response.data

    def test_delete_message(self):
        """Ensure the messages are being deleted"""
        rv = self.client.get('/delete/1')
        data = json.loads((rv.data).decode('utf-8'))
        self.assertEquals(data['status'], 1)
        
if __name__ == '__main__':
    unittest.main()