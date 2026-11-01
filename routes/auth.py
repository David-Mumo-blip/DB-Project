from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.passwords import  hash_password, verify_password
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

from db import get_db
import mysql.connector

VALID_ROLES = ('student' , 'vendor')

VENDOR_HOME = {1:'vendor.pate', 2: 'vendor.kilimanjaro'}
@auth_bp.route('/role')
def role():
    """ Choose a role before registration"""
    return render_template(role.html)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    role = request.values.get('role', '').strip().lower()

    if role not in VALID_ROLES:
        return redirect(url_for('auth.role'))

    if request.method == 'GET':
        return render_template('register.html', role=role)

    # Common account fields
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')

    if not name or not email or not password or not confirm:
        flash('Please fill in all required fields.', 'error')
        return render_template('register.html', role=role), 400

    if len(password) < 8:
        flash('Password must be at least 8 characters.', 'error')
        return render_template('register.html', role=role), 400

    if password != confirm:
        flash('Passwords do not match.', 'error')
        return render_template('register.html', role=role), 400

    # Vendor-specific application fields
    vendor_name = ''
    location_description = ''
    campus_status = ''

    if role == 'vendor':
        vendor_name = request.form.get('vendor_name', '').strip()
        location_description = request.form.get(
            'location_description', ''
        ).strip()
        campus_status = request.form.get('campus_status', '').strip()

        if not vendor_name or campus_status not in (
            'on-campus', 'off-campus'
        ):
            flash(
                'Please provide a vendor name and valid campus status.',
                'error'
            )
            return render_template('register.html', role=role), 400

    db = get_db()
    cursor = None

    try:
        cursor = db.cursor()

        # Create the account first.
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            """,
            (name, email, hash_password(password), role)
        )

        user_id = cursor.lastrowid

        if role == 'student':
            cursor.execute(
                """
                INSERT INTO students (user_id)
                VALUES (%s)
                """,
                (user_id,)
            )

        else:
            cursor.execute(
                """
                INSERT INTO vendors
                    (user_id, name, location_description,
                     campus_status, approval_status)
                VALUES (%s, %s, %s, %s, 'pending')
                """,
                (
                    user_id,
                    vendor_name,
                    location_description or None,
                    campus_status
                )
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
        if cursor is not None:
            cursor.close()
        db.close()

    if role == 'student':
        flash('Account created! Please log in.', 'success')
    else:
        flash(
            'Application submitted! Your vendor account is pending '
            'administrator approval.',
            'success'
        )

    return redirect(url_for('auth.login'))





@auth_bp.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not email or not password:
        flash("Please enter your email and password.", 'error')
        return render_template('login.html'), 400

    db = get_db()
    cursor = None

    try:
        cursor = db.cursor(dictionary = True)

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

        if not user or not verify_password(
            user['password_hash'], password
        ):
            flash('Invalid email or password.', 'error')
            return render_template('login.html'), 401

        vendor_id = None

        if user['role'] == 'vendor':
            cursor.execute(
                """
                SELECT id
                FROM vendor_specific
                WHERE user_id = %s
                LIMIT 1
                """,
                (user['id'],)
            )
            vendor = cursor.fetchone()

            if not vendor:
                flash("Your vendor profile is unavailable.", 'error')
                return render_template('login.html'), 403

            # Remember to return to add checks on vendor's approval statuses.


            session.clear()
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']

            if vendor_id is not None:
                session['vendor_id'] = vendor_id

            if user['role']== 'vendor':
                endpoint = VENDOR_HOME.get(vendor_id)

                if endpoint:
                    return redirect(url_for(endpoint))

                return redirect(url_for('index'))

            return redirect(url_for('index'))

    except mysql.connector.Error:
        db.rollback()
        flash('A database error occured. Please try again')
        return render_template('login.html'), 500

    finally:
        if cursor is not None:
            cursor.close()
        db.close()


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))
        


@auth_bp.route('/register')
def register():
    return render_template('register.html')


@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'GET':
        return render_template('student-signup.html')
    # return create_account('student', 'student-signup.html')


@auth_bp.route('/register/vendor', methods=['GET', 'POST'])
def register_vendor():
    if request.method == 'GET':
        return render_template('Vendor-specifc.html')
    # return create_account('vendor', 'vendor-signup.html')


