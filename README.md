**24f2000305 is my roll number for the college so the this project is entirely done by me**
Vehicle Parking System

A modern and efficient parking management system for 4-wheeler vehicles built with Flask, SQLite, and Bootstrap.

Features

Admin Features

* Dashboard: Overview of all parking lots with statistics
* Parking Lot Management: Add, edit, and delete parking lots
* User Management: View and manage registered users
* Reports: View parking statistics and charts
* Spot Monitoring: Monitor individual parking spots and their status

User Features

* Registration & Login: Secure user authentication
* Parking Booking: Book available parking spots
* Spot Release: Release parking spots and calculate costs
* History: View complete parking history
* Profile Management: Update personal information
* Reports: View personal parking statistics

Technology Stack

Backend: Flask (Python web framework)
Database: SQLite (lightweight, serverless database)
Frontend: HTML5, CSS3, Bootstrap 5
Templating: Jinja2
Authentication: Session-based authentication with password hashing

Installation & Setup

Prerequisites

* Python 3.7 or higher
* pip (Python package installer)

Installation Steps

1. Clone or download the project
   cd vehicle\_parking\_app

2. Install dependencies
   pip install -r requirements.txt

3. Run the application
   python app.py

4. Access the application
   Open your web browser and go to [http://localhost:5000](http://localhost:5000)

Database Setup

The application automatically creates the SQLite database (parking.db) and all required tables when first run. The database includes:

* Users table: Store user information and authentication data
* Parking Lots table: Store parking lot details
* Parking Spots table: Store individual parking spots
* Reservations table: Store parking reservations and history

Default Admin Account
Username: admin
Password: admin123

Usage Guide

For Administrators

1. Login as Admin
   Use the default admin credentials and access the admin dashboard

2. Manage Parking Lots
   Add new parking lots with location, price, and capacity
   Edit existing parking lot details
   Delete parking lots (only if all spots are empty)

3. Monitor Users
   View all registered users
   Delete users (only if they have no active reservations)

4. View Reports
   Check parking lot statistics
   Monitor spot availability
   View recent parking history

For Users

1. Registration
   Create a new account with personal details
   Verify email and contact information

2. Book Parking
   Browse available parking lots
   Select a lot and enter vehicle number
   System automatically assigns the first available spot

3. Release Parking
   Access active reservations from dashboard
   Release parking spot when leaving
   View calculated parking cost

4. View History
   Check complete parking history
   View costs and duration for each parking session
