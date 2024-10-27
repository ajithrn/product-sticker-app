from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def store_admin_required(f):
    """Decorator to require store admin role"""
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'store_admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_view
