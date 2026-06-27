from collections.abc import Sequence
from models._common import get_conn
from models.grade_category import for_course as cats_for


def calculate_weighted_average(student_id: int, course_id: int) -> float:
    cats = cats_for(course_id)
    if not cats:
        return 0.0

    cat_ids = [cat['id'] for cat in cats]
    db = get_conn()

    cat_placeholders = ','.join('?' * len(cat_ids))
    items_rows = db.execute(
        f"SELECT gi.*, gc.id AS cat_id FROM grade_items gi "
        f"JOIN grade_categories gc ON gi.category_id=gc.id "
        f"WHERE gc.id IN ({cat_placeholders}) ORDER BY gi.id",
        cat_ids
    ).fetchall()

    items_by_cat: dict[int, list[dict]] = {cat['id']: [] for cat in cats}
    for row in items_rows:
        items_by_cat[row['cat_id']].append(dict(row))

    from models.score import student_scores_for_items

    total = 0.0
    for cat in cats:
        items = items_by_cat.get(cat['id'], [])
        if not items:
            continue
        scores_dict = student_scores_for_items(student_id, items)
        cat_vals = [v for v in scores_dict.values() if v is not None]
        if cat_vals:
            cat_avg = sum(cat_vals) / len(cat_vals)
            total += cat_avg * (cat['weight'] / 100.0)
    return round(total, 1)


def letter_grade(weighted_average: float) -> str:
    if weighted_average >= 90:
        return 'A'
    if weighted_average >= 80:
        return 'B'
    if weighted_average >= 70:
        return 'C'
    if weighted_average >= 60:
        return 'D'
    return 'F'
