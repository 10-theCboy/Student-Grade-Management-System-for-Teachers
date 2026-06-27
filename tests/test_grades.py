"""
Grade service, validation, weighted average, CSV export, and statistics tests.
TC-GRADE-001 through TC-GRADE-013
"""
import csv
import io
import sqlite3
import os


def get_db():
    return sqlite3.connect(os.environ['TEST_DB_PATH'])


def get_course_id(conn, code='CS101'):
    return conn.execute(
        "SELECT id FROM courses WHERE course_code=?", (code,)
    ).fetchone()[0]


def get_student_id(conn, username='L20261001'):
    return conn.execute(
        "SELECT id FROM users WHERE username=?", (username,)
    ).fetchone()[0]


# ── Letter grade boundary tests ──────────────────────────────────────────────

def test_letter_grade_A():
    """TC-GRADE-001: Scores 90–100 return letter grade A."""
    from services.grade_service import letter_grade
    assert letter_grade(95) == 'A'
    assert letter_grade(90) == 'A'


def test_letter_grade_B():
    """TC-GRADE-002: Scores 80–89 return letter grade B."""
    from services.grade_service import letter_grade
    assert letter_grade(85) == 'B'
    assert letter_grade(80) == 'B'


def test_letter_grade_C():
    """TC-GRADE-003: Scores 70–79 return letter grade C."""
    from services.grade_service import letter_grade
    assert letter_grade(75) == 'C'
    assert letter_grade(70) == 'C'


def test_letter_grade_D():
    """TC-GRADE-004: Scores 60–69 return letter grade D."""
    from services.grade_service import letter_grade
    assert letter_grade(65) == 'D'
    assert letter_grade(60) == 'D'


def test_letter_grade_F():
    """TC-GRADE-005: Scores below 60 return letter grade F."""
    from services.grade_service import letter_grade
    assert letter_grade(55) == 'F'
    assert letter_grade(0) == 'F'


# ── Weighted average tests ────────────────────────────────────────────────────

def test_weighted_average_with_scores(app):
    """TC-GRADE-006: Weighted average for student with seeded scores is within expected range."""
    with app.app_context():
        from models._common import get_conn
        from services.grade_service import calculate_weighted_average
        db = get_conn()
        s1 = db.execute(
            "SELECT id FROM users WHERE username='L20261001'"
        ).fetchone()['id']
        c1 = db.execute(
            "SELECT id FROM courses WHERE course_code='CS101'"
        ).fetchone()['id']
        avg = calculate_weighted_average(s1, c1)
        assert 50.0 <= avg <= 100.0, f'Expected 50–100 range, got {avg}'


def test_weighted_average_no_scores(app):
    """TC-GRADE-007: Weighted average returns 0.0 when no scores exist."""
    with app.app_context():
        from models._common import get_conn
        from services.grade_service import calculate_weighted_average
        db = get_conn()
        s2 = db.execute(
            "SELECT id FROM users WHERE username='L20261002'"
        ).fetchone()['id']
        c2 = db.execute(
            "SELECT id FROM courses WHERE course_code='CS201'"
        ).fetchone()['id']
        avg = calculate_weighted_average(s2, c2)
        assert avg == 0.0


def test_weighted_average_all_same_score(app):
    """
    TC-GRADE-008: When all scores equal 80, weighted average must equal 80.0
    regardless of weight distribution (mathematical property).
    """
    with app.app_context():
        from models._common import get_conn
        from services.grade_service import calculate_weighted_average

        conn = get_db()
        c1 = get_course_id(conn)
        s1 = get_student_id(conn)

        # Clear and re-insert all scores as 80
        conn.execute("""
            DELETE FROM scores WHERE student_id=? AND grade_item_id IN (
                SELECT gi.id FROM grade_items gi
                JOIN grade_categories gc ON gi.category_id=gc.id
                WHERE gc.course_id=?
            )
        """, (s1, c1))
        items = conn.execute("""
            SELECT gi.id FROM grade_items gi
            JOIN grade_categories gc ON gi.category_id=gc.id
            WHERE gc.course_id=?
        """, (c1,)).fetchall()
        for item in items:
            conn.execute(
                "INSERT INTO scores (student_id, grade_item_id, score) VALUES (?,?,?)",
                (s1, item[0], 80)
            )
        conn.commit()
        conn.close()

        result = calculate_weighted_average(s1, c1)
        assert abs(float(result) - 80.0) < 0.5, f'Expected 80.0, got {result}'


# ── Score validation tests ────────────────────────────────────────────────────

def test_score_above_100_rejected(app, teacher_client):
    """TC-GRADE-009: Score > 100 rejected by server-side validation."""
    conn = get_db()
    course_id = get_course_id(conn)
    student_id = get_student_id(conn)
    item_id = conn.execute("""
        SELECT gi.id FROM grade_items gi
        JOIN grade_categories gc ON gi.category_id=gc.id
        WHERE gc.course_id=? LIMIT 1
    """, (course_id,)).fetchone()[0]
    conn.close()

    teacher_client.post(
        f'/teacher/courses/{course_id}/grades',
        data={f'score_{student_id}_{item_id}': '150'},
        follow_redirects=True
    )

    conn = get_db()
    row = conn.execute(
        "SELECT score FROM scores WHERE student_id=? AND grade_item_id=? AND score=150",
        (student_id, item_id)
    ).fetchone()
    conn.close()
    assert row is None


def test_score_below_0_rejected(app, teacher_client):
    """TC-GRADE-010: Score < 0 rejected by server-side validation."""
    conn = get_db()
    course_id = get_course_id(conn)
    student_id = get_student_id(conn)
    item_id = conn.execute("""
        SELECT gi.id FROM grade_items gi
        JOIN grade_categories gc ON gi.category_id=gc.id
        WHERE gc.course_id=? LIMIT 1
    """, (course_id,)).fetchone()[0]
    conn.close()

    teacher_client.post(
        f'/teacher/courses/{course_id}/grades',
        data={f'score_{student_id}_{item_id}': '-5'},
        follow_redirects=True
    )

    conn = get_db()
    row = conn.execute(
        "SELECT score FROM scores WHERE student_id=? AND grade_item_id=? AND score=-5",
        (student_id, item_id)
    ).fetchone()
    conn.close()
    assert row is None


def test_audit_log_written_on_save(app, teacher_client):
    """TC-GRADE-011: Every score save creates an audit_log entry."""
    conn = get_db()
    course_id = get_course_id(conn)
    student_id = get_student_id(conn)
    item_id = conn.execute("""
        SELECT gi.id FROM grade_items gi
        JOIN grade_categories gc ON gi.category_id=gc.id
        WHERE gc.course_id=? LIMIT 1
    """, (course_id,)).fetchone()[0]
    count_before = conn.execute(
        "SELECT COUNT(*) FROM audit_log"
    ).fetchone()[0]
    conn.close()

    teacher_client.post(
        f'/teacher/courses/{course_id}/grades',
        data={f'score_{student_id}_{item_id}': '72'},
        follow_redirects=True
    )

    conn = get_db()
    count_after = conn.execute(
        "SELECT COUNT(*) FROM audit_log"
    ).fetchone()[0]
    conn.close()
    assert count_after > count_before

# ── CSV export tests ──────────────────────────────────────────────────────────

def test_generate_csv_success(app):
    """TC-GRADE-012: CSV export for course with scores returns valid CSV response."""
    with app.app_context():
        from services.report_service import generate_csv
        from models._common import get_conn
        db = get_conn()
        c1 = db.execute(
            "SELECT id FROM courses WHERE course_code='CS101'"
        ).fetchone()['id']
        result = generate_csv(c1)
        assert result is not None
        assert result.mimetype == 'text/csv'
        body = result.get_data(as_text=True)
        reader = csv.reader(io.StringIO(body))
        rows = list(reader)
        assert len(rows) >= 3
        assert rows[0][0] == 'Student ID'
        assert 'Weighted Average' in rows[0]


def test_generate_csv_no_scores(app):
    """TC-GRADE-013: CSV export for course with no scores returns None."""
    with app.app_context():
        from services.report_service import generate_csv
        from models._common import get_conn
        db = get_conn()
        c2 = db.execute(
            "SELECT id FROM courses WHERE course_code='CS201'"
        ).fetchone()['id']
        result = generate_csv(c2)
        assert result is None


# ── Statistics tests ──────────────────────────────────────────────────────────

def test_class_statistics_bins(app):
    """TC-GRADE-014: Class statistics returns correct structure with 5 grade bins."""
    with app.app_context():
        from services.statistics_service import class_statistics
        from models._common import get_conn
        db = get_conn()
        c1 = db.execute(
            "SELECT id FROM courses WHERE course_code='CS101'"
        ).fetchone()['id']
        stats = class_statistics(c1)
        assert stats['avg'] > 0
        assert stats['highest'] >= stats['lowest']
        assert stats['lowest'] >= 0
        assert len(stats['bins']) == 5
        assert len(stats['labels']) == 5
        assert isinstance(stats['bins'], list)
        assert all(isinstance(b, (int, float)) for b in stats['bins'])


def test_student_grade_view_hides_other_identities(app, student_client):
    """TC-GRADE-015: Student grade page does not expose other students' usernames."""
    conn = get_db()
    course_id = get_course_id(conn)
    conn.close()

    response = student_client.get(
        f'/student/courses/{course_id}/grades',
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'L20261002' not in response.data
    assert b'L20261003' not in response.data