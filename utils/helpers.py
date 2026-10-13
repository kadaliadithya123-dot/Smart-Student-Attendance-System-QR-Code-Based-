import os
import csv
import io
from functools import wraps
from datetime import datetime
from flask import session, redirect, url_for, flash, request, Response

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('auth.login', role=request.endpoint.split('.')[0] if '.' in request.endpoint else 'student'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or 'role' not in session:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for('auth.login'))
            if session.get('role') not in allowed_roles:
                flash("Access denied. You do not have permissions for this section.", "danger")
                # Redirect to appropriate dashboard
                role = session.get('role')
                if role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif role == 'faculty':
                    return redirect(url_for('faculty.dashboard'))
                elif role == 'student':
                    return redirect(url_for('student.dashboard'))
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_date() -> str:
    """Returns today's date formatted as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")

def get_current_time() -> str:
    """Returns current time formatted as HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")

def export_attendance_to_csv_response(records, filename_prefix="attendance_report"):
    """
    Generates a streaming CSV response from a list of attendance row dictionaries.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Record ID",
        "Student ID",
        "Student Name",
        "Department",
        "Year",
        "Semester",
        "Section",
        "Faculty / Marked By",
        "Date",
        "Time",
        "Status"
    ])
    
    for r in records:
        writer.writerow([
            r.get('attendance_id', ''),
            r.get('student_id', ''),
            r.get('student_name', ''),
            r.get('department', ''),
            r.get('year', ''),
            r.get('semester', ''),
            r.get('section', ''),
            r.get('faculty_name', 'Faculty'),
            r.get('date', ''),
            r.get('time', ''),
            r.get('status', 'Present')
        ])
    
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    download_filename = f"{filename_prefix}_{timestamp}.csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={download_filename}"}
    )
