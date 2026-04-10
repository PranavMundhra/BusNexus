-- ================================================================
-- BusNexus ADBMS — Demo Queries
-- File: sql/demo_queries.sql
--
-- Purpose: Show faculty that every ADBMS feature is working.
-- Run AFTER sample_data.sql
-- Each section is self-contained — run them one at a time.
-- ================================================================


-- ================================================================
-- SECTION 1: VERIFY BASE DATA
-- ================================================================

-- All users with their roles
SELECT u.user_id, u.name, u.email,
       CASE
           WHEN p.user_id IS NOT NULL THEN 'Passenger'
           WHEN c.user_id IS NOT NULL THEN 'Coordinator'
       END AS role
FROM "User" u
LEFT JOIN Passenger p ON u.user_id = p.user_id
LEFT JOIN Coordinator c ON u.user_id = c.user_id;

-- All buses with JSONB amenities
SELECT bus_id, bus_type, capacity, amenities FROM Bus;

-- All trips with route info
SELECT t.trip_id, r.source, r.destination,
       t.departure_datetime, t.arrival_datetime,
       t.seats_available, t.status
FROM Trip t
JOIN Route r ON t.route_id = r.route_id;


-- ================================================================
-- SECTION 2: TRIGGER DEMO — Auto Ticket Generation
-- Shows: AFTER INSERT trigger on Booking created Ticket rows
--        without any manual INSERT into Ticket
-- ================================================================

-- Check tickets were auto-created (no manual inserts were done)
SELECT t.ticket_no, t.booking_id, t.fare, t.duration,
       u.name AS passenger,
       r.source, r.destination
FROM Ticket t
JOIN Booking b  ON t.booking_id  = b.booking_id
JOIN "User" u   ON b.user_id     = u.user_id
JOIN Trip tr    ON b.trip_id     = tr.trip_id
JOIN Route r    ON tr.route_id   = r.route_id;

-- Confirm ticket count matches booking count (trigger worked for all)
SELECT
    (SELECT COUNT(*) FROM Booking) AS total_bookings,
    (SELECT COUNT(*) FROM Ticket)  AS total_tickets;


-- ================================================================
-- SECTION 3: TRIGGER DEMO — Stop Validation
-- Shows: BEFORE INSERT trigger blocks invalid booking
-- ================================================================

-- This INSERT should FAIL with: "Boarding and dropping stops cannot be same"
-- Uncomment to demonstrate the trigger blocking it live:

-- INSERT INTO Booking (user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
-- VALUES (3, 1, 4, 4, '2026-04-15', 20, 'confirmed');


-- ================================================================
-- SECTION 4: PROCEDURE DEMO — create_booking with concurrency lock
-- Shows: Row-level locking (FOR UPDATE), seat decrement, waitlist
-- ================================================================

-- Check seats before calling procedure
SELECT trip_id, seats_available FROM Trip WHERE trip_id = 1;

-- Call the booking procedure
BEGIN;
CALL create_booking(3, 1, 1, 4, 22);
COMMIT;

-- Check seats decreased by 1 after booking
SELECT trip_id, seats_available FROM Trip WHERE trip_id = 1;

-- Check the new booking was created
SELECT * FROM Booking WHERE user_id = 3 AND trip_id = 1 ORDER BY booking_id DESC LIMIT 1;


-- ================================================================
-- SECTION 5: PROCEDURE DEMO — cancel_booking
-- Shows: Status update + seat restoration
-- ================================================================

-- Cancel booking_id = 2
CALL cancel_booking(2);

-- Verify: booking status should be 'cancelled'
SELECT booking_id, booking_status FROM Booking WHERE booking_id = 2;

-- Verify: seats_available on trip 1 should have gone back up by 1
SELECT trip_id, seats_available FROM Trip WHERE trip_id = 1;


-- ================================================================
-- SECTION 6: FUNCTION DEMO — calculate_fare
-- Shows: Function returning computed value
-- ================================================================

-- Fare for route 1 (base 250), AC type (+100) = 350
SELECT calculate_fare(1, 'AC') AS ac_fare;

-- Fare for route 1 (base 250), Sleeper type (+200) = 450
SELECT calculate_fare(1, 'Sleeper') AS sleeper_fare;

-- Fare for route 1, standard = base only
SELECT calculate_fare(1, 'Standard') AS standard_fare;


-- ================================================================
-- SECTION 7: FUNCTION DEMO — get_available_seats
-- Shows: Reusable abstracted seat check
-- ================================================================

SELECT get_available_seats(1) AS seats_on_trip_1;
SELECT get_available_seats(3) AS seats_on_trip_3;


-- ================================================================
-- SECTION 8: FUNCTION DEMO — passenger_booking_count
-- Shows: Aggregate reporting via function
-- ================================================================

SELECT passenger_booking_count(1) AS anushka_bookings;
SELECT passenger_booking_count(2) AS pranav_bookings;

-- All passengers with booking counts
SELECT u.name, passenger_booking_count(u.user_id) AS total_bookings
FROM "User" u
JOIN Passenger p ON u.user_id = p.user_id
ORDER BY total_bookings DESC;


-- ================================================================
-- SECTION 9: VIEW DEMO — booking_summary
-- Shows: Multi-table abstraction, used for reporting
-- ================================================================

SELECT * FROM booking_summary;

-- Filter only confirmed bookings from the view
SELECT * FROM booking_summary WHERE booking_status = 'confirmed';


-- ================================================================
-- SECTION 10: TEMPORAL ATTRIBUTE DEMO
-- Shows: booking_time timestamp automatically recorded
-- ================================================================

SELECT booking_id, user_id, booking_status, booking_time
FROM Booking
ORDER BY booking_time DESC;

-- Bookings made in the last 24 hours
SELECT booking_id, user_id, booking_time
FROM Booking
WHERE booking_time >= CURRENT_TIMESTAMP - INTERVAL '24 hours';


-- ================================================================
-- SECTION 11: JSONB DEMO — Semi-Structured Data
-- Shows: Querying inside JSONB amenities column
-- ================================================================

-- All buses that have WiFi
SELECT bus_id, bus_type, amenities
FROM Bus
WHERE amenities->>'wifi' = 'true';

-- All buses that are AC
SELECT bus_id, bus_type, capacity
FROM Bus
WHERE amenities->>'ac' = 'true';

-- All buses with both WiFi and charging
SELECT bus_id, bus_type
FROM Bus
WHERE amenities->>'wifi' = 'true'
  AND amenities->>'charging' = 'true';


-- ================================================================
-- SECTION 12: CONSTRAINT DEMO — CHECK constraints
-- Shows: Domain integrity enforcement
-- ================================================================

-- This should FAIL: invalid booking_status value
-- INSERT INTO Booking (user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
-- VALUES (1, 2, 1, 4, '2026-04-15', 30, 'pending');   -- 'pending' not allowed

-- This should FAIL: seat_no <= 0
-- INSERT INTO Booking (user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
-- VALUES (1, 2, 1, 4, '2026-04-15', 0, 'confirmed');  -- seat_no must be > 0

-- This should FAIL: duplicate payment for same booking
-- INSERT INTO Payment (booking_id, amount, payment_mode)
-- VALUES (1, 350.00, 'Cash');  -- booking_id 1 already has a payment (UNIQUE constraint)


-- ================================================================
-- SECTION 13: INDEX DEMO — Query Optimization
-- Shows: Indexes on Booking(user_id) and Booking(trip_id)
-- ================================================================

-- Use EXPLAIN to show index is being used
EXPLAIN SELECT * FROM Booking WHERE user_id = 1;
EXPLAIN SELECT * FROM Booking WHERE trip_id = 1;


-- ================================================================
-- SECTION 14: TRIGGER DEMO — Trip Status Auto-Update
-- Shows: BEFORE UPDATE trigger sets status = 'completed'
--        when departure_datetime is in the past
-- ================================================================

-- Update trip 1 to a past datetime — trigger should mark it 'completed'
UPDATE Trip
SET departure_datetime = '2024-01-01 06:00:00',
    arrival_datetime   = '2024-01-01 09:00:00'
WHERE trip_id = 1;

-- Verify status changed to 'completed'
SELECT trip_id, departure_datetime, status FROM Trip WHERE trip_id = 1;

-- Reset it back for further demos
UPDATE Trip
SET departure_datetime = '2026-04-15 06:00:00',
    arrival_datetime   = '2026-04-15 09:00:00',
    status             = 'scheduled'
WHERE trip_id = 1;


-- ================================================================
-- SECTION 15: ANALYTICS — Reporting Queries
-- Shows: Aggregate queries, GROUP BY, useful reporting
-- ================================================================

-- Total revenue per route
SELECT r.source, r.destination, SUM(p.amount) AS total_revenue
FROM Payment p
JOIN Booking b  ON p.booking_id = b.booking_id
JOIN Trip t     ON b.trip_id    = t.trip_id
JOIN Route r    ON t.route_id   = r.route_id
GROUP BY r.source, r.destination
ORDER BY total_revenue DESC;

-- Busiest trip by number of bookings
SELECT b.trip_id, r.source, r.destination,
       COUNT(b.booking_id) AS bookings_count
FROM Booking b
JOIN Trip t  ON b.trip_id   = t.trip_id
JOIN Route r ON t.route_id  = r.route_id
GROUP BY b.trip_id, r.source, r.destination
ORDER BY bookings_count DESC;

-- Seat occupancy per trip
SELECT t.trip_id, r.source, r.destination,
       b_cap.capacity AS total_seats,
       t.seats_available AS remaining,
       (b_cap.capacity - t.seats_available) AS booked
FROM Trip t
JOIN Route r ON t.route_id = r.route_id
JOIN Bus b_cap ON t.bus_id = b_cap.bus_id;

-- Payment mode breakdown
SELECT payment_mode, COUNT(*) AS count, SUM(amount) AS total
FROM Payment
GROUP BY payment_mode
ORDER BY total DESC;
