from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, session, abort
from db import get_db
from routes.notifications import notify

student_bp = Blueprint('student', __name__, url_prefix='/student')


class CheckoutError(Exception):
    """A problem that stops checkout; `item_id`/`gone` let us tidy the cart."""
    def __init__(self, message, item_id=None, gone=False):
        super().__init__(message)
        self.item_id = item_id
        self.gone = gone


def student_required():
    """Return a redirect if the user isn't a logged-in student, else None."""
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please log in as a student to continue.', 'error')
        return redirect(url_for('auth.login'))
    return None


@student_bp.route('/landing')
def landing():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM vendors WHERE approval_status = 'approved' ORDER BY name")
        vendors = cursor.fetchall()
        internal_vendors = [v for v in vendors if v['campus_status'] == 'on-campus']
        external_vendors = [v for v in vendors if v['campus_status'] == 'off-campus']
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
            "SELECT * FROM vendors WHERE id = %s AND approval_status = 'approved'", (vendor_id,)
        )
        vendor = cursor.fetchone()
        if not vendor:
            abort(404)

        cursor.execute("SELECT * FROM menu_items WHERE vendor_id = %s ORDER BY category, food_name", (vendor_id,))
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
    denied = student_required()
    if denied:
        return denied

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM menu_items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
    finally:
        cursor.close()
        db.close()

    if not item:
        flash('That item no longer exists.', 'error')
        return redirect(url_for('student.landing'))

    back = redirect(url_for('student.view_vendor', vendor_id=item['vendor_id']))
    cart = session.get('cart', {})
    key = str(item_id)
    in_cart = cart[key]['quantity'] if key in cart else 0

    # Stock is only deducted when the order is paid for, but don't let people
    # put more in the cart than currently exists.
    if item['availability_status'] != 'available' or item['quantity_available'] <= 0:
        flash(f"{item['food_name']} is out of stock.", 'error')
        return back
    if in_cart + 1 > item['quantity_available']:
        flash(f"Only {item['quantity_available']} {item['food_name']} available.", 'error')
        return back

    if key in cart:
        cart[key]['quantity'] += 1
    else:
        cart[key] = {
            'id': item['id'],
            'vendor_id': item['vendor_id'],
            'food_name': item['food_name'],
            'price': float(item['price']),
            'quantity': 1,
            'image_filename': item['image_filename'],
        }
    session['cart'] = cart
    session.modified = True
    flash(f"Added {item['food_name']} to your cart!", 'success')
    return back


@student_bp.route('/cart/update/<int:item_id>/<action>', methods=['POST'])
def update_cart(item_id, action):
    cart = session.get('cart', {})
    entry = cart.get(str(item_id))
    if entry and action == 'add':
        db = get_db()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT quantity_available FROM menu_items WHERE id = %s", (item_id,))
            row = cursor.fetchone()
        finally:
            cursor.close()
            db.close()
        if row and entry['quantity'] + 1 <= row['quantity_available']:
            entry['quantity'] += 1
        else:
            flash(f"No more {entry['food_name']} in stock.", 'error')
    elif entry and action == 'reduce':
        entry['quantity'] -= 1
        if entry['quantity'] <= 0:
            del cart[str(item_id)]
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('student.cart'))


@student_bp.route('/cart/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    cart = session.get('cart', {})
    cart.pop(str(item_id), None)
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('student.cart'))


@student_bp.route('/cart/checkout', methods=['POST'])
def checkout():
    denied = student_required()
    if denied:
        return denied

    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('student.cart'))

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT student_id FROM students WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        if not student:
            raise CheckoutError('Student profile not found.')
        student_id = student['student_id']

        # 1. Lock each item (in id order, to avoid deadlocks), re-check stock and
        #    price from the database, and reserve the stock. Whoever pays first
        #    gets it; the rest see "out of stock".
        lines = []
        total = Decimal('0')
        for entry in sorted(cart.values(), key=lambda e: e['id']):
            cursor.execute(
                "SELECT id, vendor_id, food_name, price, quantity_available, availability_status "
                "FROM menu_items WHERE id = %s FOR UPDATE",
                (entry['id'],)
            )
            row = cursor.fetchone()
            if not row or row['availability_status'] != 'available' or row['quantity_available'] <= 0:
                name = row['food_name'] if row else entry['food_name']
                raise CheckoutError(f"{name} is out of stock.", item_id=entry['id'], gone=True)
            if row['quantity_available'] < entry['quantity']:
                raise CheckoutError(
                    f"Only {row['quantity_available']} {row['food_name']} left - please reduce the quantity.",
                    item_id=entry['id']
                )
            cursor.execute(
                "UPDATE menu_items SET quantity_available = quantity_available - %s WHERE id = %s",
                (entry['quantity'], row['id'])
            )
            line_total = row['price'] * entry['quantity']
            total += line_total
            lines.append((row, entry['quantity'], line_total))

        # 2. Take the money from the student's wallet (guarded so it can't go negative).
        cursor.execute(
            "UPDATE students SET balance = balance - %s WHERE student_id = %s AND balance >= %s",
            (total, student_id, total)
        )
        if cursor.rowcount == 0:
            raise CheckoutError('Insufficient wallet balance to complete this order.')

        # 3. One order per item, a completed wallet payment, and a notification
        #    to the vendor that owns the item.
        vendor_ids = {row['vendor_id'] for row, _, _ in lines}
        cursor.execute(
            "SELECT id, user_id FROM vendors WHERE id IN (%s)" % ','.join(['%s'] * len(vendor_ids)),
            tuple(vendor_ids)
        )
        vendor_users = {v['id']: v['user_id'] for v in cursor.fetchall()}

        for row, qty, line_total in lines:
            cursor.execute(
                "INSERT INTO orders (customer_id, vendor_id, food_id, food_name, quantity, total_amount, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, 'pending')",
                (student_id, row['vendor_id'], row['id'], row['food_name'], qty, line_total)
            )
            order_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO payments (order_id, amount, payment_method, payment_status) "
                "VALUES (%s, %s, 'wallet', 'completed')",
                (order_id, line_total)
            )
            notify(
                cursor, vendor_users[row['vendor_id']],
                f"New order #{order_id} from {session.get('name', 'a student')}: "
                f"{qty} x {row['food_name']} (KSh {line_total:.2f})",
                order_id
            )

        db.commit()
        session.pop('cart', None)
        flash(f'Order placed! KSh {total:.2f} was paid from your wallet.', 'success')
        return redirect(url_for('student.landing'))

    except CheckoutError as err:
        db.rollback()
        if err.gone and err.item_id is not None:
            cart.pop(str(err.item_id), None)
            session['cart'] = cart
            session.modified = True
        flash(str(err), 'error')
        return redirect(url_for('student.cart'))
    except Exception as err:
        db.rollback()
        flash(f'Checkout failed: {err}', 'error')
        return redirect(url_for('student.cart'))
    finally:
        cursor.close()
        db.close()
