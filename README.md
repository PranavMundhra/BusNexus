# BusNexus — Streamlit Frontend

## Setup

### 1. Install dependencies
```bash
pip install streamlit psycopg2-binary pandas plotly
```

### 2. Configure database connection
Create `.streamlit/secrets.toml` next to `busnexus_app.py`:
```toml
DB_HOST     = "localhost"
DB_NAME     = "busnexus"
DB_USER     = "postgres"
DB_PASSWORD = "your_password"
DB_PORT     = "5432"
```

### 3. Initialize the database
Run SQL files **in order**:
```
schema.sql → functions.sql → triggers.sql → procedures.sql → sample_data.sql → other_features.sql
```

### 4. Run the app
```bash
streamlit run busnexus_app.py
```
App opens at http://localhost:8501

---

## Demo Accounts (any password accepted)
| Email | Role |
|---|---|
| anushka@gmail.com | Passenger |
| rahul@gmail.com | Passenger |
| priya@gmail.com | Passenger |
| coord@gmail.com | Coordinator |

---

## Feature Map

### Passenger
| UI Page | Backend Used |
|---|---|
| Dashboard | Direct queries + ticket_history |
| Browse Trips | `available_trips` view + filters |
| Book Trip | `get_stops_for_trip()`, `get_seat_map()`, `calculate_fare()`, `CALL create_booking()` |
| My Bookings | `booking_summary` view + `CALL cancel_booking()` |
| My Tickets | `tickets`, `ticket_history` |
| Payments | `payments` table |

### Coordinator
| UI Page | Backend Used |
|---|---|
| Analytics | Aggregated queries, revenue, occupancy |
| All Bookings | Full `bookings` JOIN query |
| Fleet & Trips | `trip_with_stops` view, routes & stops |
| Ticket Registry | `ticket_full_history` view |
| Users | `users` + `passenger_booking_count()` |