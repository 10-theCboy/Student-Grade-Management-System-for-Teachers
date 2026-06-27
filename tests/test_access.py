from tests.test_auth import login


def test_access_admin_as_teacher(client):
    login(client, 'teacher1', 'teacher123')
    rv = client.get('/admin/dashboard', follow_redirects=True)
    assert rv.status_code == 403


def test_access_teacher_as_student(client):
    login(client, 'L20261001', 'student123')
    rv = client.get('/teacher/dashboard', follow_redirects=True)
    assert rv.status_code == 403


def test_access_teacher_as_admin(client):
    login(client, 'admin', 'admin123')
    rv = client.get('/teacher/dashboard', follow_redirects=True)
    assert rv.status_code == 403


def test_access_student_as_teacher(client):
    login(client, 'teacher1', 'teacher123')
    rv = client.get('/student/dashboard', follow_redirects=True)
    assert rv.status_code == 403


def test_export_route_wrong_teacher(client):
    login(client, 'teacher2', 'teacher123')
    with client.application.app_context():
        from models._common import get_conn
        db = get_conn()
        c1 = db.execute("SELECT id FROM courses WHERE course_code='CS101'").fetchone()['id']
    rv = client.get(f'/teacher/courses/{c1}/export', follow_redirects=True)
    assert rv.status_code == 200
    assert b'Access denied' in rv.data or b'access denied' in rv.data
