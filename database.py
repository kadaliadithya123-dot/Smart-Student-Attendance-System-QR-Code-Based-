import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from utils.qr_generator import generate_qr_code

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")
QR_DIR = os.path.join(BASE_DIR, "static", "qr_codes")

def get_db():
    """Returns a SQLite connection configured with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes tables and seeds initial demo records if not present."""
    os.makedirs(QR_DIR, exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # 1. Admin table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        principal_name TEXT NOT NULL,
        college_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        department TEXT DEFAULT 'Administration',
        photo TEXT DEFAULT 'default_avatar.png'
    );
    """)

    # 2. Faculty table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faculties (
        faculty_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        year TEXT NOT NULL,
        semester TEXT NOT NULL,
        section TEXT NOT NULL,
        phone TEXT NOT NULL,
        parent_phone TEXT NOT NULL,
        email TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        photo TEXT DEFAULT 'default_avatar.png',
        qr_code TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Attendance table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        faculty_id TEXT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT DEFAULT 'Present',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # Seed Admin if none exists
    cursor.execute("SELECT COUNT(*) AS cnt FROM admins;")
    if cursor.fetchone()['cnt'] == 0:
        admin_pass = generate_password_hash("admin123")
        cursor.execute("""
        INSERT INTO admins (username, password, principal_name, college_name, email, phone, department, photo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "admin",
            admin_pass,
            "Dr. Ramesh Kumar",
            "National Institute of Engineering & Technology",
            "principal@niet.edu",
            "+91 9876543210",
            "Executive Administration",
            "default_avatar.png"
        ))
        conn.commit()

    # Seed Faculty if none exists
    cursor.execute("SELECT COUNT(*) AS cnt FROM faculties;")
    if cursor.fetchone()['cnt'] == 0:
        fac_pass = generate_password_hash("faculty123")
        faculties = [
            ("FAC001", "Dr. Anita Sharma", "Computer Science", "anita.cs@niet.edu", "+91 9876501234", "anita_fac", fac_pass),
            ("FAC002", "Prof. Vikram Verma", "Electronics & Communication", "vikram.ec@niet.edu", "+91 9876505678", "vikram_fac", fac_pass),
            ("FAC003", "Dr. K. S. Mehra", "Mechanical Engineering", "mehra.mech@niet.edu", "+91 9876509999", "mehra_fac", fac_pass)
        ]
        cursor.executemany("""
        INSERT INTO faculties (faculty_id, name, department, email, phone, username, password)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, faculties)
        conn.commit()

    # Seed Students if none exists
    cursor.execute("SELECT COUNT(*) AS cnt FROM students;")
    if cursor.fetchone()['cnt'] == 0:
        stu_pass = generate_password_hash("student123")
        students = [
            ("STU101", "Rahul Verma", "Computer Science", "3rd Year", "5th Sem", "A", "+91 9811122233", "+91 9811122234", "rahul.verma@gmail.com", "rahul101", stu_pass),
            ("STU102", "Priya Patel", "Computer Science", "3rd Year", "5th Sem", "A", "+91 9822233344", "+91 9822233345", "priya.patel@gmail.com", "priya102", stu_pass),
            ("STU103", "Amit Singh", "Electronics & Communication", "2nd Year", "3rd Sem", "B", "+91 9833344455", "+91 9833344456", "amit.singh@gmail.com", "amit103", stu_pass),
            ("STU104", "Sneha Rao", "Computer Science", "4th Year", "7th Sem", "A", "+91 9844455566", "+91 9844455567", "sneha.rao@gmail.com", "sneha104", stu_pass),
            ("STU105", "Karan Malhotra", "Mechanical Engineering", "1st Year", "1st Sem", "C", "+91 9855566677", "+91 9855566678", "karan.malhotra@gmail.com", "karan105", stu_pass)
        ]
        
        for s in students:
            # Generate QR code for each student
            qr_file = generate_qr_code(s[0], QR_DIR)
            cursor.execute("""
            INSERT INTO students (student_id, name, department, year, semester, section, phone, parent_phone, email, username, password, photo, qr_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'default_avatar.png', ?)
            """, (*s, qr_file))
        conn.commit()

    # Seed Attendance if none exists
    cursor.execute("SELECT COUNT(*) AS cnt FROM attendance;")
    if cursor.fetchone()['cnt'] == 0:
        now = datetime.now()
        dates = [
            (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            now.strftime("%Y-%m-%d")
        ]
        
        sample_attendance = [
            # 2 days ago
            ("STU101", "FAC001", dates[0], "09:12:30", "Present"),
            ("STU102", "FAC001", dates[0], "09:14:05", "Present"),
            ("STU103", "FAC002", dates[0], "09:20:11", "Present"),
            ("STU104", "FAC001", dates[0], "09:22:45", "Present"),
            # Yesterday
            ("STU101", "FAC001", dates[1], "09:05:14", "Present"),
            ("STU102", "FAC001", dates[1], "09:08:42", "Present"),
            ("STU103", "FAC002", dates[1], "09:18:20", "Present"),
            # Today
            ("STU101", "FAC001", dates[2], "08:58:19", "Present"),
            ("STU102", "FAC001", dates[2], "09:02:11", "Present"),
        ]
        cursor.executemany("""
        INSERT INTO attendance (student_id, faculty_id, date, time, status)
        VALUES (?, ?, ?, ?, ?)
        """, sample_attendance)
        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded successfully.")
