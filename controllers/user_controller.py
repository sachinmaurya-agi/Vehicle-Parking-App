# Yeh user_controller.py file hai. Yahan saare user ke routes aur logic milenge.
# Jaise dashboard, booking, release, history, profile, sab kuch yahin handle hota hai.
# Agar user ka koi naya feature banana hai toh yahin function add karo.
# Neeche har function ke upar bhi simple comments milenge.
"""
user_controller.py
------------------
This file contains all user-related routes and logic for the Vehicle Parking System Flask app.

- Each function is a route handler for a user action (dashboard, booking, releasing, history, etc).
- Database access is via sqlite3; now uses named access for clarity.
- To add or change user features, add or modify functions here.

How to make changes:
- To change HTML: Edit the corresponding template in templates/user/ (e.g., book_parking.html, history.html).
- To change CSS: Edit static/css/style.css or add inline styles in the HTML templates.
- To change backend logic: Edit or add functions in this file.
- For new user features, add a new @user_bp.route and function.

All functions now include comments explaining their purpose and key steps.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

user_bp = Blueprint('user', __name__)

def get_db_connection():
    """Helper to get a DB connection with named row access."""
    conn = sqlite3.connect('parking.db')
    conn.row_factory = sqlite3.Row
    return conn

def user_required(f):
    """Decorator to ensure user is logged in before accessing a route."""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Each function below is a Flask route for user actions.
# Comments explain what each part does and how to extend it.
@user_bp.route('/user/dashboard')
@user_required
def user_dashboard():
    """Show the user's dashboard with recent history and available lots."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get user's recent parking history
    cursor.execute('''
        SELECT r.id, pl.prime_location_name, ps.id as spot_id,
               r.parking_timestamp, r.leaving_timestamp, r.parking_cost, r.vehicle_number
        FROM reservations r
        JOIN parking_spots ps ON r.spot_id = ps.id
        JOIN parking_lots pl ON ps.lot_id = pl.id
        WHERE r.user_id = ?
        ORDER BY r.parking_timestamp DESC
        LIMIT 10
    ''', (session['user_id'],))
    recent_history = cursor.fetchall()
    # Get available parking lots
    cursor.execute('''
        SELECT pl.*, 
               COUNT(ps.id) as total_spots,
               SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id
        HAVING available_spots > 0
    ''')
    available_lots = cursor.fetchall()
    conn.close()
    # Renders the dashboard template and passes recent_history and available_lots to it
    # The template is in templates/user/dashboard.html
    return render_template('user/dashboard.html', 
                         recent_history=recent_history,
                         available_lots=available_lots)

@user_bp.route('/user/parking-lots')
@user_required
def user_parking_lots():
    """Show all parking lots with their availability."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pl.*, 
               COUNT(ps.id) as total_spots,
               SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id
    ''')
    parking_lots = cursor.fetchall()
    conn.close()
    return render_template('user/parking_lots.html', parking_lots=parking_lots)

@user_bp.route('/user/book-parking/<int:lot_id>', methods=['GET', 'POST'])
@user_required
def book_parking(lot_id):
    """Allow the user to book one or more spots in a lot, entering a vehicle number for each."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            num_spots = int(request.form['num_spots'])
        except (KeyError, ValueError):
            flash('Invalid number of spots requested.', 'error')
            conn.close()
            return redirect(url_for('user.user_parking_lots'))
        vehicle_numbers = request.form.getlist('vehicle_numbers[]')
        if len(vehicle_numbers) != num_spots:
            flash('Please enter a vehicle number for each spot you want to book.', 'error')
            conn.close()
            return redirect(url_for('user.book_parking', lot_id=lot_id))
        # Find enough available spots in the lot
        cursor.execute('''
            SELECT id FROM parking_spots 
            WHERE lot_id = ? AND status = 'A'
            LIMIT ?
        ''', (lot_id, num_spots))
        available_spots = cursor.fetchall()
        if not available_spots or len(available_spots) < num_spots:
            flash('Not enough available spots in this parking lot.', 'error')
            conn.close()
            return redirect(url_for('user.user_parking_lots'))
        parking_timestamp = datetime.now().isoformat()
        for spot, vehicle_number in zip(available_spots, vehicle_numbers):
            spot_id = spot['id']
            cursor.execute('''
                INSERT INTO reservations (spot_id, user_id, vehicle_number, parking_timestamp)
                VALUES (?, ?, ?, ?)
            ''', (spot_id, session['user_id'], vehicle_number, parking_timestamp))
            cursor.execute('''
                UPDATE parking_spots SET status = 'O' WHERE id = ?
            ''', (spot_id,))
        conn.commit()
        conn.close()
        flash(f'{num_spots} parking spot(s) booked successfully!', 'success')
        return redirect(url_for('user.user_dashboard'))
    # Get parking lot details
    cursor.execute('SELECT * FROM parking_lots WHERE id = ?', (lot_id,))
    parking_lot = cursor.fetchone()
    if not parking_lot:
        flash('Parking lot not found', 'error')
        conn.close()
        return redirect(url_for('user.user_parking_lots'))
    # Check availability
    cursor.execute('''
        SELECT COUNT(*) FROM parking_spots 
        WHERE lot_id = ? AND status = 'A'
    ''', (lot_id,))
    available_spots = cursor.fetchone()[0]
    conn.close()
    if available_spots == 0:
        flash('No available spots in this parking lot', 'error')
        return redirect(url_for('user.user_parking_lots'))
    # If GET request, render the booking form template
    # Passes parking_lot and available_spots to templates/user/book_parking.html
    return render_template('user/book_parking.html', 
                         parking_lot=parking_lot,
                         available_spots=available_spots)

@user_bp.route('/user/release-parking/<int:reservation_id>', methods=['GET', 'POST'])
@user_required
def release_parking(reservation_id):
    """Release a single parking spot and calculate cost based on duration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get reservation details
    cursor.execute('''
        SELECT r.*, ps.id as spot_id, pl.price
        FROM reservations r
        JOIN parking_spots ps ON r.spot_id = ps.id
        JOIN parking_lots pl ON ps.lot_id = pl.id
        WHERE r.id = ? AND r.user_id = ? AND r.status = 'active'
    ''', (reservation_id, session['user_id']))
    reservation = cursor.fetchone()
    if not reservation:
        flash('Reservation not found or already released', 'error')
        conn.close()
        return redirect(url_for('user.user_dashboard'))
    if request.method == 'POST':
        leaving_timestamp = datetime.now().isoformat()
        ts = reservation['parking_timestamp']
        print(f"DEBUG: reservation['parking_timestamp'] value is: {repr(ts)}")
        if ts and isinstance(ts, str):
            ts = ts.replace('\n', ' ').replace('\r', ' ').strip()
            if 'T' not in ts and ' ' in ts:
                ts = ts.replace(' ', 'T', 1)
            try:
                parking_timestamp = datetime.fromisoformat(ts)
            except Exception:
                flash('Invalid parking timestamp for this reservation.', 'error')
                conn.close()
                return redirect(url_for('user.user_dashboard'))
        else:
            flash('Invalid parking timestamp for this reservation.', 'error')
            conn.close()
            return redirect(url_for('user.user_dashboard'))
        duration = datetime.fromisoformat(leaving_timestamp) - parking_timestamp
        hours = duration.total_seconds() / 3600
        parking_cost = hours * reservation['price']  # price per hour
        # Update reservation
        cursor.execute('''
            UPDATE reservations 
            SET leaving_timestamp = ?, parking_cost = ?, status = 'completed'
            WHERE id = ?
        ''', (leaving_timestamp, parking_cost, reservation['id']))
        # Update spot status to available
        cursor.execute('''
            UPDATE parking_spots SET status = 'A' WHERE id = ?
        ''', (reservation['spot_id'],))
        conn.commit()
        conn.close()
        flash(f'Parking spot released successfully! Total cost: ₹{parking_cost:.2f}', 'success')
        return redirect(url_for('user.user_dashboard'))
    # Renders the release parking template and passes reservation details to it
    # The template is in templates/user/release_parking.html
    return render_template('user/release_parking.html', reservation=reservation)

@user_bp.route('/user/history')
@user_required
def user_history():
    """Show all parking history for the user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.id, pl.prime_location_name, ps.id as spot_id,
               r.parking_timestamp, r.leaving_timestamp, r.parking_cost, r.vehicle_number,
               r.status
        FROM reservations r
        JOIN parking_spots ps ON r.spot_id = ps.id
        JOIN parking_lots pl ON ps.lot_id = pl.id
        WHERE r.user_id = ?
        ORDER BY r.parking_timestamp DESC
    ''', (session['user_id'],))
    history = cursor.fetchall()
    conn.close()
    # Renders the history template and passes the history list to it
    # The template is in templates/user/history.html
    return render_template('user/history.html', history=history)

@user_bp.route('/user/release-multiple', methods=['POST'])
@user_required
def release_multiple():
    """Release multiple selected reservations from the history page."""
    reservation_ids = request.form.getlist('reservation_ids')
    if not reservation_ids:
        flash('No reservations selected for release.', 'error')
        return redirect(url_for('user.user_history'))
    conn = get_db_connection()
    cursor = conn.cursor()
    released_count = 0
    for res_id in reservation_ids:
        # Get reservation details
        cursor.execute('''
            SELECT r.*, ps.id as spot_id, pl.price
            FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            JOIN parking_lots pl ON ps.lot_id = pl.id
            WHERE r.id = ? AND r.user_id = ? AND r.status = 'active'
        ''', (res_id, session['user_id']))
        reservation = cursor.fetchone()
        if not reservation:
            continue
        leaving_timestamp = datetime.now().isoformat()
        ts = reservation['parking_timestamp']
        print(f"DEBUG: reservation['parking_timestamp'] value is: {repr(ts)} (reservation id: {res_id})")
        if ts and isinstance(ts, str):
            ts = ts.replace('\n', ' ').replace('\r', ' ').strip()
            if 'T' not in ts and ' ' in ts:
                ts = ts.replace(' ', 'T', 1)
            try:
                parking_timestamp = datetime.fromisoformat(ts)
            except Exception:
                continue
        else:
            continue
        duration = datetime.fromisoformat(leaving_timestamp) - parking_timestamp
        hours = duration.total_seconds() / 3600
        parking_cost = hours * reservation['price']  # price per hour
        # Update reservation
        cursor.execute('''
            UPDATE reservations 
            SET leaving_timestamp = ?, parking_cost = ?, status = 'completed'
            WHERE id = ?
        ''', (leaving_timestamp, parking_cost, reservation['id']))
        # Update spot status to available
        cursor.execute('''
            UPDATE parking_spots SET status = 'A' WHERE id = ?
        ''', (reservation['spot_id'],))
        released_count += 1
    conn.commit()
    conn.close()
    if released_count:
        flash(f'{released_count} reservation(s) released successfully!', 'success')
    else:
        flash('No reservations were released.', 'error')
    return redirect(url_for('user.user_history'))

@user_bp.route('/user/profile')
@user_required
def user_profile():
    """Show the user's profile information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, email, full_name, address, pin_code, mobile
        FROM users WHERE id = ?
    ''', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return render_template('user/profile.html', user=user)

@user_bp.route('/user/edit-profile', methods=['GET', 'POST'])
@user_required
def edit_profile():
    """Allow the user to edit their profile information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        full_name = request.form['full_name']
        address = request.form['address']
        pin_code = request.form['pin_code']
        mobile = request.form['mobile']
        cursor.execute('''
            UPDATE users 
            SET full_name = ?, address = ?, pin_code = ?, mobile = ?
            WHERE id = ?
        ''', (full_name, address, pin_code, mobile, session['user_id']))
        conn.commit()
        conn.close()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.user_profile'))
    # Get current user data
    cursor.execute('''
        SELECT username, email, full_name, address, pin_code, mobile
        FROM users WHERE id = ?
    ''', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return render_template('user/edit_profile.html', user=user)

@user_bp.route('/user/reports')
@user_required
def user_reports():
    """Show user's parking statistics and monthly report."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get user's parking statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_reservations,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_reservations,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_reservations,
            SUM(parking_cost) as total_spent
        FROM reservations 
        WHERE user_id = ?
    ''', (session['user_id'],))
    stats = cursor.fetchone()
    # Get monthly parking data for charts
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', parking_timestamp) as month,
            COUNT(*) as reservations,
            SUM(parking_cost) as total_cost
        FROM reservations 
        WHERE user_id = ? AND status = 'completed'
        GROUP BY strftime('%Y-%m', parking_timestamp)
        ORDER BY month DESC
        LIMIT 12
    ''', (session['user_id'],))
    monthly_data = cursor.fetchall()
    conn.close()
    return render_template('user/reports.html', 
                         stats=stats,
                         monthly_data=monthly_data) 