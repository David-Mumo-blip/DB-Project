from flask import Blueprint, render_template, session, redirect, url_for, flash
from db import get_db

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


def notify(cursor, user_id, message, order_id=None):
    """Queue a notification using the caller's cursor (so it commits with their transaction)."""
    cursor.execute(
        "INSERT INTO notifications (user_id, order_id, message) VALUES (%s, %s, %s)",
        (user_id, order_id, message[:255])
    )


@notifications_bp.route('/')
def inbox():
    if 'user_id' not in session:
        flash('Please log in to continue.', 'error')
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, message, is_read, created_at FROM notifications "
            "WHERE user_id = %s ORDER BY created_at DESC, id DESC LIMIT 50",
            (session['user_id'],)
        )
        items = cursor.fetchall()
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (session['user_id'],))
        db.commit()
        return render_template('notifications.html', notifications=items)
    finally:
        cursor.close()
        db.close()
