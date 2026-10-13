import os
from flask import Flask, redirect, url_for, session, render_template
from database import init_db
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.faculty import faculty_bp
from routes.student import student_bp

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'smart-attendance-system-secret-key-2026')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max upload

    # Ensure required upload & static folders exist
    for sub in ['uploads', 'qr_codes', 'exports', 'images', 'css', 'js']:
        os.makedirs(os.path.join(app.static_folder, sub), exist_ok=True)

    # Initialize SQLite database with seed data
    init_db()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(student_bp)

    @app.route('/')
    def index():
        if 'user_id' in session and 'role' in session:
            role = session['role']
            if role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif role == 'faculty':
                return redirect(url_for('faculty.dashboard'))
            elif role == 'student':
                return redirect(url_for('student.dashboard'))
        return redirect(url_for('auth.login'))

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', not_found=True), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('base.html', server_error=True), 500

    @app.context_processor
    def inject_globals():
        return {
            'app_name': 'Smart Student Attendance System',
            'current_role': session.get('role', None),
            'current_user_name': session.get('name', 'User'),
            'current_user_id': session.get('user_id', None)
        }

    return app

app = create_app()

if __name__ == '__main__':
    # Run locally on host 127.0.0.1, port 5000
    print("Starting Smart Student Attendance System on http://127.0.0.1:5000 ...")
    app.run(debug=True, host='127.0.0.1', port=5000)
