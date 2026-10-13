import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

class AdminModel:
    @staticmethod
    def get_by_id(admin_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE admin_id = ?", (admin_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_username(username):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_profile(admin_id, principal_name, college_name, email, phone, department, photo=None, new_password=None):
        conn = get_db()
        cursor = conn.cursor()
        if new_password and photo:
            hashed = generate_password_hash(new_password)
            cursor.execute("""
            UPDATE admins 
            SET principal_name=?, college_name=?, email=?, phone=?, department=?, photo=?, password=?
            WHERE admin_id=?
            """, (principal_name, college_name, email, phone, department, photo, hashed, admin_id))
        elif new_password:
            hashed = generate_password_hash(new_password)
            cursor.execute("""
            UPDATE admins 
            SET principal_name=?, college_name=?, email=?, phone=?, department=?, password=?
            WHERE admin_id=?
            """, (principal_name, college_name, email, phone, department, hashed, admin_id))
        elif photo:
            cursor.execute("""
            UPDATE admins 
            SET principal_name=?, college_name=?, email=?, phone=?, department=?, photo=?
            WHERE admin_id=?
            """, (principal_name, college_name, email, phone, department, photo, admin_id))
        else:
            cursor.execute("""
            UPDATE admins 
            SET principal_name=?, college_name=?, email=?, phone=?, department=?
            WHERE admin_id=?
            """, (principal_name, college_name, email, phone, department, admin_id))
        conn.commit()
        conn.close()

    @staticmethod
    def get_dashboard_stats():
        conn = get_db()
        cursor = conn.cursor()

        # Total faculties
        cursor.execute("SELECT COUNT(*) AS count FROM faculties")
        total_faculties = cursor.fetchone()['count']

        # Total students
        cursor.execute("SELECT COUNT(*) AS count FROM students")
        total_students = cursor.fetchone()['count']

        # Total classes (distinct department, year, section)
        cursor.execute("SELECT COUNT(DISTINCT department || '-' || year || '-' || section) AS count FROM students")
        total_classes = cursor.fetchone()['count']

        # Today's attendance percentage
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(DISTINCT student_id) AS present_count FROM attendance WHERE date = ? AND status = 'Present'", (today,))
        present_count = cursor.fetchone()['present_count']
        
        today_percentage = round((present_count / total_students * 100), 1) if total_students > 0 else 0

        # Class-wise attendance for today or overall
        cursor.execute("""
            SELECT s.department, s.year, s.section, COUNT(DISTINCT s.student_id) as total_in_class,
                   COUNT(DISTINCT a.student_id) as present_today
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id AND a.date = ? AND a.status = 'Present'
            GROUP BY s.department, s.year, s.section
            ORDER BY s.department, s.year
        """, (today,))
        class_rows = cursor.fetchall()
        class_attendance = []
        for r in class_rows:
            pct = round((r['present_today'] / r['total_in_class'] * 100), 1) if r['total_in_class'] > 0 else 0
            class_attendance.append({
                "label": f"{r['department']} ({r['year']} - Sec {r['section']})",
                "present": r['present_today'],
                "total": r['total_in_class'],
                "percentage": pct
            })

        # Daily attendance (last 7 days)
        dates_7 = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        daily_trends = []
        for d in dates_7:
            cursor.execute("SELECT COUNT(DISTINCT student_id) as cnt FROM attendance WHERE date = ? AND status = 'Present'", (d,))
            cnt = cursor.fetchone()['cnt']
            # Format display label (e.g., Oct 05)
            dt_obj = datetime.strptime(d, "%Y-%m-%d")
            daily_trends.append({
                "date": d,
                "label": dt_obj.strftime("%b %d"),
                "count": cnt,
                "percentage": round((cnt / total_students * 100), 1) if total_students > 0 else 0
            })

        # Monthly attendance for current year
        current_year = datetime.now().strftime("%Y")
        cursor.execute("""
            SELECT strftime('%m', date) as month, COUNT(DISTINCT student_id || date) as total_presences
            FROM attendance
            WHERE strftime('%Y', date) = ? AND status = 'Present'
            GROUP BY strftime('%m', date)
            ORDER BY month ASC
        """, (current_year,))
        monthly_rows = cursor.fetchall()
        month_map = {f"{m:02d}": 0 for m in range(1, 13)}
        for r in monthly_rows:
            month_map[r['month']] = r['total_presences']
        
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_trends = [
            {"label": month_names[i], "count": month_map[f"{i+1:02d}"]}
            for i in range(12)
        ]

        # Recent activities (last 8 attendances)
        cursor.execute("""
            SELECT a.attendance_id, a.student_id, s.name as student_name, s.department, s.year, s.section,
                   f.name as faculty_name, a.date, a.time, a.status
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            LEFT JOIN faculties f ON a.faculty_id = f.faculty_id
            ORDER BY a.date DESC, a.time DESC
            LIMIT 8
        """)
        recent_activities = [dict(r) for r in cursor.fetchall()]

        conn.close()

        return {
            "total_faculties": total_faculties,
            "total_students": total_students,
            "total_classes": total_classes,
            "today_percentage": today_percentage,
            "today_present": present_count,
            "today_absent": max(0, total_students - present_count),
            "class_attendance": class_attendance,
            "daily_trends": daily_trends,
            "monthly_trends": monthly_trends,
            "recent_activities": recent_activities
        }


class FacultyModel:
    @staticmethod
    def get_by_id(faculty_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM faculties WHERE faculty_id = ?", (faculty_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_username(username):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM faculties WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM faculties ORDER BY faculty_id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def create(faculty_id, name, department, email, phone, username, password):
        conn = get_db()
        cursor = conn.cursor()
        hashed = generate_password_hash(password)
        cursor.execute("""
        INSERT INTO faculties (faculty_id, name, department, email, phone, username, password)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (faculty_id, name, department, email, phone, username, hashed))
        conn.commit()
        conn.close()

    @staticmethod
    def update(faculty_id, name, department, email, phone, username, new_password=None):
        conn = get_db()
        cursor = conn.cursor()
        if new_password:
            hashed = generate_password_hash(new_password)
            cursor.execute("""
            UPDATE faculties 
            SET name=?, department=?, email=?, phone=?, username=?, password=?
            WHERE faculty_id=?
            """, (name, department, email, phone, username, hashed, faculty_id))
        else:
            cursor.execute("""
            UPDATE faculties 
            SET name=?, department=?, email=?, phone=?, username=?
            WHERE faculty_id=?
            """, (name, department, email, phone, username, faculty_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(faculty_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM faculties WHERE faculty_id = ?", (faculty_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_dashboard_stats(faculty_id=None):
        conn = get_db()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("SELECT COUNT(*) AS count FROM students")
        total_students = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(DISTINCT student_id) AS present_count FROM attendance WHERE date = ? AND status = 'Present'", (today,))
        present_count = cursor.fetchone()['present_count']

        absent_count = max(0, total_students - present_count)
        percentage = round((present_count / total_students * 100), 1) if total_students > 0 else 0

        # Today's marked by this faculty
        query = """
            SELECT a.attendance_id, a.student_id, s.name as student_name, s.department, s.year, s.section,
                   a.date, a.time, a.status
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.date = ?
        """
        params = [today]
        if faculty_id:
            query += " AND a.faculty_id = ?"
            params.append(faculty_id)
        query += " ORDER BY a.time DESC LIMIT 10"

        cursor.execute(query, params)
        recent_scans = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return {
            "total_students": total_students,
            "present_count": present_count,
            "absent_count": absent_count,
            "percentage": percentage,
            "recent_scans": recent_scans
        }


class StudentModel:
    @staticmethod
    def get_by_id(student_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_username_or_email(identifier):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE username = ? OR email = ?", (identifier, identifier))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all(search=None, department=None, year=None, section=None):
        conn = get_db()
        cursor = conn.cursor()
        query = "SELECT * FROM students WHERE 1=1"
        params = []

        if search:
            query += " AND (student_id LIKE ? OR name LIKE ? OR email LIKE ? OR username LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s, s])

        if department:
            query += " AND department = ?"
            params.append(department)

        if year:
            query += " AND year = ?"
            params.append(year)

        if section:
            query += " AND section = ?"
            params.append(section)

        query += " ORDER BY student_id ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def create(student_id, name, department, year, semester, section, phone, parent_phone, email, username, password, photo, qr_code):
        conn = get_db()
        cursor = conn.cursor()
        hashed = generate_password_hash(password)
        cursor.execute("""
        INSERT INTO students (student_id, name, department, year, semester, section, phone, parent_phone, email, username, password, photo, qr_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, name, department, year, semester, section, phone, parent_phone, email, username, hashed, photo, qr_code))
        conn.commit()
        conn.close()

    @staticmethod
    def update(student_id, name, department, year, semester, section, phone, parent_phone, email, username=None, new_password=None, photo=None):
        conn = get_db()
        cursor = conn.cursor()
        query = "UPDATE students SET name=?, department=?, year=?, semester=?, section=?, phone=?, parent_phone=?, email=?"
        params = [name, department, year, semester, section, phone, parent_phone, email]

        if username:
            query += ", username=?"
            params.append(username)

        if new_password:
            query += ", password=?"
            params.append(generate_password_hash(new_password))

        if photo:
            query += ", photo=?"
            params.append(photo)

        query += " WHERE student_id=?"
        params.append(student_id)

        cursor.execute(query, params)
        conn.commit()
        conn.close()

    @staticmethod
    def update_profile_by_student(student_id, phone, parent_phone, email, new_password=None, photo=None):
        conn = get_db()
        cursor = conn.cursor()
        query = "UPDATE students SET phone=?, parent_phone=?, email=?"
        params = [phone, parent_phone, email]

        if new_password:
            query += ", password=?"
            params.append(generate_password_hash(new_password))

        if photo:
            query += ", photo=?"
            params.append(photo)

        query += " WHERE student_id=?"
        params.append(student_id)

        cursor.execute(query, params)
        conn.commit()
        conn.close()

    @staticmethod
    def delete(student_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_attendance_stats(student_id):
        conn = get_db()
        cursor = conn.cursor()

        # Distinct college active attendance days recorded in system
        cursor.execute("SELECT COUNT(DISTINCT date) as total_days FROM attendance")
        total_days = cursor.fetchone()['total_days']
        total_days = max(1, total_days) # prevent division by zero

        # Days attended by this student
        cursor.execute("SELECT COUNT(DISTINCT date) as attended_days FROM attendance WHERE student_id = ? AND status = 'Present'", (student_id,))
        attended_days = cursor.fetchone()['attended_days']

        percentage = round((attended_days / total_days * 100), 1)

        # Today's status
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT status, time FROM attendance WHERE student_id = ? AND date = ?", (student_id, today))
        today_record = cursor.fetchone()

        today_status = today_record['status'] if today_record else "Absent"
        today_time = today_record['time'] if today_record else None

        # Full attendance history
        cursor.execute("""
            SELECT a.attendance_id, a.date, a.time, a.status, COALESCE(f.name, 'College Admin') as faculty_name
            FROM attendance a
            LEFT JOIN faculties f ON a.faculty_id = f.faculty_id
            WHERE a.student_id = ?
            ORDER BY a.date DESC, a.time DESC
        """, (student_id,))
        history = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return {
            "total_days": total_days,
            "attended_days": attended_days,
            "percentage": percentage,
            "today_status": today_status,
            "today_time": today_time,
            "history": history
        }


class AttendanceModel:
    @staticmethod
    def is_already_marked_today(student_id, date):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT attendance_id FROM attendance WHERE student_id = ? AND date = ?", (student_id, date))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    @staticmethod
    def mark_attendance(student_id, faculty_id, date, time, status="Present"):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO attendance (student_id, faculty_id, date, time, status)
        VALUES (?, ?, ?, ?, ?)
        """, (student_id, faculty_id, date, time, status))
        conn.commit()
        att_id = cursor.lastrowid
        conn.close()
        return att_id

    @staticmethod
    def get_records(date=None, department=None, class_year=None, section=None, student_id=None, faculty_id=None, start_date=None, end_date=None):
        conn = get_db()
        cursor = conn.cursor()
        query = """
            SELECT a.attendance_id, a.student_id, s.name as student_name, s.department, s.year, s.semester, s.section,
                   COALESCE(f.name, 'Admin/Faculty') as faculty_name, a.date, a.time, a.status
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            LEFT JOIN faculties f ON a.faculty_id = f.faculty_id
            WHERE 1=1
        """
        params = []

        if date:
            query += " AND a.date = ?"
            params.append(date)

        if start_date and end_date:
            query += " AND a.date BETWEEN ? AND ?"
            params.extend([start_date, end_date])

        if department:
            query += " AND s.department = ?"
            params.append(department)

        if class_year:
            query += " AND s.year = ?"
            params.append(class_year)

        if section:
            query += " AND s.section = ?"
            params.append(section)

        if student_id:
            query += " AND (a.student_id LIKE ? OR s.name LIKE ?)"
            s_val = f"%{student_id}%"
            params.extend([s_val, s_val])

        if faculty_id:
            query += " AND a.faculty_id = ?"
            params.append(faculty_id)

        query += " ORDER BY a.date DESC, a.time DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_distinct_filters():
        """Returns distinct departments, years, and sections for dropdown filters."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT department FROM students WHERE department IS NOT NULL AND department != '' ORDER BY department")
        departments = [r['department'] for r in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT year FROM students WHERE year IS NOT NULL AND year != '' ORDER BY year")
        years = [r['year'] for r in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT section FROM students WHERE section IS NOT NULL AND section != '' ORDER BY section")
        sections = [r['section'] for r in cursor.fetchall()]
        conn.close()
        return {
            "departments": departments,
            "years": years,
            "sections": sections
        }
