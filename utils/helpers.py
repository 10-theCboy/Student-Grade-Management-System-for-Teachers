import secrets
import string

from flask import session, request


def generate_csrf_token() -> str:
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def validate_csrf_token() -> bool:
    token = request.form.get('csrf_token')
    if not token or token != session.get('csrf_token'):
        return False
    return True


def generate_enrollment_code(length: int = 8) -> str:
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
