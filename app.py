from flask import Flask, render_template, jsonify, session, flash, redirect, request, url_for
from werkzeug.exceptions import RequestEntityTooLarge
from db import get_db
from routes.uploads import image_url, has_image

app = Flask(__name__)

try:
    import config
except ImportError:
    raise SystemExit(
        "config.py not found. Copy config.example.py to config.py "
        "and put your MySQL password in it."
    )




app.secret_key = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # uploaded images: 5 MB max





@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health():
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        db.close()
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.context_processor
def inject_globals():
    """Wallet balance (students) and unread notification count (everyone logged in)."""
    ctx = {'student_balance': None, 'notif_count': 0, 'image_url': image_url, 'has_image': has_image}
    if 'user_id' not in session:
        return ctx
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        try:
            if session.get('role') == 'student':
                cursor.execute("SELECT balance FROM students WHERE user_id = %s", (session['user_id'],))
                student = cursor.fetchone()
                ctx['student_balance'] = student['balance'] if student else 0
            cursor.execute(
                "SELECT COUNT(*) AS n FROM notifications WHERE user_id = %s AND is_read = FALSE",
                (session['user_id'],)
            )
            ctx['notif_count'] = cursor.fetchone()['n']
        finally:
            cursor.close()
            db.close()
    except Exception:
        pass  # never let the header widgets take a page down
    return ctx


@app.errorhandler(RequestEntityTooLarge)
def too_large(e):
    flash('That image is too large (limit 5 MB).', 'error')
    return redirect(request.referrer or url_for('index'))


from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.vendor import vendor_bp
from routes.student import student_bp
from routes.notifications import notifications_bp
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(vendor_bp)
app.register_blueprint(student_bp)
app.register_blueprint(notifications_bp)

if __name__ == '__main__':
    app.run(debug=True)