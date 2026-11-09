from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from routes.passwords import hash_password, verify_password
from functools import wraps
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

from db import get_db
import mysql.connector

VALID_ROLES = ('student', 'vendor')

# Maps a vendor's overall_id to the endpoint they should land on.
# Empty for now, so vendors go to the landing page until their pages exist.
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


@auth_bp.route('/role')
def role():
    """ Choose a role before registration"""
    return render_template('role.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    role = request.values.get('role', '').strip().lower()
    if role not in VALID_ROLES:
        return redirect(url_for('auth.role'))

    if request.method == 'GET':
        return render_template('register.html', role=role)

    # 1. Extraction & Sanitization
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')

    vendor_name = request.form.get('vendor_name', '').strip()
    location_description = request.form.get('location_description', '').strip()
    campus_status = request.form.get('campus_status', '').strip()

    # 2. Validation Constraints
    if not name or not email or not password or not confirm:
        flash('Please fill in all required fields.', 'error')
        return render_template('register.html', role=role), 400

    if len(password) < 8:
        flash('Password must be at least 8 characters.', 'error')
        return render_template('register.html', role=role), 400

    if password != confirm:
        flash('Passwords do not match.', 'error')
        return render_template('register.html', role=role), 400

    if role == 'vendor' and (not vendor_name or campus_status not in ('on-campus', 'off-campus')):
        flash('Please provide a vendor name and valid campus status.', 'error')
        return render_template('register.html', role=role), 400

    # 3. Heavy/Unsafe computations executed outside of DB transactions
    hashed_password = hash_password(password)

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role) 
            VALUES (%s, %s, %s, %s)
            """,
            (name, email, hashed_password, role)
        )
        user_id = cursor.lastrowid

        if role == 'student':
            cursor.execute(
                "INSERT INTO students (user_id) VALUES (%s)", 
                (user_id,)
            )
        else:
            cursor.execute(
                """
                INSERT INTO vendors (user_id, name, location_description, campus_status, approval_status) 
                VALUES (%s, %s, %s, %s, 'pending')
                """,
                (user_id, vendor_name, location_description or None, campus_status)
            )
        
        db.commit()

    except mysql.connector.IntegrityError as err:
        db.rollback()
        if err.errno == 1062:
            flash('That email is already registered.', 'error')
            return render_template('register.html', role=role), 409
        
        flash('The account could not be created. Please try again.', 'error')
        return render_template('register.html', role=role), 500

    except mysql.connector.Error:
        db.rollback()
        flash('A database error occurred. Please try again.', 'error')
        return render_template('register.html', role=role), 500
        
    finally:
        cursor.close()

    if role == 'student':
        flash('Account created! Please log in.', 'success')
    else:
        flash('Application submitted! Your vendor account is pending administrator approval.', 'success')
        
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not email or not password:
        flash("Please enter your email and password.", 'error')
        return render_template('login.html'), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, password_hash, role
            FROM users
            WHERE email = %s
            LIMIT 1
            """,
            (email,)
        )
        user = cursor.fetchone()

        if not user or not verify_password(user['password_hash'], password):
            flash('Invalid email or password.', 'error')
            return render_template('login.html'), 401

        vendor_id = None

        # 2. Extract Profile Identifiers based on Role
        if user['role'] == 'vendor':
            # Find the vendor profile that belongs to this user account.
            # NOTE: we select overall_id (what we read below), not user_id.
            cursor.execute(
                """
                SELECT overall_id, status
                FROM vendor_overall
                WHERE user_id = %s
                LIMIT 1
                """,
                (user['id'],)
            )
            vendor = cursor.fetchone()

            if not vendor:
                flash("Your vendor profile is unavailable.", 'error')
                return render_template('login.html'), 403

            if vendor['status'] != 'approved':
                flash("Your vendor application is still under review.", 'error')
                return render_template('login.html'), 403

            vendor_id = vendor['overall_id']

        session.clear()
        session['user_id'] = user['id']
        session['name'] = user['name']
        session['role'] = user['role']

        if vendor_id is not None:
            session['vendor_id'] = vendor_id

            endpoint = VENDOR_HOME.get(vendor_id)
            if endpoint:
                return redirect(url_for(endpoint))

        return redirect(url_for('auth.landing'))

    except mysql.connector.Error as e:
        print("LOGIN DB ERROR:", e)
        db.rollback()
        flash('A database error occurred. Please try again.', 'error')
        return render_template('login.html'), 500

    finally:
        cursor.close()


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))


@auth_bp.route('/landing')
def landing():
    return render_template('main.html')


@auth_bp.route('/pate')
def pate():
    return render_template('pate.html')


@auth_bp.route('/upesi')
def upesi():
    return render_template('upesi.html')


@auth_bp.route('/kerinton')
def kerinton():
    return render_template('kerinton.html')


@auth_bp.route('/georgies')
def georgies():
    return render_template('georgies.html')


@auth_bp.route('/cart')
def cart():
    return render_template('cart.html')


@auth_bp.route('/vendor/pate')
@vendor_only(5)
def pate_vendor():
    return render_template('patevv.html')


@auth_bp.route('/vendor/georgie')
@vendor_only(6)
def georgie_vendor():
    return render_template('georgievv.html')


@auth_bp.route('/vendor/upesi')
@vendor_only(7)
def upesi_vendor():
    return render_template('upesivv.html')


@auth_bp.route('/vendor/kerinton')
@vendor_only(8)
def kerinton_vendor():
    return render_template('kerintonvv.html')