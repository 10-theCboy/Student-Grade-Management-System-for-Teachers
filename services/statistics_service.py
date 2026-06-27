from models.enrollment import enrolled_students
from models.grade_item import for_course as items_for_course
from models.score import student_scores_for_items
from services.grade_service import calculate_weighted_average


def class_statistics(course_id: int) -> dict:
    students = enrolled_students(course_id)
    items = items_for_course(course_id)
    if not students:
        return {'avg': 0, 'highest': 0, 'lowest': 0, 'failing': 0, 'bins': [0]*5, 'labels': [], 'failing_students': []}

    grade_data = []
    for s in students:
        total = calculate_weighted_average(s['id'], course_id)
        scores_dict = student_scores_for_items(s['id'], items)
        missing = [i for i in items if scores_dict.get(i['id']) is None or scores_dict[i['id']] == 0]
        grade_data.append({'student': s, 'total': total, 'missing_items': missing})

    totals = [gd['total'] for gd in grade_data]
    avg = round(sum(totals) / len(totals), 1) if totals else 0
    highest = max(totals) if totals else 0
    lowest = min(totals) if totals else 0
    num_failing = sum(1 for t in totals if t < 60)

    labels = ['F (0-59)', 'D (60-69)', 'C (70-79)', 'B (80-89)', 'A (90-100)']
    bins = [0] * 5
    for t in totals:
        idx = 4 if t >= 90 else 3 if t >= 80 else 2 if t >= 70 else 1 if t >= 60 else 0
        bins[idx] += 1

    failing_students = [gd for gd in grade_data if gd['total'] < 60]

    return {
        'avg': avg, 'highest': highest, 'lowest': lowest,
        'failing': num_failing, 'bins': bins, 'labels': labels,
        'failing_students': failing_students, 'grade_data': grade_data
    }
