import unittest
from flask import session
from app import app, init_db, get_db_connection
import os
import sqlite3

class FlaskAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the testing environment and database."""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['DATABASE'] = 'test_database.db'

        # Create a test database
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()
        conn.close()

    def setUp(self):
        """Set up the test client and prepopulate test data."""
        self.client = app.test_client()
        self.db_path = app.config['DATABASE']

        # Prepopulate the database with a test user
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                ('testuser', 'hashedpassword')  # Use a pre-hashed password
            )
            conn.commit()

    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_registration(self):
        """Test user registration."""
        response = self.client.post('/register', data={
            'username': 'newuser',
            'password': 'newpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Account created successfully!', response.data)

    def test_login_successful(self):
        """Test successful login."""
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'hashedpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)

    def test_login_failed(self):
        """Test login with invalid credentials."""
        response = self.client.post('/login', data={
            'username': 'wronguser',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_dashboard_requires_login(self):
        """Test that the dashboard is inaccessible without login."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_access(self):
        """Test dashboard access after login."""
        with self.client.session_transaction() as session:
            session['user_id'] = 1  # Mock logged-in user

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Notes', response.data)

    def test_add_note(self):
        """Test adding a note."""
        with self.client.session_transaction() as session:
            session['user_id'] = 1  # Mock logged-in user

        response = self.client.post('/add_note', data={
            'task': 'Test Task'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Verify note added to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE task = ?", ('Test Task',))
        note = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(note)

    def test_logout(self):
        """Test user logout."""
        with self.client.session_transaction() as session:
            session['user_id'] = 1  # Mock logged-in user

        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('user_id', session)

    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.client.get('/_status/healthz')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "healthy"})


if __name__ == '__main__':
    unittest.main()
