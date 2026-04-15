import psycopg2
import os
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DB_CONFIG = {
    "dbname": "busnexus",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}


# ─────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────
def get_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print("DB Connection Error:", e)
        return None


# ─────────────────────────────────────────────
# SAFE EXECUTOR (FIXES YOUR ERROR)
# ─────────────────────────────────────────────
def execute_query(query, params=None, fetch=False, fetchone=False):
    conn = get_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(query, params)

            result = None
            if fetch:
                result = cur.fetchall()
            elif fetchone:
                result = cur.fetchone()

        conn.commit()   # ✅ COMMIT ALWAYS BEFORE RETURN
        return result

    except Exception as e:
        conn.rollback()
        print("Query Error:", e)
        raise e

    finally:
        conn.close()

# ─────────────────────────────────────────────
# 🔍 SEARCH TRIPS (JOINED DATA)
# ─────────────────────────────────────────────
def search_trips(source, destination, travel_date):
    query = """
    SELECT 
        t.trip_id,
        t.route_id,   -- ✅ ADD THIS
        t.departure_datetime,
        t.arrival_datetime,
        t.seats_available,
        r.source,
        r.destination,
        r.base_fare,
        b.bus_type
    FROM trip t
    JOIN route r ON t.route_id = r.route_id
    JOIN bus b ON t.bus_id = b.bus_id
    WHERE r.source = %s
      AND r.destination = %s
      AND DATE(t.departure_datetime) = %s
      AND t.status = 'scheduled'
    """

    rows = execute_query(query, (source, destination, travel_date), fetch=True)

    trips = []
    for row in rows:
        trips.append({
            "trip_id": row[0],
            "route_id": row[1],  # ✅ ADD THIS
            "departure_datetime": row[2],
            "arrival_datetime": row[3],
            "seats_available": row[4],
            "route": {
                "source": row[5],
                "destination": row[6],
            },
            "bus": {
                "bus_type": row[8]
            },
            "base_fare": row[7]
        })

    return trips

# ─────────────────────────────────────────────
# 💰 FARE CALCULATION
# ─────────────────────────────────────────────
def calculate_fare(route_id, bus_type):
    query = "SELECT base_fare FROM Route WHERE route_id = %s"
    result = execute_query(query, (route_id,), fetchone=True)

    base = result[0] if result else 100

    multiplier = {
        "AC": 1.5,
        "Sleeper": 1.3,
        "General": 1.0
    }

    return int(base * multiplier.get(bus_type, 1))


# ─────────────────────────────────────────────
# 🎟 CREATE BOOKING
# ─────────────────────────────────────────────
def create_booking(user_id, trip_id, boarding_stop, dropping_stop, seat_no):
    query = """
    INSERT INTO booking (
        user_id,
        trip_id,
        boarding_stop,
        dropping_stop,
        journey_date,
        seat_no,
        booking_status,
        booking_time
    )
    VALUES (%s, %s, %s, %s, CURRENT_DATE, %s, 'confirmed', NOW())
    """

    execute_query(query, (
        user_id,
        trip_id,
        boarding_stop,
        dropping_stop,
        seat_no
    ))

# ─────────────────────────────────────────────
# ❌ CANCEL BOOKING
# ─────────────────────────────────────────────
def cancel_booking(booking_id):
    query = """
    UPDATE Booking
    SET booking_status = 'cancelled'
    WHERE booking_id = %s
    """
    execute_query(query, (booking_id,))


# ─────────────────────────────────────────────
# 📄 USER BOOKINGS (JOINED)
# ─────────────────────────────────────────────
def get_user_bookings(user_id):
    query = """
    SELECT 
        b.booking_id,
        b.booking_status,
        b.seat_no,
        b.booking_time,
        t.departure_datetime,
        r.source,
        r.destination,
        r.base_fare
    FROM Booking b
    JOIN Trip t ON b.trip_id = t.trip_id
    JOIN Route r ON t.route_id = r.route_id
    WHERE b.user_id = %s
    ORDER BY b.booking_time DESC
    """

    rows = execute_query(query, (user_id,), fetch=True)

    bookings = []
    for r in rows:
        bookings.append({
            "booking_id": r[0],
            "booking_status": r[1],
            "seat_no": r[2],
            "booking_time": r[3],
            "departure": r[4],
            "route_source": r[5],
            "route_destination": r[6],
            "fare": r[7],
            "payment_mode": "UPI",
            "duration": "N/A"
        })

    return bookings


# ─────────────────────────────────────────────
# 📊 STATS
# ─────────────────────────────────────────────
def passenger_booking_count(user_id):
    query = "SELECT COUNT(*) FROM Booking WHERE user_id = %s"
    result = execute_query(query, (user_id,), fetchone=True)
    return result[0] if result else 0


def get_available_seats(trip_id):
    query = "SELECT seats_available FROM Trip WHERE trip_id = %s"
    result = execute_query(query, (trip_id,), fetchone=True)
    return result[0] if result else 0


# ─────────────────────────────────────────────
# 🔐 AUTH — SIGNUP
# ─────────────────────────────────────────────
def create_user(name, email, password):
    query = """
    INSERT INTO users (name, email, password)
    VALUES (%s, %s, %s)
    RETURNING user_id
    """
    result = execute_query(query, (name, email, password), fetchone=True)
    return result[0] if result else None


# ─────────────────────────────────────────────
# 🔐 AUTH — LOGIN
# ─────────────────────────────────────────────
def authenticate_user(email, password):
    query = """
    SELECT user_id, name
    FROM users
    WHERE email = %s AND password = %s
    """
    result = execute_query(query, (email, password), fetchone=True)

    if result:
        return {
            "user_id": result[0],
            "name": result[1]
        }
    return None