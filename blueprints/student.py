from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify
from app import get_db
from utils.decorators import login_required, require_role
from models.course import find_by_student, find_by_id
from models.enrollment import is_enrolled
from models.grade_category import for_course as categories_for_course
from models.grade_item import for_course as items_for_course
from models.score import student_scores_for_items
from services.grade_service import calculate_weighted_average, letter_grade

student_bp = Blueprint('student', __name__)


@student_bp.before_request
def load_user():
    g.db = get_db()
    if 'user_id' in session:
        g.user = g.db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
        if not g.user:
            session.clear()
            return redirect(url_for('auth.login'))


@student_bp.route('/dashboard')
@login_required
@require_role('student')
def dashboard():
    courses = find_by_student(g.user['id'])
    course_data = []
    for c in courses:
        avg = calculate_weighted_average(g.user['id'], c['id'])
        course_data.append({
            'course': c,
            'average': avg,
            'grade': letter_grade(avg),
            'progress': min(avg, 100) if avg > 0 else 0
        })
    return render_template('student/dashboard.html', course_data=course_data)


@student_bp.route('/api/courses/<int:course_id>/detail')
@login_required
@require_role('student')
def course_api_detail(course_id):
    if not is_enrolled(g.user['id'], course_id):
        return jsonify({'error': 'Not enrolled'}), 403

    course = find_by_id(course_id)
    cats = categories_for_course(course_id)
    items = items_for_course(course_id)
    scores = student_scores_for_items(g.user['id'], items)

    total = calculate_weighted_average(g.user['id'], course_id)
    letter = letter_grade(total)

    enrolled_ids = [r['id'] for r in g.db.execute(
        "SELECT id FROM enrollments WHERE course_id=?", (course_id,)
    ).fetchall()]

    class_avg_per_item = {}
    if enrolled_ids:
        placeholders = ','.join('?' * len(enrolled_ids))
        for item in items:
            rows = g.db.execute(
                f"SELECT score FROM scores WHERE student_id IN ({placeholders}) AND grade_item_id=?",
                enrolled_ids + [item['id']]
            ).fetchall()
            vals = [r['score'] for r in rows if r['score'] is not None]
            class_avg_per_item[item['id']] = round(sum(vals) / len(vals), 1) if vals else None

    cat_details = []
    for cat in cats:
        cat_items = [i for i in items if i['category_id'] == cat['id']]
        cat_scores = [scores[i['id']] for i in cat_items if scores.get(i['id']) is not None]
        if cat_scores:
            cat_avg = sum(cat_scores) / len(cat_scores)
            weighted = cat_avg * (cat['weight'] / 100.0)
            cat_details.append({
                'id': cat['id'], 'name': cat['category_name'], 'weight': cat['weight'],
                'avg': round(cat_avg, 1), 'weighted': round(weighted, 1),
                'items': [{
                    'id': i['id'], 'name': i['item_name'], 'max': i['max_score'],
                    'score': scores.get(i['id']), 'classAvg': class_avg_per_item.get(i['id'])
                } for i in cat_items]
            })
        else:
            cat_details.append({
                'id': cat['id'], 'name': cat['category_name'], 'weight': cat['weight'],
                'avg': None, 'weighted': None,
                'items': [{
                    'id': i['id'], 'name': i['item_name'], 'max': i['max_score'],
                    'score': scores.get(i['id']), 'classAvg': class_avg_per_item.get(i['id'])
                } for i in cat_items]
            })

    klass_avg = 0
    if enrolled_ids:
        totals = [calculate_weighted_average(sid, course_id) for sid in enrolled_ids]
        klass_avg = round(sum(totals) / len(totals), 1)

    return jsonify({
        'categories': cat_details,
        'total': total,
        'grade': letter,
        'classAvg': klass_avg,
        'progress': min(total, 100) if total > 0 else 0
    })


@student_bp.route('/courses/<int:course_id>/grades')
@login_required
@require_role('student')
def course_grades(course_id):
    if not is_enrolled(g.user['id'], course_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('student.dashboard'))

    course = find_by_id(course_id)
    cats = categories_for_course(course_id)
    items = items_for_course(course_id)
    scores = student_scores_for_items(g.user['id'], items)

    total = calculate_weighted_average(g.user['id'], course_id)
    letter = letter_grade(total)

    enrolled_ids = [r['id'] for r in g.db.execute(
        "SELECT id FROM enrollments WHERE course_id=?", (course_id,)
    ).fetchall()]

    class_avg_per_item = {}
    if enrolled_ids:
        placeholders = ','.join('?' * len(enrolled_ids))
        for item in items:
            rows = g.db.execute(
                f"SELECT score FROM scores WHERE student_id IN ({placeholders}) AND grade_item_id=?",
                enrolled_ids + [item['id']]
            ).fetchall()
            vals = [r['score'] for r in rows if r['score'] is not None]
            class_avg_per_item[item['id']] = round(sum(vals) / len(vals), 1) if vals else None

    cat_details = []
    for cat in cats:
        cat_items = [i for i in items if i['category_id'] == cat['id']]
        cat_scores = [scores[i['id']] for i in cat_items if scores.get(i['id']) is not None]
        if cat_scores:
            cat_avg = sum(cat_scores) / len(cat_scores)
            weighted = cat_avg * (cat['weight'] / 100.0)
            cat_details.append({'name': cat['category_name'], 'weight': cat['weight'],
                                'avg': round(cat_avg, 1), 'weighted': round(weighted, 1)})
        else:
            cat_details.append({'name': cat['category_name'], 'weight': cat['weight'],
                                'avg': None, 'weighted': None})

    klass_avg = 0
    if enrolled_ids:
        totals = [calculate_weighted_average(sid, course_id) for sid in enrolled_ids]
        klass_avg = round(sum(totals) / len(totals), 1)

    return render_template('student/grades.html', course=course, cats=cats, items=items, scores=scores,
                           cat_details=cat_details, total=total, letter=letter,
                           klass_avg=klass_avg, class_avg_per_item=class_avg_per_item)
