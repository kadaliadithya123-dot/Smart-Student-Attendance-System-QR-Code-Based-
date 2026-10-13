import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, current_app
from werkzeug.utils import secure_filename
from models.models import StudentModel
from utils.helpers import login_required, role_required, allowed_file

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    student_id = session['user_id']
    student_info = StudentModel.get_by_id(student_id)
    if not student_info:
        flash("Student record not found.", "danger")
        return redirect(url_for('auth.logout'))

    stats = StudentModel.get_attendance_stats(student_id)
    return render_template('student_dashboard.html', student=student_info, stats=stats)

@student_bp.route('/download_qr')
@login_required
@role_required('student')
def download_qr():
    student_id = session['user_id']
    student_info = StudentModel.get_by_id(student_id)
    if not student_info or not student_info.get('qr_code'):
        flash("QR Code not available.", "danger")
        return redirect(url_for('student.dashboard'))

    qr_path = os.path.join(current_app.static_folder, 'qr_codes', student_info['qr_code'])
    if not os.path.exists(qr_path):
        flash("QR Code image file not found on server.", "danger")
        return redirect(url_for('student.dashboard'))

    return send_file(
        qr_path,
        mimetype='image/png',
        as_attachment=True,
        download_name=f"{student_id}_QRCode.png"
    )

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('student')
def profile():
    student_id = session['user_id']
    student_info = StudentModel.get_by_id(student_id)

    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        parent_phone = request.form.get('parent_phone', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('password', '').strip()

        if not all([phone, parent_phone, email]):
            flash("Phone, parent phone, and email are required.", "danger")
            return render_template('profile.html', user=student_info, user_role='student')

        photo_filename = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                fname = secure_filename(f"student_{student_id}_{file.filename}")
                upload_path = os.path.join(current_app.static_folder, 'uploads', fname)
                file.save(upload_path)
                photo_filename = fname

        try:
            StudentModel.update_profile_by_student(
                student_id=student_id,
                phone=phone,
                parent_phone=parent_phone,
                email=email,
                new_password=new_password if new_password else None,
                photo=photo_filename
            )
            flash("Profile updated successfully.", "success")
            return redirect(url_for('student.profile'))
        except Exception as e:
            flash(f"Failed to update profile: {str(e)}", "danger")

    return render_template('profile.html', user=student_info, user_role='student')

@student_bp.route('/attendance')
@login_required
@role_required('student')
def attendance():
    student_id = session['user_id']
    student_info = StudentModel.get_by_id(student_id)
    stats = StudentModel.get_attendance_stats(student_id)
    return render_template('attendance.html', records=stats['history'], student=student_info, user_role='student')
