from functools import wraps
from flask import session, redirect, url_for, request, abort


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            if request.method == 'GET':
                # remember where they were headed, so we can send them back after login
                session['next'] = request.full_path.rstrip('?')
            return redirect(url_for('auth.role'))
        return f(*args, **kwargs)
    return wrapper


def vendor_required(vendor_id):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.role'))
            if session.get('role') != 'vendor' or session.get('vendor_id') != vendor_id:
                abort(403)   # logged in, but not THIS vendor
            return f(*args, **kwargs)
        return wrapper
    return decorator