import os
import random
import sqlite3


def init_test_db(path: str):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    schema = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    with open(schema, 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    db.commit()

    from app import bcrypt
    pw = lambda p: bcrypt.generate_password_hash(p).decode('utf-8')

    db.execute("INSERT INTO users (username,password_hash,full_name,email,role) VALUES (?,?,?,?,?)",
               ('admin', pw('admin123'), 'Admin', 'admin@test.com', 'admin'))
    db.execute("INSERT INTO users (username,password_hash,full_name,email,role) VALUES (?,?,?,?,?)",
               ('teacher1', pw('teacher123'), 'Dr. A', 't1@test.com', 'teacher'))
    db.execute("INSERT INTO users (username,password_hash,full_name,email,role) VALUES (?,?,?,?,?)",
               ('teacher2', pw('teacher123'), 'Dr. B', 't2@test.com', 'teacher'))
    db.execute("INSERT INTO users (username,password_hash,full_name,email,role) VALUES (?,?,?,?,?)",
               ('L20261001', pw('student123'), 'Student 1', 's1@test.com', 'student'))
    db.execute("INSERT INTO users (username,password_hash,full_name,email,role) VALUES (?,?,?,?,?)",
               ('L20261002', pw('student123'), 'Student 2', 's2@test.com', 'student'))

    t1 = db.execute("SELECT id FROM users WHERE username='teacher1'").fetchone()['id']
    t2 = db.execute("SELECT id FROM users WHERE username='teacher2'").fetchone()['id']
    s1 = db.execute("SELECT id FROM users WHERE username='L20261001'").fetchone()['id']
    s2 = db.execute("SELECT id FROM users WHERE username='L20261002'").fetchone()['id']

    db.execute("INSERT INTO courses (course_code,course_name,credits,teacher_id,enrollment_code) VALUES (?,?,?,?,?)",
               ('CS101', 'Test Course', 3, t1, 'AAAA'))
    db.execute("INSERT INTO courses (course_code,course_name,credits,teacher_id,enrollment_code) VALUES (?,?,?,?,?)",
               ('CS201', 'Other Course', 3, t2, 'BBBB'))

    c1 = db.execute("SELECT id FROM courses WHERE course_code='CS101'").fetchone()['id']
    c2 = db.execute("SELECT id FROM courses WHERE course_code='CS201'").fetchone()['id']

    db.execute("INSERT INTO enrollments (student_id,course_id) VALUES (?,?)", (s1, c1))
    db.execute("INSERT INTO enrollments (student_id,course_id) VALUES (?,?)", (s2, c1))
    db.execute("INSERT INTO enrollments (student_id,course_id) VALUES (?,?)", (s1, c2))

    db.execute("INSERT INTO grade_categories (course_id,category_name,weight) VALUES (?,?,?)", (c1, 'Assignments', 40))
    db.execute("INSERT INTO grade_categories (course_id,category_name,weight) VALUES (?,?,?)", (c1, 'Final', 60))

    c1_cats = db.execute("SELECT id FROM grade_categories WHERE course_id=?", (c1,)).fetchall()
    for cat in c1_cats:
        for j in range(1, 3):
            db.execute("INSERT INTO grade_items (category_id,item_name,max_score) VALUES (?,?,?)",
                       (cat['id'], f'Item {j}', 100))

    items = db.execute(
        "SELECT gi.id FROM grade_items gi JOIN grade_categories gc ON gi.category_id=gc.id WHERE gc.course_id=?",
        (c1,)).fetchall()
    score_vals = [85.0, 90.0, 95.0, 100.0]
    for i, item in enumerate(items):
        db.execute("INSERT INTO scores (student_id,grade_item_id,score) VALUES (?,?,?)",
                   (s1, item['id'], score_vals[i]))
    for item in items[:2]:
        db.execute("INSERT INTO scores (student_id,grade_item_id,score) VALUES (?,?,?)",
                   (s2, item['id'], 50.0))

    db.commit()
    db.close()
