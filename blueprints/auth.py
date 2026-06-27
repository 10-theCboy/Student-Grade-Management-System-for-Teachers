import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from app import bcrypt, get_db, TRANSLATIONS
from utils.decorators import login_required, require_role, csrf_required
from models.user import find_by_username, find_by_email
from models.course import find_by_enrollment_code
from models.enrollment import enroll

auth_bp = Blueprint('auth', __name__)

ROLE_REDIRECTS = {
    'admin': 'admin.dashboard',
    'teacher': 'teacher.dashboard',
    'student': 'student.dashboard'
}


@auth_bp.before_request
def load_user():
    g.db = get_db()
    if 'user_id' in session:
        g.user = g.db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
        if not g.user:
            session.clear()
            return redirect(url_for('auth.login'))


@auth_bp.route('/')
def root():
    if 'user_id' in session:
        role = session.get('role')
        if role in ROLE_REDIRECTS:
            return redirect(url_for(ROLE_REDIRECTS[role]))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf_required
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = find_by_username(username)
        if user and bcrypt.check_password_hash(user['password_hash'], password):
            selected_role = request.form.get('selected_role', '')
            if selected_role and selected_role != user['role']:
                flash(f'Tip: That account is a {user["role"].title()}, not {selected_role.title()}. '
                      f'You\'ll be logged in as {user["role"].title()} instead.', 'info')
            session['user_id'] = user['id']
            session['role'] = user['role']
            flash(f'Welcome, {user["full_name"]}!', 'success')
            return redirect(url_for(ROLE_REDIRECTS[user['role']]))

        return render_template('auth/login.html', error=True, username=username)

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
@csrf_required
def register():
    data = {}
    field_errors = {}
    if request.method == 'POST':
        data = {
            'full_name': request.form.get('full_name', '').strip(),
            'username': request.form.get('username', '').strip(),
            'email': request.form.get('email', '').strip(),
            'enrollment_code': request.form.get('enrollment_code', '').strip(),
        }
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        def add_error(field, msg):
            field_errors[field] = msg

        if not data['full_name']:
            add_error('full_name', 'Full name is required.')
        if not data['username']:
            add_error('username', 'Username is required.')
        if not data['email']:
            add_error('email', 'Email is required.')
        if not data['enrollment_code']:
            add_error('enrollment_code', 'Enrollment code is required.')
        if not password:
            add_error('password', 'Password is required.')
        if not confirm:
            add_error('confirm_password', 'Please confirm your password.')

        if password and confirm and password != confirm:
            add_error('confirm_password', 'Passwords do not match.')

        if password:
            if len(password) < 8:
                add_error('password', 'At least 8 characters.')
            elif not re.search(r'[A-Z]', password):
                add_error('password', 'Must contain an uppercase letter.')
            elif not re.search(r'[a-z]', password):
                add_error('password', 'Must contain a lowercase letter.')
            elif not re.search(r'\d', password):
                add_error('password', 'Must contain a digit.')
            elif not re.search(r'[^a-zA-Z0-9]', password):
                add_error('password', 'Must contain a special character.')

        if data['username'] and find_by_username(data['username']):
            add_error('username', 'Username already taken.')

        if data['email'] and find_by_email(data['email']):
            add_error('email', 'Email already registered.')

        course = None
        if data['enrollment_code'] and not field_errors.get('enrollment_code'):
            course = find_by_enrollment_code(data['enrollment_code'])
            if not course:
                add_error('enrollment_code', 'Invalid enrollment code.')

        if field_errors:
            return render_template('auth/register.html', data=data, field_errors=field_errors)

        pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        try:
            g.db.execute("INSERT INTO users (username,password_hash,full_name,email,role) VALUES (?,?,?,?,?)",
                         (data['username'], pw_hash, data['full_name'], data['email'], 'student'))
            g.db.commit()
            user = g.db.execute("SELECT id FROM users WHERE username=?", (data['username'],)).fetchone()
            enroll(user['id'], course['id'])
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'Registration error: {e}', 'danger')

    return render_template('auth/register.html', data=data, field_errors=field_errors)


@auth_bp.route('/language/<lang>')
def set_language(lang):
    if lang in ('en', 'zh'):
        session['lang'] = lang
    referrer = request.referrer or url_for('auth.login')
    return redirect(referrer)


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from models.user import find_by_id
    g.db = get_db()
    user = find_by_id(session['user_id'])
    current_lang = session.get('lang', 'en')
    t = TRANSLATIONS.get(current_lang, TRANSLATIONS['en'])
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        avatar_data = request.form.get('avatar_data', '').strip()
        cur_pw = request.form.get('current_password', '')
        new_pw = request.form.get('new_password', '')

        if full_name and email:
            if avatar_data:
                g.db.execute("UPDATE users SET full_name=?, email=?, avatar=? WHERE id=?",
                             (full_name, email, avatar_data, session['user_id']))
            else:
                g.db.execute("UPDATE users SET full_name=?, email=? WHERE id=?",
                             (full_name, email, session['user_id']))
            g.db.commit()
            flash(t.get('settings_updated', 'Settings updated successfully.'), 'success')

        if cur_pw and new_pw:
            if bcrypt.check_password_hash(user['password_hash'], cur_pw):
                pw_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
                g.db.execute("UPDATE users SET password_hash=? WHERE id=?", (pw_hash, session['user_id']))
                g.db.commit()
                flash(t.get('password_changed', 'Password changed successfully.'), 'success')
            else:
                flash(t.get('invalid_password', 'Current password is incorrect.'), 'danger')
        return redirect(url_for('auth.profile'))

    return render_template('profile.html', user=user)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/403')
def forbidden():
    return render_template('403.html'), 403


@auth_bp.route('/404')
def not_found():
    return render_template('404.html'), 404
