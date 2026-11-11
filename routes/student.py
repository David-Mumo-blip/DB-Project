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
    cart_items = session.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart_items.values())
    return render_template('cart.html', cart_items=cart_items, total=total)

@student_bp.route('/cart/add/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    # Ensure user is logged in as a student
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please log in as a student to add items to your cart.', 'error')
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # Fetch the menu item
        cursor.execute("SELECT * FROM menu_items WHERE id = %s", (item_id,))
        item = cursor.fetchone()

        if not item or item['availability_status'] != 'available':
            flash('Item is unavailable.', 'error')
            return redirect(url_for('student.landing'))

        # Initialize cart in session if it doesn't exist
        if 'cart' not in session:
            session['cart'] = {}

        cart = session['cart']
        item_id_str = str(item_id)

        # If item already in cart, increment quantity; otherwise add it
        if item_id_str in cart:
            cart[item_id_str]['quantity'] += 1
        else:
            cart[item_id_str] = {
                'id': item['id'],
                'vendor_id': item['vendor_id'],
                'food_name': item['food_name'],
                'price': float(item['price']),
                'quantity': 1,
                'image_filename': item['image_filename']
            }

        session.modified = True
        flash(f"Added {item['food_name']} to your cart!", 'success')
        
        # Redirect back to the vendor's menu page
        return redirect(url_for('student.view_vendor', vendor_id=item['vendor_id']))

    finally:
        cursor.close()
        db.close()


@student_bp.route('/cart/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please log in to checkout.', 'error')
        return redirect(url_for('auth.login'))

    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('student.cart'))

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Get student_id and current wallet balance
        cursor.execute("SELECT student_id, balance FROM students WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        
        if not student:
            flash('Student profile not found.', 'error')
            return redirect(url_for('student.cart'))

        student_id = student['student_id']
        balance = student['balance']

        # Calculate total order amount
        total_amount = sum(item['price'] * item['quantity'] for item in cart.values())

        if balance < total_amount:
            flash('Insufficient wallet balance to complete this order.', 'error')
            return redirect(url_for('student.cart'))

        # Deduct balance
# Deduct balance from student
        new_balance = balance - total_amount
        cursor.execute("UPDATE students SET balance = %s WHERE student_id = %s", (new_balance, student_id))

        # Track items per vendor to credit their balances correctly
        vendor_totals = {}

        for item in cart.values():
            v_id = item['vendor_id']
            item_total = item['price'] * item['quantity']
            vendor_totals[v_id] = vendor_totals.get(v_id, 0) + item_total

            cursor.execute(
                """
                INSERT INTO orders (customer_id, vendor_id, food_id, total_amount, status)
                VALUES (%s, %s, %s, %s, 'pending')
                """,
                (student_id, v_id, item['id'], item_total)
            )
            order_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO payments (order_id, amount, payment_method, payment_status)
                VALUES (%s, %s, 'wallet', 'completed')
                """,
                (order_id, item_total)
            )

        # Credit each vendor's balance with their respective order totals
        for v_id, total_earned in vendor_totals.items():
            cursor.execute(
                """
                UPDATE vendors 
                SET balance = balance + %s 
                WHERE id = %s
                """,
                (total_earned, v_id)
            )

        db.commit()
        
        # Clear the cart after successful checkout
        session.pop('cart', None)
        flash('Order placed successfully! Payment completed via wallet.', 'success')
        return redirect(url_for('student.landing'))

    except Exception as e:
        db.rollback()
        flash(f'Checkout failed: {str(e)}', 'error')
        return redirect(url_for('student.cart'))
    finally:
        cursor.close()
        db.close()

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