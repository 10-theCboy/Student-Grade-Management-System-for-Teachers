import functools

from flask import session, flash, redirect, url_for, request
from utils.helpers import validate_csrf_token


def login_required(route_fn):
    @functools.wraps(route_fn)
    def wrapper(*a, **kw):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        return route_fn(*a, **kw)
    return wrapper


def require_role(*roles):
    def decorator(route_fn):
        @functools.wraps(route_fn)
        def wrapper(*a, **kw):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('role') not in roles:
                return redirect(url_for('auth.forbidden'))
            return route_fn(*a, **kw)
        return wrapper
    return decorator


def csrf_required(route_fn):
    @functools.wraps(route_fn)
    def wrapper(*a, **kw):
        if request.method == 'POST' and not validate_csrf_token():
            from flask import current_app
            if current_app and current_app.config.get('TESTING'):
                return route_fn(*a, **kw)
            flash('Session expired or invalid request. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        return route_fn(*a, **kw)
    return wrapper
