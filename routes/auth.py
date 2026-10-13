from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from models.models import AdminModel, FacultyModel, StudentModel

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    selected_role = request.args.get('role', 'admin').lower()
    if selected_role not in ['admin', 'faculty', 'student']:
        selected_role = 'admin'

    # If already logged in, redirect to respective dashboard
    if 'user_id' in session and 'role' in session:
        role = session['role']
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'faculty':
            return redirect(url_for('faculty.dashboard'))
        elif role == 'student':
            return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        role = request.form.get('role', 'admin').lower()
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not identifier or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('login.html', selected_role=role)

        if role == 'admin':
            admin = AdminModel.get_by_username(identifier)
            if admin and check_password_hash(admin['password'], password):
                session.clear()
                session['user_id'] = admin['admin_id']
                session['role'] = 'admin'
                session['name'] = admin['principal_name']
                session['username'] = admin['username']
                session['college_name'] = admin['college_name']
                flash(f"Welcome back, {admin['principal_name']}!", "success")
                return redirect(url_for('admin.dashboard'))
            else:
                flash("Invalid Admin username or password.", "danger")

        elif role == 'faculty':
            faculty = FacultyModel.get_by_username(identifier)
            if faculty and check_password_hash(faculty['password'], password):
                session.clear()
                session['user_id'] = faculty['faculty_id']
                session['role'] = 'faculty'
                session['name'] = faculty['name']
                session['username'] = faculty['username']
                session['department'] = faculty['department']
                flash(f"Welcome back, {faculty['name']}!", "success")
                return redirect(url_for('faculty.dashboard'))
            else:
                flash("Invalid Faculty username or password.", "danger")

        elif role == 'student':
            # Student can login with either username or Gmail/email
            student = StudentModel.get_by_username_or_email(identifier)
            if student and check_password_hash(student['password'], password):
                session.clear()
                session['user_id'] = student['student_id']
                session['role'] = 'student'
                session['name'] = student['name']
                session['username'] = student['username']
                session['email'] = student['email']
                session['department'] = student['department']
                flash(f"Welcome back, {student['name']}!", "success")
                return redirect(url_for('student.dashboard'))
            else:
                flash("Invalid Student username/email or password.", "danger")

        return render_template('login.html', selected_role=role)

    return render_template('login.html', selected_role=selected_role)

@auth_bp.route('/login/admin')
def login_admin():
    return redirect(url_for('auth.login', role='admin'))

@auth_bp.route('/login/faculty')
def login_faculty():
    return redirect(url_for('auth.login', role='faculty'))

@auth_bp.route('/login/student')
def login_student():
    return redirect(url_for('auth.login', role='student'))

@auth_bp.route('/logout')
def logout():
    role = session.get('role', 'student')
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('auth.login', role=role))
