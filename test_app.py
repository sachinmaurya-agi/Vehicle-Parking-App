#!/usr/bin/env python3
"""
Simple test script for Vehicle Parking System
"""

import sqlite3
import os
from datetime import datetime

def test_database_creation():
    """Test if database and tables are created properly"""
    print("Testing database creation...")
    
    if os.path.exists('parking.db'):
        print("👍 Database file exists")
        
        conn = sqlite3.connect('parking.db')
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        required_tables = ['users', 'parking_lots', 'parking_spots', 'reservations']
        
        for table in required_tables:
            if table in tables:
                print(f"👍 Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
        
        # Check if admin user exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if admin:
            print("👍 Admin user exists")
        else:
            print("❌ Admin user missing")
        
        conn.close()
    else:
        print("❌ Database file not found")

def test_sample_data():
    """Test adding sample data"""
    print("\nTesting sample data insertion...")
    
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    try:
        # Add a sample parking lot
        cursor.execute('''
            INSERT INTO parking_lots (prime_location_name, price, address, pin_code, maximum_number_of_spots)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Test Parking Lot', 50.0, '123 Test Street', '123456', 10))
        
        lot_id = cursor.lastrowid
        print(f"👍 Added sample parking lot (ID: {lot_id})")
        
        # Add sample parking spots
        for i in range(10):
            cursor.execute('''
                INSERT INTO parking_spots (lot_id, status)
                VALUES (?, 'A')
            ''', (lot_id,))
        
        print("👍 Added 10 sample parking spots")
        
        # Add a sample user
        cursor.execute('''
            INSERT INTO users (username, email, password, full_name, address, pin_code, mobile, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('testuser', 'test@example.com', 'hashed_password', 'Test User', 'Test Address', '123456', '1234567890', 'user'))
        
        print("👍 Added sample user")
        
        conn.commit()
        print("👍 Sample data inserted successfully")
        
    except Exception as e:
        print(f"❌ Error inserting sample data: {e}")
        conn.rollback()
    
    conn.close()

def main():
    """Main test function"""
    print("=" * 50)
    print("Vehicle Parking System - Test Script")
    print("=" * 50)
    
    test_database_creation()
    test_sample_data()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)
    print("\nTo run the application:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the app: python app.py")
    print("3. Open browser: http://localhost:5000")
    print("\nDefault admin credentials:")
    print("Username: admin")
    print("Password: admin123")

if __name__ == "__main__":
    main() 