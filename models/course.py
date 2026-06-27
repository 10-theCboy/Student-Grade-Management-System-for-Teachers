from collections.abc import Sequence
from models._common import get_conn


def create(course_code: str, course_name: str, credits: int, enrollment_code: str) -> None:
    db = get_conn()
    db.execute("INSERT INTO courses (course_code,course_name,credits,enrollment_code) VALUES (?,?,?,?)",
               (course_code, course_name, credits, enrollment_code))
    db.commit()


def find_by_enrollment_code(code: str) -> dict | None:
    db = get_conn()
    return db.execute("SELECT * FROM courses WHERE enrollment_code=?", (code,)).fetchone()


def all_with_teachers() -> Sequence[dict]:
    db = get_conn()
    return db.execute('''
        SELECT c.*, u.full_name AS teacher_name
        FROM courses c LEFT JOIN users u ON c.teacher_id=u.id
        ORDER BY c.course_code
    ''').fetchall()


def find_by_id(course_id: int) -> dict | None:
    db = get_conn()
    return db.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()


def assign_teacher(course_id: int, teacher_id: int) -> None:
    db = get_conn()
    db.execute("UPDATE courses SET teacher_id=? WHERE id=?", (teacher_id, course_id))
    db.commit()


def find_by_teacher(teacher_id: int) -> Sequence[dict]:
    db = get_conn()
    return db.execute("SELECT * FROM courses WHERE teacher_id=? ORDER BY course_code", (teacher_id,)).fetchall()


def find_by_student(student_id: int) -> Sequence[dict]:
    db = get_conn()
    return db.execute('''
        SELECT c.*, u.full_name AS teacher_name
        FROM courses c
        JOIN enrollments e ON c.id=e.course_id
        LEFT JOIN users u ON c.teacher_id=u.id
        WHERE e.student_id=? ORDER BY c.course_code
    ''', (student_id,)).fetchall()


def update(course_id: int, course_name: str, credits: int) -> None:
    db = get_conn()
    db.execute("UPDATE courses SET course_name=?, credits=? WHERE id=?", (course_name, credits, course_id))
    db.commit()
