def login(client, username, password):
    # Get CSRF token from session first
    client.get('/login')
    with client.session_transaction() as sess:
        csrf = sess.get('csrf_token', '')
    return client.post('/login', data={
        'username': username,
        'password': password,
        'csrf_token': csrf
    }, follow_redirects=True)


def test_login_valid_admin(client):
    rv = login(client, 'admin', 'admin123')
    assert rv.status_code == 200
    assert b'Dashboard' in rv.data


def test_login_valid_teacher(client):
    rv = login(client, 'teacher1', 'teacher123')
    assert rv.status_code == 200
    assert b'Dashboard' in rv.data


def test_login_valid_student(client):
    rv = login(client, 'L20261001', 'student123')
    assert rv.status_code == 200


def test_login_wrong_password(client):
    rv = login(client, 'teacher1', 'wrong')
    assert rv.status_code == 200
    body = rv.data.lower()
    assert b'invalid' in body or b'incorrect' in body


def test_login_nonexistent_user(client):
    rv = login(client, 'nobody', 'x')
    assert rv.status_code == 200
    body = rv.data.lower()
    assert b'invalid' in body or b'incorrect' in body or b'not found' in body


def test_logout(client):
    login(client, 'teacher1', 'teacher123')
    rv = client.get('/logout', follow_redirects=True)
    assert rv.status_code == 200
