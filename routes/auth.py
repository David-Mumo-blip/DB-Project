from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.passwords import  hash_password, verify_password
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

from db import get_db
import mysql.connector

VALID_ROLES = ('student' , 'vendor')

VENDOR_HOME = {1:'vendor.pate', 2: 'vendor.kilimanjaro'}

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
        





