from collections.abc import Sequence
from models._common import get_conn


def enrolled_students(course_id: int) -> Sequence[dict]:
    db = get_conn()
    return db.execute('''
        SELECT u.id, u.full_name, u.username, e.enrolled_at
        FROM users u JOIN enrollments e ON u.id=e.student_id
        WHERE e.course_id=? ORDER BY u.full_name
    ''', (course_id,)).fetchall()


def is_enrolled(student_id: int, course_id: int) -> bool:
    db = get_conn()
    return db.execute("SELECT 1 FROM enrollments WHERE student_id=? AND course_id=?", (student_id, course_id)).fetchone() is not None


def enroll(student_id: int, course_id: int) -> None:
    db = get_conn()
    db.execute("INSERT OR IGNORE INTO enrollments (student_id,course_id) VALUES (?,?)", (student_id, course_id))
    db.commit()


def unenroll(student_id: int, course_id: int) -> None:
    db = get_conn()
    db.execute("DELETE FROM enrollments WHERE student_id=? AND course_id=?", (student_id, course_id))
    db.commit()
