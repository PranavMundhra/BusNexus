"""
utils/mock_data.py
==================
Phase 1 Mock Data Layer
-----------------------
All data structures mirror the PostgreSQL schema defined in schema.sql.
In Phase 2, replace these with real psycopg2 / SQLAlchemy calls.

Tables mirrored: User, Bus, Route, Stop, Route_Stop, Trip,
                  Booking, Ticket, Payment, Driver, Employee
"""

from datetime import datetime, timedelta, date
import random

# ─────────────────────────────────────────────
# USERS  (mirrors "User" table)
# ─────────────────────────────────────────────
MOCK_USERS = [
    {"user_id": 1, "name": "Arjun Mehta",    "email": "arjun@example.com",  "contact_no": "9876543210", "role": "passenger"},
    {"user_id": 2, "name": "Priya Sharma",   "email": "priya@example.com",  "contact_no": "9812345678", "role": "passenger"},
    {"user_id": 3, "name": "Rohan Desai",    "email": "rohan@example.com",  "contact_no": "9823456789", "role": "passenger"},
    {"user_id": 4, "name": "Admin Coord",    "email": "admin@busnexus.com", "contact_no": "9000000001", "role": "coordinator"},
]

# ─────────────────────────────────────────────
# EMPLOYEES & DRIVERS  (mirrors Employee + Driver)
# ─────────────────────────────────────────────
MOCK_EMPLOYEES = [
    {"emp_id": 1, "name": "Ramesh Kumar",  "contact_no": "9111111111"},
    {"emp_id": 2, "name": "Suresh Patil",  "contact_no": "9222222222"},
    {"emp_id": 3, "name": "Mahesh Yadav",  "contact_no": "9333333333"},
]
MOCK_DRIVERS = [1, 2, 3]   # emp_ids that are drivers

# ─────────────────────────────────────────────
# BUSES  (mirrors Bus table)
# ─────────────────────────────────────────────
MOCK_BUSES = [
    {"bus_id": 1, "bus_type": "AC",      "capacity": 40, "amenities": ["WiFi", "USB Charging", "AC"],          "user_id": 4},
    {"bus_id": 2, "bus_type": "Sleeper", "capacity": 36, "amenities": ["Sleeper Berths", "Blanket", "Reading Light"], "user_id": 4},
    {"bus_id": 3, "bus_type": "General", "capacity": 52, "amenities": ["Fan", "Basic Seating"],                 "user_id": 4},
    {"bus_id": 4, "bus_type": "AC",      "capacity": 44, "amenities": ["WiFi", "AC", "Entertainment Screen"],  "user_id": 4},
]

# ─────────────────────────────────────────────
# ROUTES  (mirrors Route table)
# ─────────────────────────────────────────────
MOCK_ROUTES = [
    {"route_id": 1, "source": "Mumbai",    "destination": "Pune",      "distance": 148, "base_fare": 250.0},
    {"route_id": 2, "source": "Pune",      "destination": "Nashik",    "distance": 212, "base_fare": 320.0},
    {"route_id": 3, "source": "Mumbai",    "destination": "Nashik",    "distance": 167, "base_fare": 280.0},
    {"route_id": 4, "source": "Nashik",    "destination": "Aurangabad","distance": 107, "base_fare": 180.0},
    {"route_id": 5, "source": "Pune",      "destination": "Kolhapur",  "distance": 228, "base_fare": 350.0},
    {"route_id": 6, "source": "Mumbai",    "destination": "Nagpur",    "distance": 840, "base_fare": 700.0},
]

# ─────────────────────────────────────────────
# STOPS  (mirrors Stop table)
# ─────────────────────────────────────────────
MOCK_STOPS = [
    {"stop_id": 1,  "stop_name": "Mumbai Central",    "location": "Mumbai"},
    {"stop_id": 2,  "stop_name": "Dadar",             "location": "Mumbai"},
    {"stop_id": 3,  "stop_name": "Vashi",             "location": "Navi Mumbai"},
    {"stop_id": 4,  "stop_name": "Khopoli",           "location": "Raigad"},
    {"stop_id": 5,  "stop_name": "Pune Station",      "location": "Pune"},
    {"stop_id": 6,  "stop_name": "Shivaji Nagar",     "location": "Pune"},
    {"stop_id": 7,  "stop_name": "Nashik CBS",        "location": "Nashik"},
    {"stop_id": 8,  "stop_name": "Nashik Road",       "location": "Nashik"},
    {"stop_id": 9,  "stop_name": "Aurangabad ST",     "location": "Aurangabad"},
    {"stop_id": 10, "stop_name": "Kolhapur Central",  "location": "Kolhapur"},
    {"stop_id": 11, "stop_name": "Nagpur Central",    "location": "Nagpur"},
    {"stop_id": 12, "stop_name": "Wardha",            "location": "Wardha"},
]

# ─────────────────────────────────────────────
# TRIPS  (mirrors Trip table)
# ─────────────────────────────────────────────
# departure_datetime must be in the future for status='scheduled'
_today = datetime.now()

MOCK_TRIPS = [
    {
        "trip_id": 1,  "bus_id": 1, "route_id": 1, "driver_id": 1,
        "departure_datetime": _today + timedelta(days=1, hours=6),
        "arrival_datetime":   _today + timedelta(days=1, hours=9, minutes=30),
        "seats_available": 12, "status": "scheduled",
    },
    {
        "trip_id": 2,  "bus_id": 2, "route_id": 1, "driver_id": 2,
        "departure_datetime": _today + timedelta(days=1, hours=22),
        "arrival_datetime":   _today + timedelta(days=2, hours=1, minutes=30),
        "seats_available": 6, "status": "scheduled",
    },
    {
        "trip_id": 3,  "bus_id": 3, "route_id": 2, "driver_id": 3,
        "departure_datetime": _today + timedelta(days=2, hours=8),
        "arrival_datetime":   _today + timedelta(days=2, hours=13),
        "seats_available": 20, "status": "scheduled",
    },
    {
        "trip_id": 4,  "bus_id": 4, "route_id": 3, "driver_id": 1,
        "departure_datetime": _today + timedelta(days=1, hours=7, minutes=30),
        "arrival_datetime":   _today + timedelta(days=1, hours=11),
        "seats_available": 0, "status": "scheduled",     # Full → waitlist scenario
    },
    {
        "trip_id": 5,  "bus_id": 1, "route_id": 4, "driver_id": 2,
        "departure_datetime": _today + timedelta(days=3, hours=9),
        "arrival_datetime":   _today + timedelta(days=3, hours=12),
        "seats_available": 30, "status": "scheduled",
    },
    {
        "trip_id": 6,  "bus_id": 2, "route_id": 6, "driver_id": 3,
        "departure_datetime": _today + timedelta(days=2, hours=20),
        "arrival_datetime":   _today + timedelta(days=3, hours=10),
        "seats_available": 18, "status": "scheduled",
    },
]

# ─────────────────────────────────────────────
# BOOKINGS  (mirrors Booking table)
# ─────────────────────────────────────────────
MOCK_BOOKINGS = [
    {
        "booking_id": 1001, "user_id": 1, "trip_id": 1,
        "boarding_stop": 1, "dropping_stop": 5,
        "journey_date": date.today() + timedelta(days=1),
        "seat_no": 5, "booking_status": "confirmed",
        "booking_time": datetime.now() - timedelta(hours=3),
    },
    {
        "booking_id": 1002, "user_id": 2, "trip_id": 3,
        "boarding_stop": 6, "dropping_stop": 7,
        "journey_date": date.today() + timedelta(days=2),
        "seat_no": 12, "booking_status": "confirmed",
        "booking_time": datetime.now() - timedelta(hours=1),
    },
    {
        "booking_id": 1003, "user_id": 1, "trip_id": 2,
        "boarding_stop": 2, "dropping_stop": 6,
        "journey_date": date.today() + timedelta(days=1),
        "seat_no": 8, "booking_status": "cancelled",
        "booking_time": datetime.now() - timedelta(days=1),
    },
]

# ─────────────────────────────────────────────
# TICKETS  (mirrors Ticket table; auto-generated by trigger)
# ─────────────────────────────────────────────
MOCK_TICKETS = [
    {"ticket_no": 5001, "booking_id": 1001, "fare": 350.0,  "duration": "3h 30m"},
    {"ticket_no": 5002, "booking_id": 1002, "fare": 420.0,  "duration": "5h 00m"},
]

# ─────────────────────────────────────────────
# PAYMENTS  (mirrors Payment table)
# ─────────────────────────────────────────────
MOCK_PAYMENTS = [
    {"payment_id": 9001, "booking_id": 1001, "amount": 350.0, "payment_mode": "UPI",         "payment_date": datetime.now() - timedelta(hours=3)},
    {"payment_id": 9002, "booking_id": 1002, "amount": 420.0, "payment_mode": "Credit Card",  "payment_date": datetime.now() - timedelta(hours=1)},
]


# ─────────────────────────────────────────────
# HELPER FUNCTIONS  (mirror SQL functions)
# ─────────────────────────────────────────────

def calculate_fare(route_id: int, seat_type: str) -> float:
    """
    Mirrors: calculate_fare(r_id INT, seat_type TEXT) → NUMERIC
    Adds surcharge based on seat type over base_fare.
    """
    route = next((r for r in MOCK_ROUTES if r["route_id"] == route_id), None)
    if not route:
        return 0.0
    base = route["base_fare"]
    if seat_type == "AC":
        return base + 100
    elif seat_type == "Sleeper":
        return base + 200
    return base  # General


def get_available_seats(trip_id: int) -> int:
    """Mirrors: get_available_seats(t_id INT) → INT"""
    trip = next((t for t in MOCK_TRIPS if t["trip_id"] == trip_id), None)
    return trip["seats_available"] if trip else 0


def passenger_booking_count(user_id: int) -> int:
    """Mirrors: passenger_booking_count(u_id INT) → INT"""
    return sum(1 for b in MOCK_BOOKINGS if b["user_id"] == user_id)


def get_route_by_id(route_id: int) -> dict:
    return next((r for r in MOCK_ROUTES if r["route_id"] == route_id), {})


def get_bus_by_id(bus_id: int) -> dict:
    return next((b for b in MOCK_BUSES if b["bus_id"] == bus_id), {})


def get_driver_name(driver_id: int) -> str:
    emp = next((e for e in MOCK_EMPLOYEES if e["emp_id"] == driver_id), None)
    return emp["name"] if emp else "Unknown"


def get_stop_name(stop_id: int) -> str:
    stop = next((s for s in MOCK_STOPS if s["stop_id"] == stop_id), None)
    return stop["stop_name"] if stop else "Unknown"


def search_trips(source: str, destination: str, travel_date: date) -> list:
    """
    Mirrors: SELECT Trip JOIN Route WHERE source=? AND destination=?
    Filters by source, destination, date, and status='scheduled'
    """
    results = []
    for trip in MOCK_TRIPS:
        route = get_route_by_id(trip["route_id"])
        dep_date = trip["departure_datetime"].date()
        if (
            route.get("source") == source
            and route.get("destination") == destination
            and dep_date == travel_date
            and trip["status"] == "scheduled"
        ):
            results.append({**trip, "route": route, "bus": get_bus_by_id(trip["bus_id"])})
    return results


def get_user_bookings(user_id: int) -> list:
    """
    Mirrors: SELECT * FROM booking_summary WHERE user_id = ?
    Returns enriched booking records (joining route, trip, stop names).
    """
    enriched = []
    for b in MOCK_BOOKINGS:
        if b["user_id"] == user_id:
            trip   = next((t for t in MOCK_TRIPS  if t["trip_id"]   == b["trip_id"]),    {})
            route  = get_route_by_id(trip.get("route_id", -1))
            ticket = next((t for t in MOCK_TICKETS if t["booking_id"] == b["booking_id"]), {})
            payment= next((p for p in MOCK_PAYMENTS if p["booking_id"] == b["booking_id"]), {})
            enriched.append({
                **b,
                "route_source":      route.get("source", "N/A"),
                "route_destination": route.get("destination", "N/A"),
                "departure":         trip.get("departure_datetime"),
                "boarding_name":     get_stop_name(b["boarding_stop"]),
                "dropping_name":     get_stop_name(b["dropping_stop"]),
                "fare":              ticket.get("fare", "N/A"),
                "duration":          ticket.get("duration", "N/A"),
                "payment_mode":      payment.get("payment_mode", "N/A"),
                "ticket_no":         ticket.get("ticket_no", "N/A"),
            })
    return enriched
