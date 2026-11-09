from flask import Blueprint, render_template, request, redirect, url_for, flash,session,abort
student_bp = Blueprint('student', __name__, url_prefix='/student')
from functools import wraps

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



@student_bp.route('/landing')
def landing():
    return render_template('main.html')


@student_bp.route('/pate')
def pate():
    return render_template('pate.html')


@student_bp.route('/upesi')
def upesi():
    return render_template('upesi.html')


@student_bp.route('/kerinton')
def kerinton():
    return render_template('kerinton.html')


@student_bp.route('/georgies')
def georgies():
    return render_template('georgies.html')


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