import unittest
import json
import os
from app import create_app
from database import get_db

class TestAttendanceSystem(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_login_page_renders(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AttendTrack', response.data)
        self.assertIn(b'Admin', response.data)
        self.assertIn(b'Faculty', response.data)
        self.assertIn(b'Student', response.data)

    def test_02_admin_login_and_dashboard(self):
        # Login as Admin
        response = self.client.post('/login', data={
            'role': 'admin',
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'College Admin Overview', response.data)
        self.assertIn(b'Total Faculties', response.data)
        self.assertIn(b'Total Students', response.data)

    def test_03_student_login_with_gmail(self):
        # Login using student Gmail
        response = self.client.post('/login', data={
            'role': 'student',
            'username': 'rahul.verma@gmail.com',
            'password': 'student123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Student Portal', response.data)
        self.assertIn(b'Rahul Verma', response.data)
        self.assertIn(b'Download QR Code', response.data)

    def test_04_student_qr_download(self):
        # Login as student
        self.client.post('/login', data={
            'role': 'student',
            'username': 'rahul101',
            'password': 'student123'
        })
        response = self.client.get('/student/download_qr')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')
        self.assertIn('STU101_QRCode.png', response.headers.get('Content-Disposition', ''))

    def test_05_faculty_scanner_and_duplicate_prevention(self):
        # Login as Faculty
        self.client.post('/login', data={
            'role': 'faculty',
            'username': 'anita_fac',
            'password': 'faculty123'
        })

        # Test valid student STU103 (Amit Singh, not marked today yet)
        response = self.client.post('/faculty/mark_attendance', 
            data=json.dumps({'student_id': 'STU103'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Attendance Marked Successfully')
        self.assertEqual(data['student']['student_id'], 'STU103')

        # Test duplicate scan for same student on same day
        dup_response = self.client.post('/faculty/mark_attendance',
            data=json.dumps({'student_id': 'STU103'}),
            content_type='application/json'
        )
        self.assertEqual(dup_response.status_code, 200)
        dup_data = json.loads(dup_response.data)
        self.assertFalse(dup_data['success'])
        self.assertTrue(dup_data['already_marked'])
        self.assertEqual(dup_data['message'], 'Attendance Already Marked')

        # Test invalid student ID
        invalid_response = self.client.post('/faculty/mark_attendance',
            data=json.dumps({'student_id': 'INVALID999'}),
            content_type='application/json'
        )
        self.assertEqual(invalid_response.status_code, 404)

    def test_06_faculty_register_student_and_qr_generation(self):
        # Login as Faculty
        self.client.post('/login', data={
            'role': 'faculty',
            'username': 'anita_fac',
            'password': 'faculty123'
        })

        # Register new student
        new_stu_id = 'STU999'
        response = self.client.post('/faculty/register_student', data={
            'student_id': new_stu_id,
            'name': 'Test Student User',
            'department': 'Computer Science',
            'year': '1st Year',
            'semester': '2nd Sem',
            'section': 'B',
            'phone': '+91 9999900001',
            'parent_phone': '+91 9999900002',
            'email': 'test.student@gmail.com',
            'username': 'teststu999',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check QR code file exists
        qr_file_path = os.path.join(self.app.static_folder, 'qr_codes', f'{new_stu_id}.png')
        self.assertTrue(os.path.exists(qr_file_path))

        # Check newly created student can log in with Gmail!
        self.client.get('/logout')
        login_res = self.client.post('/login', data={
            'role': 'student',
            'username': 'test.student@gmail.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Test Student User', login_res.data)

    def test_07_csv_reports_export(self):
        # Login as Admin
        self.client.post('/login', data={
            'role': 'admin',
            'username': 'admin',
            'password': 'admin123'
        })

        response = self.client.get('/admin/reports/export?type=daily')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')
        self.assertIn(b'Record ID,Student ID,Student Name', response.data)

if __name__ == '__main__':
    unittest.main()
