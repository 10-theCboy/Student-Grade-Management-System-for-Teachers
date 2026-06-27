import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from schema import init_test_db


@pytest.fixture
def app():
    import gc
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    os.environ['TEST_DB_PATH'] = tmp.name
    os.environ['SECRET_KEY'] = 'test-key'

    from app import create_app as _create_app
    init_test_db(tmp.name)
    app = _create_app()
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost'

    with app.app_context():
        yield app

    gc.collect()
    for _ in range(5):
        try:
            os.unlink(tmp.name)
            break
        except PermissionError:
            import time
            time.sleep(0.1)
            gc.collect()
    if 'TEST_DB_PATH' in os.environ:
        del os.environ['TEST_DB_PATH']
    if 'SECRET_KEY' in os.environ:
        del os.environ['SECRET_KEY']


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def teacher_client(app):
    client = app.test_client()
    client.get('/login')
    with client.session_transaction() as sess:
        csrf = sess.get('csrf_token', '')
    client.post('/login', data={
        'username': 'teacher1',
        'password': 'teacher123',
        'csrf_token': csrf
    }, follow_redirects=True)
    return client


@pytest.fixture
def student_client(app):
    client = app.test_client()
    client.get('/login')
    with client.session_transaction() as sess:
        csrf = sess.get('csrf_token', '')
    client.post('/login', data={
        'username': 'L20261001',
        'password': 'student123',
        'csrf_token': csrf
    }, follow_redirects=True)
    return client