from collections.abc import Sequence
from models._common import get_conn


def for_course(course_id: int) -> Sequence[dict]:
    db = get_conn()
    return db.execute("SELECT * FROM grade_categories WHERE course_id=? ORDER BY id", (course_id,)).fetchall()


def find_by_id(cat_id: int) -> dict | None:
    db = get_conn()
    return db.execute("SELECT * FROM grade_categories WHERE id=?", (cat_id,)).fetchone()


def create(course_id: int, name: str, weight: float) -> None:
    db = get_conn()
    db.execute("INSERT INTO grade_categories (course_id,category_name,weight) VALUES (?,?,?)",
               (course_id, name, weight))
    db.commit()


def update(cat_id: int, name: str, weight: float) -> None:
    db = get_conn()
    db.execute("UPDATE grade_categories SET category_name=?, weight=? WHERE id=?", (name, weight, cat_id))
    db.commit()


def delete(cat_id: int) -> None:
    db = get_conn()
    db.execute("DELETE FROM grade_categories WHERE id=?", (cat_id,))
    db.commit()


def total_weight(course_id: int) -> float:
    db = get_conn()
    row = db.execute("SELECT COALESCE(SUM(weight),0) FROM grade_categories WHERE course_id=?", (course_id,)).fetchone()
    return row[0]


def has_scores(course_id: int) -> bool:
    db = get_conn()
    row = db.execute('''
        SELECT 1 FROM scores s
        JOIN grade_items gi ON s.grade_item_id=gi.id
        JOIN grade_categories gc ON gi.category_id=gc.id
        WHERE gc.course_id=? LIMIT 1
    ''', (course_id,)).fetchone()
    return row is not None
