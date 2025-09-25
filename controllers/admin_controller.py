# Yeh admin_controller.py file hai. Yahan saare admin ke routes aur logic milenge.
# Jaise dashboard, users, parking lots, reports, sab kuch yahin handle hota hai.
# Agar admin ka koi naya feature banana hai toh yahin function add karo.
# Neeche har function ke upar bhi simple comments milenge.
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Each function below is a Flask route for admin actions.
# Comments explain what each part does and how to extend it.
@admin_bp.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    # Get parking lots with spot counts
    cursor.execute('''
        SELECT pl.*, 
               COUNT(ps.id) as total_spots,
               SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots,
               SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id
    ''')
    parking_lots = cursor.fetchall()
    
    # Get recent parking history
    cursor.execute('''
        SELECT r.id, u.full_name, pl.prime_location_name, ps.id as spot_id,
               r.parking_timestamp, r.leaving_timestamp, r.parking_cost
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        JOIN parking_spots ps ON r.spot_id = ps.id
        JOIN parking_lots pl ON ps.lot_id = pl.id
        ORDER BY r.parking_timestamp DESC
        LIMIT 10
    ''')
    recent_history = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         parking_lots=parking_lots, 
                         recent_history=recent_history)

@admin_bp.route('/admin/parking-lots')
@admin_required
def admin_parking_lots():
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT pl.*, 
               COUNT(ps.id) as total_spots,
               SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots,
               SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id
    ''')
    parking_lots = cursor.fetchall()
    
    conn.close()
    return render_template('admin/parking_lots.html', parking_lots=parking_lots)

@admin_bp.route('/admin/add-parking-lot', methods=['GET', 'POST'])
@admin_required
def add_parking_lot():
    if request.method == 'POST':
        prime_location_name = request.form['prime_location_name']
        price = float(request.form['price'])
        address = request.form['address']
        pin_code = request.form['pin_code']
        maximum_number_of_spots = int(request.form['maximum_number_of_spots'])
        
        conn = sqlite3.connect('parking.db')
        cursor = conn.cursor()
        
        # Insert parking lot
        cursor.execute('''
            INSERT INTO parking_lots (prime_location_name, price, address, pin_code, maximum_number_of_spots)
            VALUES (?, ?, ?, ?, ?)
        ''', (prime_location_name, price, address, pin_code, maximum_number_of_spots))
        
        lot_id = cursor.lastrowid
        
        # Create parking spots
        for i in range(maximum_number_of_spots):
            cursor.execute('''
                INSERT INTO parking_spots (lot_id, status)
                VALUES (?, 'A')
            ''', (lot_id,))
        
        conn.commit()
        conn.close()
        
        flash('Parking lot added successfully!', 'success')
        return redirect(url_for('admin.admin_parking_lots'))
    
    return render_template('admin/add_parking_lot.html')

@admin_bp.route('/admin/edit-parking-lot/<int:lot_id>', methods=['GET', 'POST'])
@admin_required
def edit_parking_lot(lot_id):
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        prime_location_name = request.form['prime_location_name']
        price = float(request.form['price'])
        address = request.form['address']
        pin_code = request.form['pin_code']
        maximum_number_of_spots = int(request.form['maximum_number_of_spots'])
        
        # Check if any spots are occupied
        cursor.execute('''
            SELECT COUNT(*) FROM parking_spots 
            WHERE lot_id = ? AND status = 'O'
        ''', (lot_id,))
        occupied_spots = cursor.fetchone()[0]
        
        if occupied_spots > 0:
            flash('Cannot edit parking lot with occupied spots', 'error')
            return redirect(url_for('admin.admin_parking_lots'))
        
        # Update parking lot
        cursor.execute('''
            UPDATE parking_lots 
            SET prime_location_name = ?, price = ?, address = ?, pin_code = ?, maximum_number_of_spots = ?
            WHERE id = ?
        ''', (prime_location_name, price, address, pin_code, maximum_number_of_spots, lot_id))
        
        # Delete existing spots
        cursor.execute('DELETE FROM parking_spots WHERE lot_id = ?', (lot_id,))
        
        # Create new spots
        for i in range(maximum_number_of_spots):
            cursor.execute('''
                INSERT INTO parking_spots (lot_id, status)
                VALUES (?, 'A')
            ''', (lot_id,))
        
        conn.commit()
        conn.close()
        
        flash('Parking lot updated successfully!', 'success')
        return redirect(url_for('admin.admin_parking_lots'))
    
    # Get parking lot details
    cursor.execute('SELECT * FROM parking_lots WHERE id = ?', (lot_id,))
    parking_lot = cursor.fetchone()
    conn.close()
    
    if not parking_lot:
        flash('Parking lot not found', 'error')
        return redirect(url_for('admin.admin_parking_lots'))
    
    return render_template('admin/edit_parking_lot.html', parking_lot=parking_lot)

@admin_bp.route('/admin/delete-parking-lot/<int:lot_id>', methods=['POST'])
@admin_required
def delete_parking_lot(lot_id):
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    # Check if any spots are occupied
    cursor.execute('''
        SELECT COUNT(*) FROM parking_spots 
        WHERE lot_id = ? AND status = 'O'
    ''', (lot_id,))
    occupied_spots = cursor.fetchone()[0]
    
    if occupied_spots > 0:
        flash('Cannot delete parking lot with occupied spots', 'error')
        conn.close()
        return redirect(url_for('admin.admin_parking_lots'))
    
    # Delete parking spots
    cursor.execute('DELETE FROM parking_spots WHERE lot_id = ?', (lot_id,))
    
    # Delete parking lot
    cursor.execute('DELETE FROM parking_lots WHERE id = ?', (lot_id,))
    
    conn.commit()
    conn.close()
    
    flash('Parking lot deleted successfully!', 'success')
    return redirect(url_for('admin.admin_parking_lots'))

@admin_bp.route('/admin/users')
@admin_required
def admin_users():
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, email, full_name, mobile, role FROM users WHERE role != "admin"')
    users = cursor.fetchall()
    
    conn.close()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    # Check if user has active reservations
    cursor.execute('''
        SELECT COUNT(*) FROM reservations 
        WHERE user_id = ? AND status = 'active'
    ''', (user_id,))
    active_reservations = cursor.fetchone()[0]
    
    if active_reservations > 0:
        flash('Cannot delete user with active reservations', 'error')
        conn.close()
        return redirect(url_for('admin.admin_users'))
    
    # Delete user
    cursor.execute('DELETE FROM users WHERE id = ? AND role != "admin"', (user_id,))
    
    conn.commit()
    conn.close()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/parking-spots/<int:lot_id>')
@admin_required
def view_parking_spots(lot_id):
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    # Get parking lot details
    cursor.execute('SELECT * FROM parking_lots WHERE id = ?', (lot_id,))
    parking_lot = cursor.fetchone()
    
    if not parking_lot:
        flash('Parking lot not found', 'error')
        conn.close()
        return redirect(url_for('admin.admin_parking_lots'))
    
    # Get parking spots with reservation details
    cursor.execute('''
        SELECT ps.*, r.vehicle_number, r.parking_timestamp, u.full_name
        FROM parking_spots ps
        LEFT JOIN reservations r ON ps.id = r.spot_id AND r.status = 'active'
        LEFT JOIN users u ON r.user_id = u.id
        WHERE ps.lot_id = ?
        ORDER BY ps.id
    ''', (lot_id,))
    parking_spots = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/parking_spots.html', 
                         parking_lot=parking_lot, 
                         parking_spots=parking_spots)

@admin_bp.route('/admin/reports')
@admin_required
def admin_reports():
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    # Get summary statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_lots,
            SUM(maximum_number_of_spots) as total_spots
        FROM parking_lots
    ''')
    lot_stats = cursor.fetchone()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_spots,
            SUM(CASE WHEN status = 'A' THEN 1 ELSE 0 END) as available_spots,
            SUM(CASE WHEN status = 'O' THEN 1 ELSE 0 END) as occupied_spots
        FROM parking_spots
    ''')
    spot_stats = cursor.fetchone()
    
    # Get parking lot wise statistics
    cursor.execute('''
        SELECT pl.prime_location_name,
               COUNT(ps.id) as total_spots,
               SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots,
               SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id
    ''')
    lot_wise_stats = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/reports.html', 
                         lot_stats=lot_stats,
                         spot_stats=spot_stats,
                         lot_wise_stats=lot_wise_stats) 