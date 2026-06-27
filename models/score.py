from collections.abc import Sequence
from models._common import get_conn


def find(student_id: int, grade_item_id: int) -> dict | None:
    db = get_conn()
    return db.execute("SELECT * FROM scores WHERE student_id=? AND grade_item_id=?", (student_id, grade_item_id)).fetchone()


def upsert(student_id: int, grade_item_id: int, score: float) -> float | None:
    db = get_conn()
    old = db.execute("SELECT score FROM scores WHERE student_id=? AND grade_item_id=?", (student_id, grade_item_id)).fetchone()
    old_val = old['score'] if old else None
    if old:
        db.execute("UPDATE scores SET score=? WHERE student_id=? AND grade_item_id=?", (score, student_id, grade_item_id))
    else:
        db.execute("INSERT INTO scores (student_id,grade_item_id,score) VALUES (?,?,?)", (student_id, grade_item_id, score))
    db.commit()
    return old_val


def student_scores_for_items(student_id: int, items: Sequence[dict]) -> dict[int, float | None]:
    if not items:
        return {}
    db = get_conn()
    item_ids = [item['id'] for item in items]
    placeholders = ','.join('?' * len(item_ids))
    rows = db.execute(
        f"SELECT grade_item_id, score FROM scores WHERE student_id=? AND grade_item_id IN ({placeholders})",
        [student_id] + item_ids
    ).fetchall()
    result = {item['id']: None for item in items}
    for row in rows:
        result[row['grade_item_id']] = row['score']
    return result
