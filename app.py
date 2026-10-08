from flask import Flask, render_template, jsonify

try:
    import config
except ImportError:
    raise SystemExit(
        "config.py not found. Copy config.example.py to config.py "
        "and put your MySQL password in it."
    )

from db import get_db
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.vendor import vendor_bp
from routes.student import student_bp

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(vendor_bp)
app.register_blueprint(student_bp)


@app.route('/')
def index():
    return render_template('starter.html')


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


if __name__ == '__main__':
    app.run(debug=True)