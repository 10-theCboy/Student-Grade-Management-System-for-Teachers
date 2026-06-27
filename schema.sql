CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin','teacher','student')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL,
    credits INTEGER NOT NULL,
    teacher_id INTEGER REFERENCES users(id),
    enrollment_code TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES users(id),
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id)
);

CREATE TABLE IF NOT EXISTS grade_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    category_name TEXT NOT NULL,
    weight REAL NOT NULL CHECK(weight >= 0 AND weight <= 100)
);

CREATE TABLE IF NOT EXISTS grade_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES grade_categories(id) ON DELETE CASCADE,
    item_name TEXT NOT NULL,
    max_score REAL DEFAULT 100
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES users(id),
    grade_item_id INTEGER NOT NULL REFERENCES grade_items(id) ON DELETE CASCADE,
    score REAL CHECK(score >= 0 AND score <= 100),
    entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, grade_item_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    changed_by INTEGER NOT NULL REFERENCES users(id),
    student_id INTEGER NOT NULL REFERENCES users(id),
    grade_item_id INTEGER NOT NULL REFERENCES grade_items(id),
    old_score REAL,
    new_score REAL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
