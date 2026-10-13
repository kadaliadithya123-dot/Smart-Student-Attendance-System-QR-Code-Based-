import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from werkzeug.utils import secure_filename
from models.models import FacultyModel, StudentModel, AttendanceModel
from utils.helpers import login_required, role_required, allowed_file, get_current_date, get_current_time, export_attendance_to_csv_response
from utils.qr_generator import generate_qr_code

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty_bp.route('/dashboard')
@login_required
@role_required('faculty')
def dashboard():
    faculty_id = session['user_id']
    stats = FacultyModel.get_dashboard_stats(faculty_id)
    faculty_info = FacultyModel.get_by_id(faculty_id)
    return render_template('faculty_dashboard.html', stats=stats, faculty=faculty_info)

@faculty_bp.route('/register_student', methods=['GET', 'POST'])
@login_required
@role_required('faculty')
def register_student():
    filter_data = AttendanceModel.get_distinct_filters()

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip().upper()
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        semester = request.form.get('semester', '').strip()
        section = request.form.get('section', '').strip().upper()
        phone = request.form.get('phone', '').strip()
        parent_phone = request.form.get('parent_phone', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Validate mandatory fields
        if not all([student_id, name, department, year, semester, section, phone, parent_phone, email, username, password]):
            flash("All student fields are required.", "danger")
            return render_template('register_student.html', filters=filter_data)

        if StudentModel.get_by_id(student_id):
            flash(f"Student ID '{student_id}' already exists.", "danger")
            return render_template('register_student.html', filters=filter_data)

        if StudentModel.get_by_username_or_email(username):
            flash(f"Username '{username}' is already in use.", "danger")
            return render_template('register_student.html', filters=filter_data)

        # Handle photo upload
        photo_filename = 'default_avatar.png'
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                fname = secure_filename(f"student_{student_id}_{file.filename}")
                upload_path = os.path.join(current_app.static_folder, 'uploads', fname)
                file.save(upload_path)
                photo_filename = fname

        # Automatically generate unique QR code
        qr_dir = os.path.join(current_app.static_folder, 'qr_codes')
        qr_filename = generate_qr_code(student_id, qr_dir)

        # Save to SQLite
        try:
            StudentModel.create(
                student_id=student_id,
                name=name,
                department=department,
                year=year,
                semester=semester,
                section=section,
                phone=phone,
                parent_phone=parent_phone,
                email=email,
                username=username,
                password=password,
                photo=photo_filename,
                qr_code=qr_filename
            )
            flash(f"Student '{name}' ({student_id}) registered successfully with QR code generated!", "success")
            return redirect(url_for('faculty.students'))
        except Exception as e:
            flash(f"Error registering student: {str(e)}", "danger")

    return render_template('register_student.html', filters=filter_data)

@faculty_bp.route('/scanner')
@login_required
@role_required('faculty')
def scanner():
    return render_template('scanner.html')

@faculty_bp.route('/mark_attendance', methods=['POST'])
@login_required
@role_required('faculty')
def mark_attendance():
    """AJAX endpoint for the live html5-qrcode scanner."""
    data = request.get_json(silent=True) or {}
    student_id = data.get('student_id', '').strip().upper()

    if not student_id:
        return jsonify({"success": False, "message": "No Student ID provided."}), 400

    student = StudentModel.get_by_id(student_id)
    if not student:
        return jsonify({"success": False, "message": f"Student ID '{student_id}' not found in database."}), 404

    today = get_current_date()
    cur_time = get_current_time()

    # Check duplicate attendance for current day
    if AttendanceModel.is_already_marked_today(student_id, today):
        return jsonify({
            "success": False,
            "already_marked": True,
            "message": "Attendance Already Marked",
            "student": {
                "student_id": student['student_id'],
                "name": student['name'],
                "department": student['department']
            }
        })

    # Save attendance
    try:
        faculty_id = session.get('user_id')
        AttendanceModel.mark_attendance(
            student_id=student_id,
            faculty_id=faculty_id,
            date=today,
            time=cur_time,
            status="Present"
        )
        return jsonify({
            "success": True,
            "already_marked": False,
            "message": "Attendance Marked Successfully",
            "student": {
                "student_id": student['student_id'],
                "name": student['name'],
                "department": student['department'],
                "year": student['year'],
                "section": student['section'],
                "date": today,
                "time": cur_time
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@faculty_bp.route('/students')
@login_required
@role_required('faculty')
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
        user_role='faculty'
    )

@faculty_bp.route('/students/edit/<student_id>', methods=['POST'])
@login_required
@role_required('faculty')
def edit_student(student_id):
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    year = request.form.get('year', '').strip()
    semester = request.form.get('semester', '').strip()
    section = request.form.get('section', '').strip().upper()
    phone = request.form.get('phone', '').strip()
    parent_phone = request.form.get('parent_phone', '').strip()
    email = request.form.get('email', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    photo_filename = None
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename != '' and allowed_file(file.filename):
            fname = secure_filename(f"student_{student_id}_{file.filename}")
            upload_path = os.path.join(current_app.static_folder, 'uploads', fname)
            file.save(upload_path)
            photo_filename = fname

    try:
        StudentModel.update(
            student_id=student_id,
            name=name,
            department=department,
            year=year,
            semester=semester,
            section=section,
            phone=phone,
            parent_phone=parent_phone,
            email=email,
            username=username if username else None,
            new_password=password if password else None,
            photo=photo_filename
        )
        flash(f"Student '{name}' updated successfully.", "success")
    except Exception as e:
        flash(f"Failed to update student: {str(e)}", "danger")

    return redirect(url_for('faculty.students'))

@faculty_bp.route('/students/delete/<student_id>', methods=['POST'])
@login_required
@role_required('faculty')
def delete_student(student_id):
    try:
        StudentModel.delete(student_id)
        flash("Student record removed successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete student: {str(e)}", "danger")
    return redirect(url_for('faculty.students'))

@faculty_bp.route('/attendance')
@login_required
@role_required('faculty')
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
        user_role='faculty'
    )

@faculty_bp.route('/reports')
@login_required
@role_required('faculty')
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
        user_role='faculty'
    )

@faculty_bp.route('/reports/export')
@login_required
@role_required('faculty')
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

    return export_attendance_to_csv_response(records, filename_prefix=f"faculty_{report_type}_report")
