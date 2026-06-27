from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app import get_db
from utils.decorators import login_required, require_role, csrf_required
from models.course import find_by_id, find_by_teacher
from models.grade_category import for_course as categories_for_course, find_by_id as find_category, create as create_category, update as update_category, delete as delete_category, total_weight, has_scores
from models.grade_item import for_course as items_for_course, for_category as items_for_category, find_by_id as find_item, create as create_item, delete as delete_item, has_scores as item_has_scores, item_name_exists
from models.score import upsert as upsert_score, student_scores_for_items
from services.grade_service import calculate_weighted_average, letter_grade
from services.report_service import generate_csv
from services.statistics_service import class_statistics
from models.enrollment import enrolled_students
from models.audit_log import log as audit_log

teacher_bp = Blueprint('teacher', __name__)

def track_course_access(course_id):
    recent = session.get('recent_courses', [])
    if course_id in recent:
        recent.remove(course_id)
    recent.insert(0, course_id)
    session['recent_courses'] = recent[:5]

    freq = session.get('freq_courses', {})
    freq[str(course_id)] = freq.get(str(course_id), 0) + 1
    session['freq_courses'] = freq


@teacher_bp.before_request
def load_user():
    g.db = get_db()
    if 'user_id' in session:
        g.user = g.db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
        if not g.user:
            session.clear()
            return redirect(url_for('auth.login'))


@teacher_bp.route('/dashboard')
@login_required
@require_role('teacher')
def dashboard():
    courses = find_by_teacher(g.user['id'])
    all_student_ids = set()
    for c in courses:
        rows = g.db.execute("SELECT student_id FROM enrollments WHERE course_id=?", (c['id'],)).fetchall()
        all_student_ids.update(r['student_id'] for r in rows)
    unique_students = len(all_student_ids)
    failing = 0
    for sid in all_student_ids:
        for c in courses:
            avg = calculate_weighted_average(sid, c['id'])
            if avg and avg < 60:
                failing += 1
                break
    totals = []
    for c in courses:
        enrolled = g.db.execute(
            "SELECT student_id FROM enrollments WHERE course_id=?", (c['id'],)
        ).fetchall()
        for r in enrolled:
            avg = calculate_weighted_average(r['student_id'], c['id'])
            if avg:
                totals.append(avg)
    class_avg = round(sum(totals) / len(totals), 1) if totals else 0
    course_stats = {}
    for c in courses:
        enrolled = g.db.execute(
            "SELECT student_id FROM enrollments WHERE course_id=?", (c['id'],)
        ).fetchall()
        enrolled_ids = [r['student_id'] for r in enrolled]
        course_totals = [calculate_weighted_average(sid, c['id']) for sid in enrolled_ids]
        course_totals = [t for t in course_totals if t]
        course_avg = round(sum(course_totals) / len(course_totals), 1) if course_totals else None
        course_stats[c['id']] = {
            'avg': course_avg,
            'enrolled': len(enrolled_ids)
        }
    stats = {
        'course_count': len(courses),
        'student_count': unique_students,
        'failing': failing,
        'class_avg': class_avg,
    }
    course_map = {c['id']: c for c in courses}
    recent_ids = session.get('recent_courses', [])
    recent_courses = [course_map[cid] for cid in recent_ids if cid in course_map]
    freq_raw = session.get('freq_courses', {})
    freq_sorted = sorted(freq_raw.items(), key=lambda x: -x[1])
    freq_courses = [(course_map[int(cid)], count) for cid, count in freq_sorted if int(cid) in course_map]
    return render_template('teacher/dashboard.html', courses=courses, stats=stats, course_stats=course_stats, recent_courses=recent_courses, freq_courses=freq_courses)


@teacher_bp.route('/courses/<int:course_id>/categories', methods=['GET', 'POST'])
@login_required
@require_role('teacher')
@csrf_required
def categories(course_id):
    course = find_by_id(course_id)
    if not course or course['teacher_id'] != g.user['id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.dashboard'))
    track_course_access(course_id)
    locked = has_scores(course_id)
    if request.method == 'POST':
        action = request.form.get('action', 'add')
        if locked and action in ('add', 'edit', 'delete'):
            flash('Grades have already been entered for this course. Categories are locked.', 'danger')
            return redirect(url_for('teacher.categories', course_id=course_id))

        if action == 'add':
            name = request.form.get('category_name', '').strip()
            weight = request.form.get('weight', 0)
            if not name or not weight:
                flash('Category name and weight are required.', 'danger')
            else:
                try:
                    weight = float(weight)
                    if weight < 0 or weight > 100:
                        flash('Weight must be between 0 and 100.', 'danger')
                    elif total_weight(course_id) + weight > 100:
                        flash(f'Total weight would exceed 100% (currently {total_weight(course_id):.0f}%).', 'danger')
                    else:
                        create_category(course_id, name, weight)
                        flash('Category added.', 'success')
                except (ValueError, TypeError):
                    flash('Weight must be a number.', 'danger')

        elif action == 'edit':
            cat_id = request.form.get('cat_id')
            name = request.form.get('category_name', '').strip()
            weight = request.form.get('weight', 0)
            cat = find_category(cat_id) if cat_id else None
            if not cat or cat['course_id'] != course_id:
                flash('Category not found.', 'danger')
            elif not name or not weight:
                flash('Category name and weight are required.', 'danger')
            else:
                try:
                    weight = float(weight)
                    if weight < 0 or weight > 100:
                        flash('Weight must be between 0 and 100.', 'danger')
                    elif total_weight(course_id) - cat['weight'] + weight > 100:
                        flash(f'Total weight would exceed 100% (currently {total_weight(course_id):.0f}%).', 'danger')
                    else:
                        update_category(cat_id, name, weight)
                        flash('Category updated.', 'success')
                except (ValueError, TypeError):
                    flash('Weight must be a number.', 'danger')

        elif action == 'delete':
            cat_id = request.form.get('cat_id')
            cat = find_category(cat_id) if cat_id else None
            if not cat or cat['course_id'] != course_id:
                flash('Category not found.', 'danger')
            else:
                delete_category(cat_id)
                flash('Category deleted.', 'success')

        elif action == 'add_item':
            cat_id = request.form.get('cat_id')
            cat = find_category(cat_id) if cat_id else None
            name = request.form.get('item_name', '').strip()
            max_score = request.form.get('max_score', 100)
            if not cat or cat['course_id'] != course_id:
                flash('Category not found.', 'danger')
            elif not name:
                flash('Item name is required.', 'danger')
            elif item_name_exists(cat_id, name):
                flash(f'Item name "{name}" already exists in this category.', 'danger')
            else:
                try:
                    create_item(cat_id, name, float(max_score))
                    flash('Item added.', 'success')
                except (ValueError, TypeError):
                    flash('Max score must be a number.', 'danger')

        elif action == 'delete_item':
            item_id = request.form.get('item_id')
            item = find_item(item_id) if item_id else None
            if not item:
                flash('Item not found.', 'danger')
            elif item_has_scores(item_id):
                flash('Cannot delete item: scores have already been entered for it.', 'danger')
            else:
                delete_item(item_id)
                flash('Item deleted.', 'success')

        return redirect(url_for('teacher.categories', course_id=course_id))
    cats = categories_for_course(course_id)
    items_by_cat = {}
    for cat in cats:
        items_by_cat[cat['id']] = items_for_category(cat['id'])
    return render_template('teacher/categories.html', course=course, categories=cats, items_by_cat=items_by_cat, total_weight=total_weight(course_id), locked=locked)


@teacher_bp.route('/courses/<int:course_id>/grades', methods=['GET', 'POST'])
@login_required
@require_role('teacher')
@csrf_required
def grades(course_id):
    course = find_by_id(course_id)
    if not course or course['teacher_id'] != g.user['id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.dashboard'))
    track_course_access(course_id)
    if request.method == 'POST':
        errors = []
        saved = 0
        for key, val in request.form.items():
            if not key.startswith('score_'):
                continue
            parts = key.split('_')
            if len(parts) != 3:
                continue
            _, sid_str, iid_str = parts
            val = val.strip()
            if val == '':
                continue
            try:
                score_val = float(val)
            except (ValueError, TypeError):
                errors.append(f'Score for item #{iid_str}: not a number.')
                continue
            if score_val < 0 or score_val > 100:
                errors.append(f'Score for item #{iid_str}: must be 0–100.')
                continue
            old_score = upsert_score(sid_str, iid_str, score_val)
            audit_log(g.user['id'], sid_str, iid_str, old_score, score_val)
            saved += 1
        students_affected = set()
        for key in request.form:
            if key.startswith('score_'):
                parts = key.split('_')
                if len(parts) == 3:
                    students_affected.add(int(parts[1]))
        for sid in students_affected:
            calculate_weighted_average(sid, course_id)
        if errors:
            for e in errors:
                flash(e, 'danger')
        if saved:
            flash(f'{saved} score(s) saved.', 'success')
        if not saved and not errors:
            flash('No scores submitted.', 'info')
        return redirect(url_for('teacher.grades', course_id=course_id))
    students = enrolled_students(course_id)
    cats = categories_for_course(course_id)
    items = items_for_course(course_id)
    scores = {}
    averages = {}
    grades_map = {}
    for s in students:
        scores[s['id']] = student_scores_for_items(s['id'], items)
        avg = calculate_weighted_average(s['id'], course_id)
        averages[s['id']] = avg
        grades_map[s['id']] = letter_grade(avg)
    return render_template('teacher/grades.html', course=course, students=students, categories=cats, items=items, scores=scores, averages=averages, grades_map=grades_map)


@teacher_bp.route('/courses/<int:course_id>/report')
@login_required
@require_role('teacher')
def report(course_id):
    course = find_by_id(course_id)
    if not course or course['teacher_id'] != g.user['id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.dashboard'))
    track_course_access(course_id)
    stats = class_statistics(course_id)
    return render_template('teacher/report.html', course=course, **stats)


@teacher_bp.route('/courses/<int:course_id>/export/confirm')
@login_required
@require_role('teacher')
def export_confirm(course_id):
    course = find_by_id(course_id)
    if not course or course['teacher_id'] != g.user['id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.dashboard'))
    track_course_access(course_id)
    from models.enrollment import enrolled_students
    from models.grade_category import for_course as categories_for_course
    from models.grade_item import for_course as items_for_course
    stats = class_statistics(course_id)
    cats = categories_for_course(course_id)
    items = items_for_course(course_id)
    students = enrolled_students(course_id)
    return render_template('teacher/export_confirm.html', course=course,
                           num_students=len(students), num_categories=len(cats),
                           num_items=len(items), class_avg=stats['avg'])


@teacher_bp.route('/courses/<int:course_id>/export')
@login_required
@require_role('teacher')
def export(course_id):
    course = find_by_id(course_id)
    if not course or course['teacher_id'] != g.user['id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.dashboard'))
    result = generate_csv(course_id)
    if result is None:
        flash('No scores have been entered for this course yet. Export cancelled.', 'warning')
        return redirect(url_for('teacher.report', course_id=course_id))
    return result
