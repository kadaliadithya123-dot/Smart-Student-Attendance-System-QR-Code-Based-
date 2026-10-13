import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from models.models import AdminModel, FacultyModel, StudentModel, AttendanceModel
from utils.helpers import login_required, role_required, allowed_file, export_attendance_to_csv_response

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    stats = AdminModel.get_dashboard_stats()
    admin_info = AdminModel.get_by_id(session['user_id'])
    return render_template('admin_dashboard.html', stats=stats, admin=admin_info)

@admin_bp.route('/faculties')
@login_required
@role_required('admin')
def faculties():
    faculty_list = FacultyModel.get_all()
    filter_data = AttendanceModel.get_distinct_filters()
    return render_template('faculty_management.html', faculties=faculty_list, departments=filter_data['departments'])

@admin_bp.route('/faculties/add', methods=['POST'])
@login_required
@role_required('admin')
def add_faculty():
    faculty_id = request.form.get('faculty_id', '').strip().upper()
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not all([faculty_id, name, department, email, phone, username, password]):
        flash("All faculty fields are mandatory.", "danger")
        return redirect(url_for('admin.faculties'))

    if FacultyModel.get_by_id(faculty_id):
        flash(f"Faculty ID '{faculty_id}' already exists.", "danger")
        return redirect(url_for('admin.faculties'))

    if FacultyModel.get_by_username(username):
        flash(f"Username '{username}' is already taken.", "danger")
        return redirect(url_for('admin.faculties'))

    try:
        FacultyModel.create(faculty_id, name, department, email, phone, username, password)
        flash(f"Faculty member '{name}' registered successfully.", "success")
    except Exception as e:
        flash(f"Error registering faculty: {str(e)}", "danger")

    return redirect(url_for('admin.faculties'))

@admin_bp.route('/faculties/edit/<faculty_id>', methods=['POST'])
@login_required
@role_required('admin')
def edit_faculty(faculty_id):
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not all([name, department, email, phone, username]):
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for('admin.faculties'))

    try:
        FacultyModel.update(faculty_id, name, department, email, phone, username, new_password=password if password else None)
        flash(f"Faculty '{name}' details updated successfully.", "success")
    except Exception as e:
        flash(f"Failed to update faculty: {str(e)}", "danger")

    return redirect(url_for('admin.faculties'))

@admin_bp.route('/faculties/delete/<faculty_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_faculty(faculty_id):
    try:
        FacultyModel.delete(faculty_id)
        flash("Faculty member deleted successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete faculty: {str(e)}", "danger")
    return redirect(url_for('admin.faculties'))

@admin_bp.route('/students')
@login_required
@role_required('admin')
def students():
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    year = request.args.get('year', '').strip()
    section = request.args.get('section', '').strip()

    student_list = StudentModel.get_all(
        search=search if search else None,
        department=department if department else None,
        year=year if year else None,
        section=section if section else None
    )
    filter_data = AttendanceModel.get_distinct_filters()

    return render_template(
        'students.html',
        students=student_list,
        filters=filter_data,
        selected_search=search,
        selected_dept=department,
        selected_year=year,
        selected_sec=section,
        user_role='admin'
    )

@admin_bp.route('/attendance')
@login_required
@role_required('admin')
def attendance():
    date = request.args.get('date', '').strip()
    department = request.args.get('department', '').strip()
    class_year = request.args.get('year', '').strip()
    section = request.args.get('section', '').strip()
    student_id = request.args.get('student_id', '').strip()

    records = AttendanceModel.get_records(
        date=date if date else None,
        department=department if department else None,
        class_year=class_year if class_year else None,
        section=section if section else None,
        student_id=student_id if student_id else None
    )
    filter_data = AttendanceModel.get_distinct_filters()

    return render_template(
        'attendance.html',
        records=records,
        filters=filter_data,
        selected_date=date,
        selected_dept=department,
        selected_year=class_year,
        selected_sec=section,
        selected_student=student_id,
        user_role='admin'
    )

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def profile():
    admin = AdminModel.get_by_id(session['user_id'])
    if request.method == 'POST':
        principal_name = request.form.get('principal_name', '').strip()
        college_name = request.form.get('college_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        new_password = request.form.get('password', '').strip()

        photo_filename = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                fname = secure_filename(f"admin_{session['user_id']}_{file.filename}")
                upload_path = os.path.join(current_app.static_folder, 'uploads', fname)
                file.save(upload_path)
                photo_filename = fname

        AdminModel.update_profile(
            session['user_id'],
            principal_name,
            college_name,
            email,
            phone,
            department,
            photo=photo_filename,
            new_password=new_password if new_password else None
        )
        session['name'] = principal_name
        session['college_name'] = college_name
        flash("Principal profile updated successfully.", "success")
        return redirect(url_for('admin.profile'))

    return render_template('profile.html', user=admin, user_role='admin')

@admin_bp.route('/reports')
@login_required
@role_required('admin')
def reports():
    report_type = request.args.get('type', 'daily')
    target_date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    department = request.args.get('department', '')

    start_date = None
    end_date = None

    if report_type == 'daily':
        start_date = target_date
        end_date = target_date
    elif report_type == 'weekly':
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        start_date = (dt - timedelta(days=6)).strftime("%Y-%m-%d")
        end_date = target_date
    elif report_type == 'monthly':
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        start_date = dt.strftime("%Y-%m-01")
        # end date is last day or target_date
        end_date = target_date

    records = AttendanceModel.get_records(
        start_date=start_date,
        end_date=end_date,
        department=department if department else None
    )
    filter_data = AttendanceModel.get_distinct_filters()

    return render_template(
        'reports.html',
        records=records,
        report_type=report_type,
        target_date=target_date,
        department=department,
        start_date=start_date,
        end_date=end_date,
        filters=filter_data,
        user_role='admin'
    )

@admin_bp.route('/reports/export')
@login_required
@role_required('admin')
def export_csv():
    report_type = request.args.get('type', 'daily')
    target_date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    department = request.args.get('department', '')

    start_date = None
    end_date = None

    if report_type == 'daily':
        start_date = target_date
        end_date = target_date
    elif report_type == 'weekly':
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        start_date = (dt - timedelta(days=6)).strftime("%Y-%m-%d")
        end_date = target_date
    elif report_type == 'monthly':
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        start_date = dt.strftime("%Y-%m-01")
        end_date = target_date

    records = AttendanceModel.get_records(
        start_date=start_date,
        end_date=end_date,
        department=department if department else None
    )

    return export_attendance_to_csv_response(records, filename_prefix=f"admin_{report_type}_report")
