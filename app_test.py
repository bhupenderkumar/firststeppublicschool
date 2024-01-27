import unittest
from flask import Flask, session
from app import app  # Replace 'your_app' with the actual name of your Flask app
from pymongo import MongoClient
 

class YourAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.mongo = MongoClient("localhost:27017")  # Adjust this line based on how you initialize your database
        self.mongo.db.drop_database('test_db')  # Reset the test database

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to Your App', response.data)

    def test_login(self):
        response = self.app.post('/login', data={'username': 'your_username', 'password': 'your_password'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login Successful', response.data)

    def test_create_fee(self):
        with self.app:
            with self.app.session_transaction() as sess:
                sess['user_id'] = 'your_user_id'  # Replace with a valid user ID for testing
                sess['user_role'] = 'admin'  # Adjust based on your roles
                sess['username'] = 'your_username'

            response = self.app.post('/create_fees', data={'fee_amount': 100, 'fee_type': 'Tuition'})
            self.assertEqual(response.status_code, 302)  # Expecting a redirect after successful creation

            # Check if the fee was added to the database
            fees_count = self.mongo.db.fees.count_documents({})
            self.assertEqual(fees_count, 1)

    def test_signup(self):
        response = self.app.post('/signup', data={'username': 'new_user', 'password': 'new_password', 'role': 'student'})
        self.assertEqual(response.status_code, 302)  # Expecting a redirect after successful signup

        # Check if the new user was added to the database
        user_count = self.mongo.db.students.count_documents({'username': 'new_user'})
        self.assertEqual(user_count, 1)

    def test_dashboard(self):
        with self.app:
            with self.app.session_transaction() as sess:
                sess['user_id'] = 'your_user_id'  # Replace with a valid user ID for testing
                sess['user_role'] = 'teacher'  # Adjust based on your roles
                sess['username'] = 'your_username'

            response = self.app.get('/dashboard')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Teacher Dashboard', response.data)

    # Add more test cases based on your routes and functionalities

if __name__ == '__main__':
    unittest.main()
