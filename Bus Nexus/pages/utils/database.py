import mysql.connector
import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
import secrets

# Database connection function
@st.cache_resource
def init_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1974Navneet#",
        database="busnexus"
    )

# Execute query with params and return dataframe
def query_with_params(query, params=None):
    conn = init_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.commit()
        return result
    except Exception as e:
        st.error(f"Database error: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()

# Execute an insert/update query and return success/failure
def execute_query(query, params=None):
    conn = init_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return True, cursor.lastrowid
    except Exception as e:
        st.error(f"Database error: {e}")
        conn.rollback()
        return False, None
    finally:
        cursor.close()

# Password hashing utility
def hash_password(password):
    """Hash a password for storing."""
    salt = secrets.token_hex(8)
    h = hashlib.sha256()
    h.update(salt.encode('utf-8'))
    h.update(password.encode('utf-8'))
    return f"{salt}${h.hexdigest()}"

# Password verification
def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt, hash = stored_password.split('$')
    h = hashlib.sha256()
    h.update(salt.encode('utf-8'))
    h.update(provided_password.encode('utf-8'))
    return h.hexdigest() == hash

# User authentication functions
def register_user(first_name, last_name, email, phone, password, role='passenger'):
    # Check if email already exists
    check_query = "SELECT user_id FROM users WHERE email = %s"
    existing_user = query_with_params(check_query, (email,))
    
    if existing_user:
        return False, "Email already registered"
    
    hashed_password = hash_password(password)
    
    insert_query = """
    INSERT INTO users (first_name, last_name, email, phone, role, password)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    success, user_id = execute_query(
        insert_query, 
        (first_name, last_name, email, phone, role, hashed_password)
    )
    
    if success:
        return True, user_id
    else:
        return False, "Registration failed"

def login_user(email, password):
    query = "SELECT user_id, first_name, last_name, email, role, password FROM users WHERE email = %s"
    result = query_with_params(query, (email,))
    
    if not result:
        return False, "Email not found"
    
    user = result[0]
    
    if verify_password(user['password'], password):
        # Remove password from returned user object
        user.pop('password', None)
        return True, user
    else:
        return False, "Invalid password"

# Bus search functions
def get_search_results(origin, destination, travel_date):
    query = """
    SELECT 
        t.trip_id, b.bus_no, b.bus_type, 
        t.departure_datetime, t.arrival_datetime,
        t.seats_available, r.origin, r.destination, 
        r.base_fare
    FROM 
        trip t
    JOIN 
        route r ON t.route_id = r.route_id
    JOIN 
        bus b ON t.bus_id = b.bus_id
    WHERE 
        r.origin = %s
        AND r.destination = %s
        AND DATE(t.departure_datetime) = %s
        AND t.seats_available > 0
        AND t.status = 'scheduled'
    """
    
    if isinstance(travel_date, str):
        travel_date = datetime.strptime(travel_date, "%Y-%m-%d")

    formatted_date = travel_date.strftime("%Y-%m-%d")
    return query_with_params(query, (origin, destination, formatted_date))

# Trip booking functions
def get_trip_details(trip_id):
    query = """
    SELECT 
        t.trip_id, b.bus_id, b.bus_no, b.bus_type, b.capacity,
        t.departure_datetime, t.arrival_datetime,
        t.seats_available, t.status,                 
        r.origin, r.destination, 
        r.base_fare, r.route_id
    FROM 
        trip t
    JOIN 
        route r ON t.route_id = r.route_id
    JOIN 
        bus b ON t.bus_id = b.bus_id
    WHERE 
        t.trip_id = %s
    """
    
    result = query_with_params(query, (trip_id,))
    if result:
        return result[0]
    return None

def add_booking(user_id, trip_id, num_seats, booking_date=None, status="booked"):
    """
    Add a new booking to the database and update the trip's available seats.
    
    Args:
        user_id (int): The ID of the user making the booking (from session state).
        trip_id (int): The ID of the trip being booked.
        num_seats (int): Number of seats to book.
        booking_date (str, optional): Date and time of booking in "YYYY-MM-DD HH:MM:SS" format.
        status (str): Status of the booking (default: "booked").
    
    Returns:
        tuple: (success: bool, booking_id: int or None) - Success status and booking ID if successful.
    """
    conn = init_connection()
    cursor = conn.cursor()

    try:
        # Start a transaction
        conn.start_transaction()

        # Check available seats
        check_seats_query = "SELECT seats_available FROM trip WHERE trip_id = %s"
        cursor.execute(check_seats_query, (trip_id,))
        result = cursor.fetchone()
        if not result or result[0] < num_seats:
            conn.rollback()
            return False, "Insufficient seats available"

        # Calculate total fare (using base_fare from route)
        trip_details = get_trip_details(trip_id)
        if not trip_details:
            conn.rollback()
            return False, "Trip not found"
        total_fare = trip_details['base_fare'] * num_seats

        # Use current timestamp if booking_date is not provided
        if not booking_date:
            booking_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insert the new booking
        insert_booking_query = """
        INSERT INTO booking (user_id, trip_id, total_fare, payment_status, booking_status, booking_datetime)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_booking_query, (user_id, trip_id, total_fare, 'unpaid', status, booking_date))
        booking_id = cursor.lastrowid

        # Insert ticket records with sequential seat numbers
        for seat_num in range(1, num_seats + 1):
            insert_ticket_query = """
            INSERT INTO ticket (booking_id, seat_no, pickup_point, drop_point)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_ticket_query, (booking_id, str(seat_num), trip_details['origin'], trip_details['destination']))

        # Update available seats
        update_seats_query = "UPDATE trip SET seats_available = seats_available - %s WHERE trip_id = %s"
        cursor.execute(update_seats_query, (num_seats, trip_id))

        # Commit the transaction
        conn.commit()
        return True, booking_id

    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()

def create_booking(user_id, trip_id, seats, total_fare, pickup_point, drop_point):
    # Note: This function is kept as is but may be redundant with add_booking
    conn = init_connection()
    cursor = conn.cursor()
    
    try:
        # Start a transaction
        conn.start_transaction()

        # Insert booking record
        booking_query = """
        INSERT INTO booking (user_id, trip_id, total_fare, payment_status, booking_status, booking_datetime)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(booking_query, (
            user_id, trip_id, total_fare, 
            'unpaid', 'booked', datetime.now()
        ))
        
        booking_id = cursor.lastrowid
        
        # Insert ticket records for each seat
        ticket_query = """
        INSERT INTO ticket (booking_id, seat_no, pickup_point, drop_point)
        VALUES (%s, %s, %s, %s)
        """
        
        for seat in seats:
            cursor.execute(ticket_query, (booking_id, seat, pickup_point, drop_point))
        
        # Update available seats
        update_seats_query = """
        UPDATE trip 
        SET seats_available = seats_available - %s
        WHERE trip_id = %s
        """
        
        cursor.execute(update_seats_query, (len(seats), trip_id))
        
        # Commit the transaction
        conn.commit()
        return True, booking_id
        
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()

def get_booking_history(user_id):
    query = """
    SELECT 
        b.booking_id, b.booking_datetime, b.total_fare, 
        b.booking_status, b.payment_status,
        t.departure_datetime, t.arrival_datetime,
        r.origin, r.destination, 
        bus.bus_no, bus.bus_type
    FROM 
        booking b
    JOIN 
        trip t ON b.trip_id = t.trip_id
    JOIN 
        route r ON t.route_id = r.route_id
    JOIN 
        bus ON t.bus_id = bus.bus_id
    WHERE 
        b.user_id = %s
    ORDER BY 
        b.booking_datetime DESC
    """
    
    return query_with_params(query, (user_id,))

def get_booking_tickets(booking_id):
    query = """
    SELECT 
        ticket_id, seat_no, pickup_point, drop_point
    FROM 
        ticket
    WHERE 
        booking_id = %s
    """
    
    return query_with_params(query, (booking_id,))

def cancel_booking(booking_id):
    # Get trip_id and number of tickets
    ticket_query = "SELECT COUNT(*) as ticket_count FROM ticket WHERE booking_id = %s"
    trip_query = "SELECT trip_id FROM booking WHERE booking_id = %s"
    
    conn = init_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get trip_id
        cursor.execute(trip_query, (booking_id,))
        trip_result = cursor.fetchone()
        if not trip_result:
            return False, "Booking not found"
        
        trip_id = trip_result['trip_id']
        
        # Get ticket count
        cursor.execute(ticket_query, (booking_id,))
        ticket_result = cursor.fetchone()
        ticket_count = ticket_result['ticket_count']
        
        # Update booking status
        update_booking_query = """
        UPDATE booking
        SET booking_status = 'cancelled'
        WHERE booking_id = %s
        """
        
        cursor.execute(update_booking_query, (booking_id,))
        
        # Restore seats
        update_seats_query = """
        UPDATE trip 
        SET seats_available = seats_available + %s
        WHERE trip_id = %s
        """
        
        cursor.execute(update_seats_query, (ticket_count, trip_id))
        
        conn.commit()
        return True, "Booking cancelled successfully"
        
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()

# Coordinator dashboard functions
def get_all_buses():
    query = "SELECT bus_id, bus_no, bus_type, capacity, driver_id FROM bus"
    return query_with_params(query)

def add_bus(bus_no, bus_type, capacity, driver_id=None):
    query = """
    INSERT INTO bus (bus_no, bus_type, capacity, driver_id)
    VALUES (%s, %s, %s, %s)
    """
    
    success, bus_id = execute_query(query, (bus_no, bus_type, capacity, driver_id))
    return success, bus_id

def update_bus(bus_id, bus_no, bus_type, capacity, driver_id=None):
    query = """
    UPDATE bus
    SET bus_no = %s, bus_type = %s, capacity = %s, driver_id = %s
    WHERE bus_id = %s
    """
    
    success, _ = execute_query(query, (bus_no, bus_type, capacity, driver_id, bus_id))
    return success

def delete_bus(bus_id):
    # Check if bus is used in any trips
    check_query = "SELECT COUNT(*) as trip_count FROM trip WHERE bus_id = %s"
    result = query_with_params(check_query, (bus_id,))
    
    if result[0]['trip_count'] > 0:
        return False, "Cannot delete bus that is used in trips"
    
    query = "DELETE FROM bus WHERE bus_id = %s"
    success, _ = execute_query(query, (bus_id,))
    return success, None

# Route management functions
def get_all_routes():
    query = "SELECT route_id, origin, destination, distance, base_fare, route_desc FROM route"
    return query_with_params(query)

def add_route(origin, destination, distance, base_fare, origin_lat, origin_lon, destination_lat, destination_lon, route_desc=None):
    query = """
    INSERT INTO route (origin, destination, distance, base_fare, route_desc, origin_lat, origin_lon, destination_lat, destination_lon)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    success, route_id = execute_query(query, (
        origin, destination, distance, base_fare,
        route_desc, origin_lat, origin_lon, destination_lat, destination_lon
    ))
    return success, route_id

def update_route(route_id, origin, destination, distance, base_fare, origin_lat, origin_lon, destination_lat, destination_lon, route_desc=None):
    query = """
    UPDATE route
    SET origin = %s, destination = %s, distance = %s, base_fare = %s, origin_lat = %s, origin_lon = %s, 
        destination_lat = %s, destination_lon = %s, route_desc = %s
    WHERE route_id = %s
    """
    
    success, _ = execute_query(query, (origin, destination, distance, base_fare,
        origin_lat, origin_lon, destination_lat, destination_lon, route_desc, route_id))
    return success

def delete_route(route_id):
    # Check if route is used in any trips
    check_query = "SELECT COUNT(*) as trip_count FROM trip WHERE route_id = %s"
    result = query_with_params(check_query, (route_id,))
    
    if result[0]['trip_count'] > 0:
        return False, "Cannot delete route that is used in trips"
    
    query = "DELETE FROM route WHERE route_id = %s"
    success, _ = execute_query(query, (route_id,))
    return success, None

# Trip management functions
def get_all_trips(include_past=False):
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    query = """
    SELECT 
        t.trip_id, b.bus_no, r.origin, r.destination, 
        t.departure_datetime, t.arrival_datetime, 
        t.seats_available, t.status
    FROM 
        trip t
    JOIN 
        bus b ON t.bus_id = b.bus_id
    JOIN 
        route r ON t.route_id = r.route_id
    """
    
    if not include_past:
        query += " WHERE DATE(t.departure_datetime) >= %s"
        return query_with_params(query, (current_date,))
    
    return query_with_params(query)

def add_trip(bus_id, route_id, departure_datetime, arrival_datetime, seats_available=None):
    # If seats_available is not provided, get bus capacity
    if not seats_available:
        bus_query = "SELECT capacity FROM bus WHERE bus_id = %s"
        result = query_with_params(bus_query, (bus_id,))
        if result:
            seats_available = result[0]['capacity']
        else:
            return False, "Bus not found"
    
    query = """
    INSERT INTO trip (bus_id, route_id, departure_datetime, arrival_datetime, seats_available, status)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    success, trip_id = execute_query(
        query, 
        (bus_id, route_id, departure_datetime, arrival_datetime, seats_available, 'scheduled')
    )
    return success, trip_id

# Dashboard statistics functions
def get_total_bookings():
    query = "SELECT COUNT(*) as total FROM booking WHERE booking_status = 'booked'"
    result = query_with_params(query)
    return result[0]['total'] if result else 0

def get_daily_revenue(start_date=None, end_date=None):
    query = """
    SELECT 
        DATE(booking_datetime) as booking_date,
        SUM(total_fare) as daily_revenue,
        COUNT(*) as booking_count
    FROM 
        booking
    WHERE 
        booking_status = 'booked'
    """
    
    params = []
    
    if start_date:
        query += " AND DATE(booking_datetime) >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND DATE(booking_datetime) <= %s"
        params.append(end_date)
    
    query += " GROUP BY DATE(booking_datetime) ORDER BY booking_date DESC"
    
    return query_with_params(query, tuple(params) if params else None)

def get_route_popularity():
    query = """
    SELECT 
        r.origin, r.destination, COUNT(*) as trip_count
    FROM 
        booking b
    JOIN 
        trip t ON b.trip_id = t.trip_id
    JOIN 
        route r ON t.route_id = r.route_id
    WHERE 
        b.booking_status = 'booked'
    GROUP BY 
        r.origin, r.destination
    ORDER BY 
        trip_count DESC
    LIMIT 10
    """
    
    return query_with_params(query)

def get_popular_destinations():
    query = """
    SELECT 
        r.destination, COUNT(*) as count
    FROM 
        booking b
    JOIN 
        trip t ON b.trip_id = t.trip_id
    JOIN 
        route r ON t.route_id = r.route_id
    WHERE 
        b.booking_status = 'booked'
    GROUP BY 
        r.destination
    ORDER BY 
        count DESC
    LIMIT 10
    """
    
    return query_with_params(query)

# Utility functions
def get_distinct_origins():
    query = "SELECT DISTINCT origin FROM route ORDER BY origin"
    results = query_with_params(query)
    return [result['origin'] for result in results] if results else []

def get_distinct_destinations():
    query = "SELECT DISTINCT destination FROM route ORDER BY destination"
    results = query_with_params(query)
    return [result['destination'] for result in results] if results else []

def get_all_drivers():
    query = "SELECT * FROM driver"
    return query_with_params(query)

def add_driver(first_name, last_name, contact_no, license_no, hired_date):
    query = """
    INSERT INTO driver (first_name, last_name, contact_no, license_no, hired_date)
    VALUES (%s, %s, %s, %s, %s)
    """
    return execute_query(query, (first_name, last_name, contact_no, license_no, hired_date))

def update_driver(driver_id, first_name, last_name, contact_no, license_no, hired_date):
    query = """
    UPDATE driver
    SET first_name = %s, last_name = %s, contact_no = %s, license_no = %s, hired_date = %s
    WHERE driver_id = %s
    """
    return execute_query(query, (first_name, last_name, contact_no, license_no, hired_date, driver_id))

def delete_driver(driver_id):
    # Check if driver is assigned to any bus
    check_query = "SELECT COUNT(*) as bus_count FROM bus WHERE driver_id = %s"
    result = query_with_params(check_query, (driver_id,))
    if result[0]['bus_count'] > 0:
        return False, "Cannot delete driver assigned to a bus"
    query = "DELETE FROM driver WHERE driver_id = %s"
    return execute_query(query, (driver_id,))
result = get_trip_details(1)
print(result)