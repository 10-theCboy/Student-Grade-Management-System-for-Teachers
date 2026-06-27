from collections.abc import Sequence
from flask import g
from app import get_db
from models._common import get_conn


def find_by_username(username: str) -> dict | None:
    db = get_conn()
    return db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()


def find_by_id(user_id: int) -> dict | None:
    db = get_conn()
    return db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()


def find_by_email(email: str) -> dict | None:
    db = get_conn()
    return db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()


def all_students() -> Sequence[dict]:
    db = get_conn()
    return db.execute("SELECT * FROM users WHERE role='student' ORDER BY full_name").fetchall()


def all_teachers() -> Sequence[dict]:
    db = get_conn()
    return db.execute("SELECT * FROM users WHERE role='teacher' ORDER BY full_name").fetchall()
