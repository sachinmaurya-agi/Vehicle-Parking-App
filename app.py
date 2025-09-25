# Yeh app.py file hai. Yahan se pura Flask app start hota hai.
# Database bhi yahin se banta hai, aur admin/user ke routes bhi yahin se register hote hain.
# Neeche har section ke upar simple comments milenge.
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Import blueprints
from controllers.admin_controller import admin_bp
from controllers.user_controller import user_bp

# Register blueprints for admin and user routes
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

# Initialize the database and create tables if they do not exist
def init_db():
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            address TEXT,
            pin_code TEXT,
            mobile TEXT,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    # Create parking_lots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prime_location_name TEXT NOT NULL,
            price REAL NOT NULL,
            address TEXT NOT NULL,
            pin_code TEXT NOT NULL,
            maximum_number_of_spots INTEGER NOT NULL
        )
    ''')
    
    # Create parking_spots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER NOT NULL,
            status TEXT DEFAULT 'A',
            FOREIGN KEY (lot_id) REFERENCES parking_lots (id)
        )
    ''')
    
    # Create reservations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            vehicle_number TEXT NOT NULL,
            parking_timestamp DATETIME NOT NULL,
            leaving_timestamp DATETIME,
            parking_cost REAL,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (spot_id) REFERENCES parking_spots (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_password = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO users (username, email, password, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin@parking.com', admin_password, 'Administrator', 'admin'))
    
    conn.commit()
    conn.close()

# Initialize the database and create tables if they do not exist
init_db()

# Each route below renders a template or redirects to another route
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('parking.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[8]
            flash('Login successful!', 'success')
            if user[8] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        full_name = request.form['full_name']
        address = request.form['address']
        pin_code = request.form['pin_code']
        mobile = request.form['mobile']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        conn = sqlite3.connect('parking.db')
        cursor = conn.cursor()
        
        # Check if username or email already exists
        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone():
            flash('Username or email already exists', 'error')
            conn.close()
            return render_template('register.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, email, password, full_name, address, pin_code, mobile)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, hashed_password, full_name, address, pin_code, mobile))
        
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('login'))
    return redirect(url_for('admin.admin_dashboard'))

@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('login'))
    return redirect(url_for('user.user_dashboard'))

if __name__ == '__main__':
    app.run(debug=True) 