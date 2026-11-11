from flask import Flask, render_template, jsonify,session
from routes.extensions import mysql
from db import get_db

app = Flask(__name__)

try:
    import config
except ImportError:
    raise SystemExit(
        "config.py not found. Copy config.example.py to config.py "
        "and put your MySQL password in it."
    )




app.secret_key = config.SECRET_KEY





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
def inject_student_balance():
    if session.get('role') == 'student' and 'user_id' in session:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT balance FROM students WHERE user_id = %s", (session['user_id'],))
            student = cursor.fetchone()
            balance = student['balance'] if student else 0.0
            return {'student_balance': balance}
        finally:
            cursor.close()
            db.close()
    return {'student_balance': None}

from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.vendor import vendor_bp
from routes.student import student_bp
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(vendor_bp)
app.register_blueprint(student_bp)

if __name__ == '__main__':
    app.run(debug=True)