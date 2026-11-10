from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from functools import wraps
from routes.guards import login_required
from db import get_db

student_bp = Blueprint('student', __name__, url_prefix='/student')

VENDOR_HOME = { 
    5: 'auth.pate_vendor',    
    6: 'auth.georgie_vendor',   
    7: 'auth.upesi_vendor',    
    8: 'auth.kerinton_vendor',
}

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
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Fetch all approved vendors from the database
        cursor.execute("SELECT * FROM vendors WHERE approval_status = 'approved'")
        vendors = cursor.fetchall()
        
        print("DEBUG - VENDORS FROM DB: ", vendors)
        
        # Separate them to match your template's On-Campus vs Off-Campus sections
        internal_vendors = [v for v in vendors if v['campus_status'] == 'on-campus']
        external_vendors = [v for v in vendors if v['campus_status'] == 'off-campus']

        if not vendors:
            internal_vendors = []
            external_vendors = []
            
        return render_template('main.html', internal_vendors=internal_vendors, external_vendors=external_vendors)
    finally:
        cursor.close()
        db.close()


@student_bp.route('/vendor/<int:vendor_id>')
def view_vendor(vendor_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM vendors WHERE id = %s",
            (vendor_id,)
        )
        vendor = cursor.fetchone()

        if not vendor:
            abort(404)

        cursor.execute(
            "SELECT * FROM menu_items WHERE vendor_id = %s",
            (vendor_id,)
        )
        products = cursor.fetchall()

        return render_template('vendor_menu.html', vendor=vendor, products=products)
    finally:
        cursor.close()
        db.close()


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