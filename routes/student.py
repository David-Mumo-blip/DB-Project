from flask import Blueprint, render_template, request, redirect, url_for, flash,session,abort
student_bp = Blueprint('student', __name__, url_prefix='/student')
from functools import wraps
from routes.guards import login_required
from db import get_db


VENDOR_HOME = { 5: 'auth.pate_vendor',     
    6: 'auth.georgie_vendor',   
    7: 'auth.upesi_vendor',     
    8: 'auth.kerinton_vendor',}

def vendor_only(expected_vendor_id):
    """Allow only the logged-in vendor whose overall_id matches."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'error')
                return redirect(url_for('auth.login'))
            if (session.get('role') != 'vendor'
                    or session.get('vendor_id') != expected_vendor_id):
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator

def get_student_balance():
    user_id = session.get('user_id')

    if not user_id or session.get('role') != 'student':
        return None

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT balance FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        return user['balance'] if user else None
    finally:
        cursor.close()
        conn.close()



@student_bp.route('/landing')
def landing():
    return render_template('main.html')


@student_bp.route('/pate')
@login_required
def pate():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""SELECT id, food_name, price, quantity_available
    FROM food
    WHERE vendor_id = 1""")

    food = cursor.fetchall()

    print("MENU ITEMS:", food)

    cursor.close()
    db.close()

    return render_template('pate.html', food=food, balance=get_student_balance())


@student_bp.route('/upesi')
@login_required
def upesi():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, food_name, price, quantity_available
            FROM food
            WHERE vendor_id = 2
            ORDER BY id
        """)

        food = cursor.fetchall()

    finally:
        cursor.close()
        db.close()

    return render_template(
        'upesi.html',
        food=food,
        balance=get_student_balance()
    )



@student_bp.route('/kerinton')
@login_required
def kerinton():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, food_name, price, quantity_available
            FROM food
            WHERE vendor_id = 2
            ORDER BY id
        """)

        food = cursor.fetchall()

    finally:
        cursor.close()
        db.close()

    return render_template(
        'kerinton.html',
        food=food,
        balance=get_student_balance()
    )



@student_bp.route('/georgie')
@login_required
def georgie():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, food_name, price, quantity_available
            FROM food
            WHERE vendor_id = 2
            ORDER BY id
        """)

        food = cursor.fetchall()

    finally:
        cursor.close()
        db.close()

    return render_template(
        'georgies.html',
        food=food,
        balance=get_student_balance()
    )



@student_bp.route('/cart')
def cart():
    return render_template('cart.html')


@student_bp.route('/vendor/pate')
@vendor_only(5)
def pate_vendor():
    return render_template('patevv.html')


@student_bp.route('/vendor/georgie')
@vendor_only(6)
def georgie_vendor():
    return render_template('georgievv.html')


@student_bp.route('/vendor/upesi')
@vendor_only(7)
def upesi_vendor():
    return render_template('upesivv.html')


@student_bp.route('/vendor/kerinton')
@vendor_only(8)
def kerinton_vendor():
    return render_template('kerintonvv.html')