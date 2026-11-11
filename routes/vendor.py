from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from db import get_db
import mysql.connector

vendor_bp = Blueprint('vendor', __name__, url_prefix='/vendor')

@vendor_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'vendor':
        abort(403)
        
    vendor_id = session.get('vendor_id')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Fetch vendor details including their wallet balance
        cursor.execute("SELECT * FROM vendors WHERE id = %s", (vendor_id,))
        vendor = cursor.fetchone()
        
        # Fetch inventory
        cursor.execute("SELECT * FROM menu_items WHERE vendor_id = %s", (vendor_id,))
        products = cursor.fetchall()
        
        # Calculate total historical revenue from completed payments
        cursor.execute(
            """
            SELECT COALESCE(SUM(p.amount), 0) AS total_revenue
            FROM payments p
            JOIN orders o ON p.order_id = o.order_id
            WHERE o.vendor_id = %s AND p.payment_status = 'completed'
            """,
            (vendor_id,)
        )
        rev_data = cursor.fetchone()
        revenue = rev_data['total_revenue'] if rev_data else 0

        goal = 10000  # Target goal placeholder
        percent = min(int((revenue / goal) * 100), 100) if goal > 0 else 0
        
        return render_template(
            'vendor_dashboard.html', 
            vendor=vendor, 
            products=products, 
            revenue=revenue,
            vendor_balance=vendor['balance'],
            goal=goal,
            percent=percent
        )
    finally:
        cursor.close()
        db.close()

@vendor_bp.route('/orders')
def orders():
    if 'user_id' not in session or session.get('role') != 'vendor':
        abort(403)
        
    vendor_id = session.get('vendor_id')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT o.order_id, o.order_date, o.total_amount, o.status, m.food_name, u.name as customer_name
            FROM orders o
            JOIN menu_items m ON o.food_id = m.id
            JOIN students s ON o.customer_id = s.student_id
            JOIN users u ON s.user_id = u.id
            WHERE o.vendor_id = %s
            ORDER BY o.order_date DESC
            """,
            (vendor_id,)
        )
        vendor_orders = cursor.fetchall()
        return render_template('vendor_orders.html', orders=vendor_orders)
    finally:
        cursor.close()
        db.close()


@vendor_bp.route('/product/new', methods=['GET', 'POST'])
def new_product():
    if 'user_id' not in session or session.get('role') != 'vendor':
        abort(403)

    vendor_id = session.get('vendor_id')

    if request.method == 'GET':
        return render_template('add_product.html')

    food_name = request.form.get('food_name', '').strip()
    price = request.form.get('price')
    category = request.form.get('category')
    quantity = request.form.get('quantity_available', 20)
    image_filename = request.form.get('image_filename', 'image1.jpeg')

    if not food_name or not price or not category:
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('vendor.new_product'))

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO menu_items (vendor_id, food_name, price, category, quantity_available, image_filename)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (vendor_id, food_name, price, category, quantity, image_filename)
        )
        db.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('vendor.dashboard'))
    except Exception as e:
        db.rollback()
        flash(f'Error adding product: {str(e)}', 'error')
        return redirect(url_for('vendor.new_product'))
    finally:
        cursor.close()
        db.close()


@vendor_bp.route('/product/<int:id>/stock/<action>', methods=['POST'])
def update_stock(id, action):
    if 'user_id' not in session or session.get('role') != 'vendor':
        abort(403)

    vendor_id = session.get('vendor_id')
    db = get_db()
    cursor = db.cursor()

    try:
        if action == 'add':
            cursor.execute("UPDATE menu_items SET quantity_available = quantity_available + 1 WHERE id = %s AND vendor_id = %s", (id, vendor_id))
        elif action == 'reduce':
            cursor.execute("UPDATE menu_items SET quantity_available = GREATEST(0, quantity_available - 1) WHERE id = %s AND vendor_id = %s", (id, vendor_id))
        
        db.commit()
        return redirect(url_for('vendor.dashboard'))
    finally:
        cursor.close()
        db.close()


@vendor_bp.route('/product/<int:id>/delete', methods=['POST'])
def delete_product(id):
    if 'user_id' not in session or session.get('role') != 'vendor':
        abort(403)

    vendor_id = session.get('vendor_id')
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("DELETE FROM menu_items WHERE id = %s AND vendor_id = %s", (id, vendor_id))
        db.commit()
        flash('Product removed.', 'success')
        return redirect(url_for('vendor.dashboard'))
    finally:
        cursor.close()
        db.close()


@vendor_bp.route('/goal/set', methods=['POST'])
def set_goal():
    # Placeholder if you want to store revenue goals in session or database later
    flash('Goal updated successfully!', 'success')
    return redirect(url_for('vendor.dashboard'))