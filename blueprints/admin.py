from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app import get_db
from utils.decorators import login_required, require_role, csrf_required
from utils.helpers import generate_enrollment_code
from models.course import all_with_teachers, find_by_id, update as update_course
from models.user import all_teachers, all_students
from models.enrollment import enrolled_students, enroll, unenroll
from models.grade_category import for_course as categories_for_course
from models.grade_item import for_course as items_for_course
from models.score import student_scores_for_items

admin_bp = Blueprint('admin', __name__)


@admin_bp.before_request
def load_user():
    g.db = get_db()
    if 'user_id' in session:
        g.user = g.db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
        if not g.user:
            session.clear()
            return redirect(url_for('auth.login'))


@admin_bp.route('/dashboard')
@login_required
@require_role('admin')
def dashboard():
    stats = {
        'students': g.db.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
        'teachers': g.db.execute("SELECT COUNT(*) FROM users WHERE role='teacher'").fetchone()[0],
        'courses': g.db.execute("SELECT COUNT(*) FROM courses").fetchone()[0],
        'enrollments': g.db.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0],
    }
    recent_logs = g.db.execute('''
        SELECT a.*, cb.full_name AS changed_by_name, s.full_name AS student_name,
               gi.item_name, c.course_name
        FROM audit_log a
        JOIN users cb ON a.changed_by=cb.id
        JOIN users s ON a.student_id=s.id
        JOIN grade_items gi ON a.grade_item_id=gi.id
        JOIN grade_categories gc ON gi.category_id=gc.id
        JOIN courses c ON gc.course_id=c.id
        ORDER BY a.changed_at DESC LIMIT 5
    ''').fetchall()
    courses_data = g.db.execute('''
        SELECT c.id, c.course_code, c.course_name, c.credits,
               u.full_name AS teacher_name,
               (SELECT COUNT(*) FROM enrollments e WHERE e.course_id=c.id) AS student_count,
               (SELECT ROUND(AVG(s.score), 1) FROM scores s
                JOIN grade_items gi ON s.grade_item_id=gi.id
                JOIN grade_categories gc ON gi.category_id=gc.id
                WHERE gc.course_id=c.id) AS avg_grade
        FROM courses c
        LEFT JOIN users u ON c.teacher_id=u.id
        ORDER BY c.course_code
    ''').fetchall()
    return render_template('admin/dashboard.html', stats=stats, recent_logs=recent_logs, courses_data=courses_data)


@admin_bp.route('/courses', methods=['GET', 'POST'])
@login_required
@require_role('admin')
@csrf_required
def courses():
    if request.method == 'POST':
        code = request.form.get('course_code', '').strip()
        name = request.form.get('course_name', '').strip()
        credits = request.form.get('credits', 3)
        if not code or not name:
            flash('Course code and name are required.', 'danger')
        else:
            enc = generate_enrollment_code()
            try:
                from models.course import create as create_course
                create_course(code, name, credits, enc)
                flash(f'Course created. Enrollment code: {enc}', 'success')
            except Exception as e:
                flash(f'Error: {e}', 'danger')
        return redirect(url_for('admin.courses'))
    return render_template('admin/courses.html', courses=all_with_teachers(), teachers=all_teachers())


@admin_bp.route('/courses/<int:course_id>/assign', methods=['POST'])
@login_required
@require_role('admin')
@csrf_required
def assign_teacher_route(course_id):
    teacher_id = request.form.get('teacher_id')
    if teacher_id:
        from models.course import assign_teacher
        assign_teacher(course_id, teacher_id)
        flash('Teacher assigned.', 'success')
    return redirect(url_for('admin.courses'))


@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('admin')
@csrf_required
def edit_course(course_id):
    course = find_by_id(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('admin.courses'))
    if request.method == 'POST':
        name = request.form.get('course_name', '').strip()
        credits = request.form.get('credits', 3)
        teacher_id = request.form.get('teacher_id')
        if not name:
            flash('Course name is required.', 'danger')
        else:
            update_course(course_id, name, int(credits))
            g.db.execute("UPDATE courses SET teacher_id=? WHERE id=?", (teacher_id or None, course_id))
            g.db.commit()
            flash('Course updated.', 'success')
            return redirect(url_for('admin.courses'))
    teachers = all_teachers()
    return render_template('admin/edit_course.html', course=course, teachers=teachers)


@admin_bp.route('/courses/<int:course_id>/enrollments', methods=['GET', 'POST'])
@login_required
@require_role('admin')
@csrf_required
def enrollments_route(course_id):
    course = find_by_id(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('admin.courses'))
    if request.method == 'POST':
        student_ids = request.form.getlist('student_ids')
        action = request.form.get('action')
        if action == 'enroll':
            for sid in student_ids:
                enroll(sid, course_id)
            flash('Students enrolled.', 'success')
        elif action == 'unenroll':
            for sid in student_ids:
                unenroll(sid, course_id)
            flash('Students unenrolled.', 'success')
        return redirect(url_for('admin.enrollments_route', course_id=course_id))
    enrolled = enrolled_students(course_id)
    enrolled_ids = [r['id'] for r in enrolled]
    available = [s for s in all_students() if s['id'] not in enrolled_ids]
    cats = categories_for_course(course_id)
    items = items_for_course(course_id)
    grades = {}
    for s in enrolled:
        scores_dict = student_scores_for_items(s['id'], items)
        total = 0.0
        for cat in cats:
            cat_items = [i for i in items if i['category_id'] == cat['id']]
            if cat_items:
                cat_scores = [scores_dict[i['id']] for i in cat_items if scores_dict.get(i['id']) is not None]
                if cat_scores:
                    cat_avg = sum(cat_scores) / len(cat_scores)
                    total += cat_avg * (cat['weight'] / 100.0)
        grades[s['id']] = round(total, 1)
    return render_template('admin/enrollments.html', course=course, enrolled=enrolled, available=available, grades=grades)


@admin_bp.route('/audit-log')
@login_required
@require_role('admin')
def audit_log():
    course_filter = request.args.get('course_id', '')
    teacher_filter = request.args.get('teacher_id', '')

    query = '''
        SELECT a.*, cb.full_name AS changed_by_name, s.full_name AS student_name,
               gi.item_name, c.course_name, c.id AS course_id_val,
               gc.category_name
        FROM audit_log a
        JOIN users cb ON a.changed_by=cb.id
        JOIN users s ON a.student_id=s.id
        JOIN grade_items gi ON a.grade_item_id=gi.id
        JOIN grade_categories gc ON gi.category_id=gc.id
        JOIN courses c ON gc.course_id=c.id
        WHERE 1=1
    '''
    params = []
    if course_filter:
        query += ' AND c.id=?'
        params.append(course_filter)
    if teacher_filter:
        query += ' AND cb.id=?'
        params.append(teacher_filter)
    query += ' ORDER BY a.changed_at DESC'

    logs = g.db.execute(query, params).fetchall()

    courses = g.db.execute("SELECT id, course_code, course_name FROM courses ORDER BY course_code").fetchall()
    teachers = g.db.execute("SELECT id, full_name FROM users WHERE role='teacher' ORDER BY full_name").fetchall()
    return render_template('admin/audit_log.html', logs=logs, courses=courses,
                           teachers=teachers, course_filter=course_filter,
                           teacher_filter=teacher_filter)
