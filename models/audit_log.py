from models._common import get_conn


def log(changed_by: int, student_id: int, grade_item_id: int, old_score: float | None, new_score: float) -> None:
    db = get_conn()
    db.execute(
        "INSERT INTO audit_log (changed_by,student_id,grade_item_id,old_score,new_score) VALUES (?,?,?,?,?)",
        (changed_by, student_id, grade_item_id, old_score, new_score))
    db.commit()
