import csv
import io
from datetime import date
from flask import Response
from models.enrollment import enrolled_students
from models.grade_item import for_course as items_for_course
from models.score import student_scores_for_items
from services.grade_service import calculate_weighted_average, letter_grade


def generate_csv(course_id: int) -> Response | None:
    from models.course import find_by_id
    course = find_by_id(course_id)
    if not course:
        return None

    students = enrolled_students(course_id)
    items = items_for_course(course_id)

    has_any = False
    for s in students:
        scores_dict = student_scores_for_items(s['id'], items)
        if any(v is not None for v in scores_dict.values()):
            has_any = True
            break
    if not has_any:
        return None

    output = io.StringIO()
    writer = csv.writer(output)
    header = ['Student ID', 'Full Name']
    for item in items:
        header.append(item['item_name'])
    header += ['Weighted Average', 'Letter Grade']
    writer.writerow(header)

    for s in students:
        scores_dict = student_scores_for_items(s['id'], items)
        row = [s['username'], s['full_name']]
        for item in items:
            val = scores_dict.get(item['id'])
            row.append(val if val is not None else '')
        avg = calculate_weighted_average(s['id'], course_id)
        row += [avg, letter_grade(avg)]
        writer.writerow(row)

    output.seek(0)
    today = date.today().isoformat()
    filename = f'grades_{course["course_code"]}_{today}.csv'
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={filename}'})
