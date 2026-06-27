from collections.abc import Sequence
from models._common import get_conn


def for_course(course_id: int) -> Sequence[dict]:
    db = get_conn()
    return db.execute('''
        SELECT gi.* FROM grade_items gi
        JOIN grade_categories gc ON gi.category_id=gc.id
        WHERE gc.course_id=? ORDER BY gi.id
    ''', (course_id,)).fetchall()


def for_category(category_id: int) -> Sequence[dict]:
    db = get_conn()
    return db.execute("SELECT * FROM grade_items WHERE category_id=? ORDER BY id", (category_id,)).fetchall()


def find_by_id(item_id: int) -> dict | None:
    db = get_conn()
    return db.execute("SELECT * FROM grade_items WHERE id=?", (item_id,)).fetchone()


def create(category_id: int, item_name: str, max_score: float = 100) -> None:
    db = get_conn()
    db.execute("INSERT INTO grade_items (category_id,item_name,max_score) VALUES (?,?,?)",
               (category_id, item_name, max_score))
    db.commit()


def update(item_id: int, item_name: str, max_score: float) -> None:
    db = get_conn()
    db.execute("UPDATE grade_items SET item_name=?, max_score=? WHERE id=?", (item_name, max_score, item_id))
    db.commit()


def delete(item_id: int) -> None:
    db = get_conn()
    db.execute("DELETE FROM grade_items WHERE id=?", (item_id,))
    db.commit()


def has_scores(item_id: int) -> bool:
    db = get_conn()
    row = db.execute("SELECT 1 FROM scores WHERE grade_item_id=? LIMIT 1", (item_id,)).fetchone()
    return row is not None


def item_name_exists(category_id: int, item_name: str, exclude_id: int | None = None) -> bool:
    db = get_conn()
    query = "SELECT 1 FROM grade_items WHERE category_id=? AND item_name=?"
    params = [category_id, item_name]
    if exclude_id:
        query += " AND id!=?"
        params.append(exclude_id)
    return db.execute(query, params).fetchone() is not None
