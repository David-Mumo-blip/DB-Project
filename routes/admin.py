from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, session, abort
from db import get_db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT v.id, v.name, v.location_description, v.campus_status,
                   u.name AS owner_name, u.email
            FROM vendors v JOIN users u ON v.user_id = u.id
            WHERE v.approval_status = 'pending'
            ORDER BY v.id
            """
        )
        pending = cursor.fetchall()
        cursor.execute(
            "SELECT id, name, location_description, campus_status, approval_status "
            "FROM vendors WHERE approval_status <> 'pending' ORDER BY id"
        )
        reviewed = cursor.fetchall()
        return render_template('admin_dashboard.html', pending=pending, reviewed=reviewed)
    finally:
        cursor.close()
        db.close()


@admin_bp.route('/vendor/<int:vendor_id>/<decision>', methods=['POST'])
@admin_required
def decide(vendor_id, decision):
    if decision not in ('approve', 'reject'):
        abort(404)
    status = 'approved' if decision == 'approve' else 'rejected'

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE vendors SET approval_status = %s WHERE id = %s", (status, vendor_id))
        db.commit()
        if cursor.rowcount:
            flash(f'Vendor {status}.', 'success')
        else:
            flash('Vendor not found (or already in that state).', 'error')
    finally:
        cursor.close()
        db.close()
    return redirect(url_for('admin.dashboard'))
