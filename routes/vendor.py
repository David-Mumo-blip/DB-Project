from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from db import get_db
from routes.notifications import notify
from routes.uploads import save_image, delete_image, has_uploaded_file
from werkzeug.exceptions import HTTPException

vendor_bp = Blueprint('vendor', __name__, url_prefix='/vendor')

CATEGORIES = ('appetizer', 'main_course', 'dessert', 'beverage')
PLACEHOLDER_IMAGE = 'image1.jpeg'   # used when a vendor does not upload a product photo


def vendor_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'vendor' or not session.get('vendor_id'):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@vendor_bp.route('/dashboard')
@vendor_required
def dashboard():
    vendor_id = session['vendor_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM vendors WHERE id = %s", (vendor_id,))
        vendor = cursor.fetchone()

        cursor.execute("SELECT * FROM menu_items WHERE vendor_id = %s ORDER BY food_name", (vendor_id,))
        products = cursor.fetchall()

        # Money only counts once an order has been readied (status 'completed').
        # Vendor self-orders (customer_id IS NULL) earn nothing.
        cursor.execute(
            """
            SELECT COALESCE(SUM(total_amount), 0) AS total_revenue
            FROM orders
            WHERE vendor_id = %s AND status = 'completed' AND customer_id IS NOT NULL
            """,
            (vendor_id,)
        )
        revenue = float(cursor.fetchone()['total_revenue'])

        cursor.execute(
            "SELECT COUNT(*) AS n FROM orders WHERE vendor_id = %s AND status = 'pending'",
            (vendor_id,)
        )
        pending_orders = cursor.fetchone()['n']

        goal = float(vendor['revenue_goal']) if vendor['revenue_goal'] else 0.0
        percent = min(int(revenue / goal * 100), 100) if goal > 0 else 0

        return render_template(
            'vendor_dashboard.html',
            vendor=vendor,
            products=products,
            revenue=revenue,
            vendor_balance=vendor['balance'],
            goal=goal,
            percent=percent,
            pending_orders=pending_orders,
        )
    finally:
        cursor.close()
        db.close()


@vendor_bp.route('/goal/set', methods=['POST'])
@vendor_required
def set_goal():
    try:
        new_goal = Decimal(request.form.get('goal', '').strip())
        if new_goal <= 0:
            raise InvalidOperation
    except InvalidOperation:
        flash('Please enter a goal amount greater than 0.', 'error')
        return redirect(url_for('vendor.dashboard'))

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE vendors SET revenue_goal = %s WHERE id = %s",
            (new_goal, session['vendor_id'])
        )
        db.commit()
        flash('Revenue goal updated successfully!', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error updating goal: {e}', 'error')
    finally:
        cursor.close()
        db.close()
    return redirect(url_for('vendor.dashboard'))


# ---------------------------------------------------------------- orders

@vendor_bp.route('/orders')
@vendor_required
def orders():
    vendor_id = session['vendor_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # Only orders still waiting to be readied; readied ones drop off this page.
        cursor.execute(
            """
            SELECT o.order_id, o.order_date, o.quantity, o.total_amount, o.status,
                   o.customer_id, m.food_name, u.name AS customer_name
            FROM orders o
            JOIN menu_items m ON o.food_id = m.id
            LEFT JOIN students s ON o.customer_id = s.student_id
            LEFT JOIN users u ON s.user_id = u.id
            WHERE o.vendor_id = %s AND o.status = 'pending'
            ORDER BY o.order_date ASC
            """,
            (vendor_id,)
        )
        vendor_orders = cursor.fetchall()

        cursor.execute(
            "SELECT id, food_name, quantity_available FROM menu_items "
            "WHERE vendor_id = %s AND quantity_available > 0 ORDER BY food_name",
            (vendor_id,)
        )
        products = cursor.fetchall()
        return render_template('vendor_orders.html', orders=vendor_orders, products=products)
    finally:
        cursor.close()
        db.close()


@vendor_bp.route('/orders/own', methods=['POST'])
@vendor_required
def own_order():
    """A vendor orders one of their own products: no payment, no student, just stock + an order."""
    vendor_id = session['vendor_id']
    try:
        food_id = int(request.form.get('food_id', ''))
        quantity = int(request.form.get('quantity', '1'))
        if quantity < 1:
            raise ValueError
    except ValueError:
        flash('Choose a product and a quantity of at least 1.', 'error')
        return redirect(url_for('vendor.orders'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, food_name, price, quantity_available FROM menu_items "
            "WHERE id = %s AND vendor_id = %s FOR UPDATE",
            (food_id, vendor_id)
        )
        item = cursor.fetchone()
        if not item:
            flash('That product is not on your menu.', 'error')
            return redirect(url_for('vendor.orders'))
        if item['quantity_available'] < quantity:
            flash(f"Only {item['quantity_available']} {item['food_name']} in stock.", 'error')
            return redirect(url_for('vendor.orders'))

        cursor.execute(
            "UPDATE menu_items SET quantity_available = quantity_available - %s WHERE id = %s",
            (quantity, food_id)
        )
        cursor.execute(
            "INSERT INTO orders (customer_id, vendor_id, food_id, quantity, total_amount, status) "
            "VALUES (NULL, %s, %s, %s, %s, 'pending')",
            (vendor_id, food_id, quantity, item['price'] * quantity)
        )
        db.commit()
        flash(f"Order placed: {quantity} x {item['food_name']}.", 'success')
    except Exception as e:
        db.rollback()
        flash(f'Could not place the order: {e}', 'error')
    finally:
        cursor.close()
        db.close()
    return redirect(url_for('vendor.orders'))


@vendor_bp.route('/orders/<int:order_id>/ready', methods=['POST'])
@vendor_required
def ready_order(order_id):
    vendor_id = session['vendor_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT o.order_id, o.customer_id, o.quantity, o.total_amount, o.status,
                   m.food_name, v.name AS vendor_name, s.user_id AS student_user_id
            FROM orders o
            JOIN menu_items m ON o.food_id = m.id
            JOIN vendors v ON o.vendor_id = v.id
            LEFT JOIN students s ON o.customer_id = s.student_id
            WHERE o.order_id = %s AND o.vendor_id = %s
            FOR UPDATE
            """,
            (order_id, vendor_id)
        )
        order = cursor.fetchone()
        if not order or order['status'] != 'pending':
            flash('That order is not waiting to be readied.', 'error')
            return redirect(url_for('vendor.orders'))

        cursor.execute("UPDATE orders SET status = 'completed' WHERE order_id = %s", (order_id,))

        if order['customer_id'] is not None:
            # Only now does the money reach the vendor, and the student is told.
            cursor.execute(
                "UPDATE vendors SET balance = balance + %s WHERE id = %s",
                (order['total_amount'], vendor_id)
            )
            notify(
                cursor, order['student_user_id'],
                f"Your order #{order_id} ({order['quantity']} x {order['food_name']}) "
                f"from {order['vendor_name']} is ready!",
                order_id
            )

        db.commit()
        flash(f'Order #{order_id} marked ready.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Could not update the order: {e}', 'error')
    finally:
        cursor.close()
        db.close()
    return redirect(url_for('vendor.orders'))


# --------------------------------------------------------------- products

def read_product_form(form):
    """Validate the add/edit product form. Returns a dict, or raises ValueError(message)."""
    food_name = form.get('food_name', '').strip()
    category = form.get('category')
    availability = form.get('availability_status', 'available')
    try:
        price = Decimal(form.get('price', '').strip())
        quantity = int(form.get('quantity_available') or 0)
    except (InvalidOperation, ValueError):
        raise ValueError('Enter a valid price and stock quantity.')

    if not food_name:
        raise ValueError('Please enter a food name.')
    if category not in CATEGORIES:
        raise ValueError('Please choose a category.')
    if availability not in ('available', 'unavailable'):
        raise ValueError('Invalid availability.')
    if price < 0 or quantity < 0:
        raise ValueError('Price and stock cannot be negative.')

    return {
        'food_name': food_name, 'price': price, 'category': category,
        'availability_status': availability, 'quantity_available': quantity,
    }


@vendor_bp.route('/product/new', methods=['GET', 'POST'])
@vendor_required
def new_product():
    """Add a product: every column of menu_items (name, price, category, availability, stock, image)."""
    if request.method == 'GET':
        return render_template('add_product.html', product=None)

    try:
        data = read_product_form(request.form)
        image_filename = save_image(request.files.get('image')) or PLACEHOLDER_IMAGE
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('vendor.new_product'))

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO menu_items
                (vendor_id, food_name, price, category, availability_status, quantity_available, image_filename)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (session['vendor_id'], data['food_name'], data['price'], data['category'],
             data['availability_status'], data['quantity_available'], image_filename)
        )
        db.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('vendor.dashboard'))
    except Exception as e:
        db.rollback()
        if image_filename != PLACEHOLDER_IMAGE:
            delete_image(image_filename)
        flash(f'Error adding product: {e}', 'error')
        return redirect(url_for('vendor.new_product'))
    finally:
        cursor.close()
        db.close()


@vendor_bp.route('/product/<int:id>/edit', methods=['GET', 'POST'])
@vendor_required
def edit_product(id):
    """Change any detail of one of your products, including its photo."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    new_image = None
    try:
        cursor.execute("SELECT * FROM menu_items WHERE id = %s AND vendor_id = %s", (id, session['vendor_id']))
        product = cursor.fetchone()
        if not product:
            abort(404)

        if request.method == 'GET':
            return render_template('add_product.html', product=product)

        try:
            data = read_product_form(request.form)
            new_image = save_image(request.files.get('image'))
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('vendor.edit_product', id=id))

        image_filename = new_image or product['image_filename']
        cursor.execute(
            """
            UPDATE menu_items
            SET food_name = %s, price = %s, category = %s, availability_status = %s,
                quantity_available = %s, image_filename = %s
            WHERE id = %s AND vendor_id = %s
            """,
            (data['food_name'], data['price'], data['category'], data['availability_status'],
             data['quantity_available'], image_filename, id, session['vendor_id'])
        )
        db.commit()
        if new_image and has_uploaded_file(product['image_filename']):
            delete_image(product['image_filename'])   # tidy the replaced upload
        flash('Product updated.', 'success')
        return redirect(url_for('vendor.dashboard'))
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        delete_image(new_image)
        flash(f'Could not update the product: {e}', 'error')
        return redirect(url_for('vendor.dashboard'))
    finally:
        cursor.close()
        db.close()


@vendor_bp.route('/product/<int:id>/stock/<action>', methods=['POST'])
@vendor_required
def update_stock(id, action):
    """Add or remove `amount` units of stock. This writes to menu_items, which is
    exactly what students read, so the change shows up on their side straight away."""
    try:
        amount = max(1, min(int(request.form.get('amount', 1)), 10000))
    except ValueError:
        amount = 1

    if action not in ('add', 'reduce'):
        abort(404)

    db = get_db()
    cursor = db.cursor()
    try:
        if action == 'add':
            cursor.execute(
                "UPDATE menu_items SET quantity_available = quantity_available + %s "
                "WHERE id = %s AND vendor_id = %s", (amount, id, session['vendor_id']))
        else:
            cursor.execute(
                "UPDATE menu_items SET quantity_available = GREATEST(0, CAST(quantity_available AS SIGNED) - %s) "
                "WHERE id = %s AND vendor_id = %s", (amount, id, session['vendor_id']))
        db.commit()
    finally:
        cursor.close()
        db.close()
    return redirect(url_for('vendor.dashboard'))


@vendor_bp.route('/product/<int:id>/delete', methods=['POST'])
@vendor_required
def delete_product(id):
    db = get_db()
    cursor = db.cursor()
    try:
        # Deleting a product would also wipe its order history (ON DELETE CASCADE),
        # so only products that were never ordered can be removed.
        cursor.execute("SELECT COUNT(*) FROM orders WHERE food_id = %s", (id,))
        if cursor.fetchone()[0]:
            flash('This product has orders and cannot be removed. Set its stock to 0 instead.', 'error')
            return redirect(url_for('vendor.dashboard'))
        cursor.execute("DELETE FROM menu_items WHERE id = %s AND vendor_id = %s", (id, session['vendor_id']))
        db.commit()
        flash('Product removed.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Could not remove the product: {e}', 'error')
    finally:
        cursor.close()
        db.close()
    return redirect(url_for('vendor.dashboard'))
