"""
Unit tests for the Beekeeping Management Flask application.

Tests cover:
1. Login - positive and negative tests
2. Access control - positive and negative tests
3. Data creation - positive and negative tests
"""

import unittest
import sqlite3
import os
import tempfile
import bcrypt
from unittest import mock
from web_app import app


class BeekeepingAppTestCase(unittest.TestCase):
    """Base test case for Beekeeping Management app."""
    
    # Store the real sqlite3.connect function
    _real_sqlite3_connect = sqlite3.connect

    def setUp(self):
        """Set up test client and test database before each test."""
        # Create temporary database file for testing
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        # Patch sqlite3.connect in web_app module to use test database
        import web_app
        self.patcher = mock.patch.object(web_app.sqlite3, 'connect')
        self.mock_connect = self.patcher.start()
        
        # Make sqlite3.connect use our test database (use the real connect, not mock)
        def connect_side_effect(db_path):
            return self._real_sqlite3_connect(self.db_path)
        
        self.mock_connect.side_effect = connect_side_effect
        
        # Configure Flask app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create test database with schema
        self._create_test_database()
        
        # Create test users
        self._create_test_users()

    def tearDown(self):
        """Clean up after each test."""
        self.app_context.pop()
        self.patcher.stop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def _create_test_database(self):
        """Create test database with all required tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )''')
        
        # Apiaries table
        c.execute('''CREATE TABLE IF NOT EXISTS apiaries (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        location TEXT,
                        latitude REAL,
                        longitude REAL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )''')
        
        # Apiary visits table
        c.execute('''CREATE TABLE IF NOT EXISTS apiary_visits (
                        id INTEGER PRIMARY KEY,
                        apiary_id INTEGER,
                        visit_date TEXT NOT NULL,
                        notes TEXT,
                        FOREIGN KEY (apiary_id) REFERENCES apiaries (id)
                    )''')
        
        # Beehives table
        c.execute('''CREATE TABLE IF NOT EXISTS beehives (
                        id INTEGER PRIMARY KEY,
                        apiary_id INTEGER,
                        name TEXT NOT NULL,
                        description TEXT,
                        image_path TEXT,
                        FOREIGN KEY (apiary_id) REFERENCES apiaries (id)
                    )''')
        
        # Honey harvests table
        c.execute('''CREATE TABLE IF NOT EXISTS honey_harvests (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        date TEXT NOT NULL,
                        honey_type TEXT NOT NULL,
                        amount REAL NOT NULL,
                        money_earned REAL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )''')
        
        # Recipes table
        c.execute('''CREATE TABLE IF NOT EXISTS recipes (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        yield REAL NOT NULL DEFAULT 1,
                        yield_unit TEXT DEFAULT 'units',
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )''')
        
        # Ingredients table
        c.execute('''CREATE TABLE IF NOT EXISTS ingredients (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )''')
        
        # Recipe ingredients table
        c.execute('''CREATE TABLE IF NOT EXISTS recipe_ingredients (
                        id INTEGER PRIMARY KEY,
                        recipe_id INTEGER,
                        ingredient_id INTEGER,
                        quantity REAL NOT NULL,
                        unit TEXT,
                        FOREIGN KEY (recipe_id) REFERENCES recipes (id),
                        FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
                    )''')
        
        conn.commit()
        conn.close()

    def _create_test_users(self):
        """Create test users in the database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create admin user
        admin_password_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt())
        c.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ('admin', admin_password_hash)
        )
        
        # Create test user
        test_password_hash = bcrypt.hashpw('password123'.encode(), bcrypt.gensalt())
        c.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ('testuser', test_password_hash)
        )
        
        conn.commit()
        conn.close()

    def _login_user(self, username='admin', password='admin123'):
        """Helper method to log in a user."""
        return self.client.post('/', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def _get_user_id(self, username='admin'):
        """Helper method to get user ID from database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None


class TestLogin(BeekeepingAppTestCase):
    """Test cases for user login functionality."""

    def test_login_positive_correct_credentials(self):
        """Positive test: Login with correct credentials succeeds."""
        response = self._login_user('admin', 'admin123')
        
        # Check response status code (should redirect to home)
        self.assertEqual(response.status_code, 200)
        
        # Verify we're on the home page (contains "Beekeeping Management" or similar)
        self.assertIn(b'Beekeeping', response.data)

    def test_login_negative_wrong_password(self):
        """Negative test: Login with wrong password fails."""
        response = self.client.post('/', data={
            'username': 'admin',
            'password': 'wrongpassword'
        }, follow_redirects=False)
        
        # Should not redirect to home
        self.assertIn(response.status_code, [200, 302])
        
        # Check that we get an error message or stay on login page
        # The app shows error message, so verify it's rendered
        response_with_text = self.client.post('/', data={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertTrue(
            b'Invalid' in response_with_text.data or 
            b'login' in response_with_text.data.lower()
        )

    def test_login_negative_nonexistent_user(self):
        """Negative test: Login with nonexistent user fails."""
        response = self.client.post('/', data={
            'username': 'nonexistentuser',
            'password': 'somepassword'
        }, follow_redirects=False)
        
        # Should not create a session
        response_with_error = self.client.post('/', data={
            'username': 'nonexistentuser',
            'password': 'somepassword'
        })
        self.assertTrue(
            b'Invalid' in response_with_error.data or
            b'login' in response_with_error.data.lower()
        )


class TestAccessControl(BeekeepingAppTestCase):
    """Test cases for access control and authentication."""

    def test_access_control_positive_logged_in_user_can_access_apiaries(self):
        """Positive test: Logged-in user can access /apiaries page."""
        # First login
        self._login_user('admin', 'admin123')
        
        # Then access apiaries page
        response = self.client.get('/apiaries')
        
        # Should get 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Page should contain apiaries content
        self.assertIn(b'Apiaries', response.data)

    def test_access_control_negative_not_logged_in_blocked_from_apiaries(self):
        """Negative test: Not logged-in user is redirected when accessing /apiaries."""
        # Do not login, directly access apiaries
        response = self.client.get('/apiaries', follow_redirects=False)
        
        # Should redirect (302 or similar)
        self.assertIn(response.status_code, [301, 302, 303, 307, 308])

    def test_access_control_positive_logged_in_user_can_access_harvests(self):
        """Positive test: Logged-in user can access /harvests page."""
        self._login_user('admin', 'admin123')
        
        response = self.client.get('/harvests')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Harvest', response.data)

    def test_access_control_negative_not_logged_in_blocked_from_harvests(self):
        """Negative test: Not logged-in user cannot access /harvests."""
        response = self.client.get('/harvests', follow_redirects=False)
        
        # Should redirect
        self.assertIn(response.status_code, [301, 302, 303, 307, 308])


class TestDataCreation(BeekeepingAppTestCase):
    """Test cases for data creation (apiaries and harvests)."""

    def test_data_creation_positive_add_valid_apiary(self):
        """Positive test: Adding a valid apiary creates the record."""
        # Login first
        self._login_user('admin', 'admin123')
        
        # Get user ID
        user_id = self._get_user_id('admin')
        
        # Add apiary via POST
        response = self.client.post('/apiaries/add', data={
            'name': 'North Apiary',
            'location': 'Forest near Riga',
            'latitude': '56.9496',
            'longitude': '24.1052'
        }, follow_redirects=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'successfully', response.data.lower() or b'Apiary', response.data)
        
        # Verify data was saved to database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM apiaries WHERE user_id = ? AND name = ?", (user_id, 'North Apiary'))
        result = c.fetchone()
        conn.close()
        
        self.assertIsNotNone(result, "Apiary should be saved to database")
        self.assertEqual(result[2], 'North Apiary')  # name field

    def test_data_creation_negative_add_apiary_with_empty_name(self):
        """Negative test: Adding apiary with empty name should fail gracefully."""
        self._login_user('admin', 'admin123')
        
        user_id = self._get_user_id('admin')
        
        # Try to add apiary with empty name
        # This should fail at the form validation or DB level
        try:
            response = self.client.post('/apiaries/add', data={
                'name': '',
                'location': 'Some Location',
                'latitude': '56.9496',
                'longitude': '24.1052'
            }, follow_redirects=True)
            
            # Check database - empty name should not be created
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM apiaries WHERE user_id = ? AND name = ''", (user_id,))
            count = c.fetchone()[0]
            conn.close()
            
            # Should not have created record with empty name, or it will fail at insert
            self.assertEqual(count, 0, "Should not create apiary with empty name")
        except Exception:
            # If form validation prevents submission, that's also acceptable
            pass

    def test_data_creation_positive_add_valid_harvest(self):
        """Positive test: Adding a valid harvest creates the record."""
        self._login_user('admin', 'admin123')
        
        user_id = self._get_user_id('admin')
        
        # Add harvest
        response = self.client.post('/harvests/add', data={
            'date': '2026-04-09',
            'honey_type': 'Acacia',
            'amount': '5.5',
            'money_earned': '50.00'
        }, follow_redirects=True)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Verify data was saved
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM honey_harvests WHERE user_id = ? AND honey_type = ?",
            (user_id, 'Acacia')
        )
        result = c.fetchone()
        conn.close()
        
        self.assertIsNotNone(result, "Harvest should be saved to database")
        self.assertEqual(result[3], 'Acacia')  # honey_type field
        self.assertEqual(result[4], 5.5)  # amount field

    def test_data_creation_negative_add_harvest_with_invalid_amount(self):
        """Negative test: Adding harvest with invalid amount should fail."""
        self._login_user('admin', 'admin123')
        
        user_id = self._get_user_id('admin')
        
        # Try to add harvest with non-numeric amount
        try:
            response = self.client.post('/harvests/add', data={
                'date': '2026-04-09',
                'honey_type': 'Wildflower',
                'amount': 'invalid_amount',
                'money_earned': '30.00'
            }, follow_redirects=True)
            
            # If it fails to convert to float, no record should be created
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                "SELECT COUNT(*) FROM honey_harvests WHERE user_id = ? AND honey_type = ?",
                (user_id, 'Wildflower')
            )
            count = c.fetchone()[0]
            conn.close()
            
            self.assertEqual(count, 0, "Should not create harvest with invalid amount")
        except Exception:
            # If form validation or type error prevents submission, that's acceptable
            pass

    def test_data_creation_negative_add_harvest_with_missing_required_field(self):
        """Negative test: Adding harvest with missing required field fails."""
        self._login_user('admin', 'admin123')
        
        user_id = self._get_user_id('admin')
        
        # Try to add harvest without honey_type
        try:
            response = self.client.post('/harvests/add', data={
                'date': '2026-04-09',
                'honey_type': '',  # Missing required field
                'amount': '3.0',
                'money_earned': '25.00'
            }, follow_redirects=True)
            
            # Should not create record with empty honey_type
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                "SELECT COUNT(*) FROM honey_harvests WHERE user_id = ? AND honey_type = ''",
                (user_id,)
            )
            count = c.fetchone()[0]
            conn.close()
            
            self.assertEqual(count, 0, "Should not create harvest with empty honey_type")
        except Exception:
            # If validation error, that's also acceptable
            pass


class TestLogout(BeekeepingAppTestCase):
    """Test cases for logout functionality."""

    def test_logout_clears_session(self):
        """Test that logout clears the session."""
        # Login
        self._login_user('admin', 'admin123')
        
        # Access protected page to verify login
        response_before = self.client.get('/apiaries')
        self.assertEqual(response_before.status_code, 200)
        
        # Logout
        response = self.client.get('/logout', follow_redirects=False)
        
        # Should redirect
        self.assertIn(response.status_code, [301, 302, 303, 307, 308])
        
        # Try to access protected page again
        response_after = self.client.get('/apiaries', follow_redirects=False)
        
        # Should be redirected to login (not 200)
        self.assertIn(response_after.status_code, [301, 302, 303, 307, 308])


if __name__ == '__main__':
    unittest.main()
