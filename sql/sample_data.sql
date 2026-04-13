-- ================================================================
-- BusNexus ADBMS — FINAL DATA.SQL (Dynamic + Optimized)
-- ================================================================

-- =========================
-- 1. USERS
-- =========================
INSERT INTO users (name, email, contact_no, role) VALUES
('Anushka Sharma', 'anushka@gmail.com', '9876543210', 'passenger'),
('Rahul Mehta', 'rahul@gmail.com', '9123456780', 'passenger'),
('Priya Singh', 'priya@gmail.com', '9988776655', 'passenger'),
('Admin Coordinator', 'coord@gmail.com', '9000000000', 'coordinator')
ON CONFLICT (email) DO NOTHING;

-- =========================
-- 2. PASSENGERS & COORDINATORS
-- =========================
INSERT INTO passengers (user_id)
SELECT user_id FROM users u
WHERE role = 'passenger'
AND NOT EXISTS (
    SELECT 1 FROM passengers p WHERE p.user_id = u.user_id
);

INSERT INTO coordinators (user_id)
SELECT user_id FROM users u
WHERE role = 'coordinator'
AND NOT EXISTS (
    SELECT 1 FROM coordinators c WHERE c.user_id = u.user_id
);

-- =========================
-- 3. ACCOUNTS
-- =========================
INSERT INTO accounts (user_id, username, email, password_hash)
SELECT user_id,
       LOWER(SPLIT_PART(email, '@', 1)),
       email,
       'hashed_' || user_id
FROM users
ON CONFLICT (email) DO NOTHING;

-- =========================
-- 4. EMPLOYEES
-- =========================
INSERT INTO employees (name, contact_no, role) VALUES
('Driver One', '8888888888', 'driver'),
('Driver Two', '7777777777', 'driver'),
('Maintenance Guy', '6666666666', 'maintenance')
ON CONFLICT DO NOTHING;

-- =========================
-- 5. DRIVERS
-- =========================
INSERT INTO drivers (emp_id, phone_number)
SELECT emp_id, contact_no
FROM employees e
WHERE role = 'driver'
AND NOT EXISTS (
    SELECT 1 FROM drivers d WHERE d.emp_id = e.emp_id
);

-- =========================
-- 6. MAINTENANCE STAFF
-- =========================
INSERT INTO maintenance_staff (emp_id, specialization, shift)
SELECT emp_id, 'engine', 'morning'
FROM employees e
WHERE role = 'maintenance'
AND NOT EXISTS (
    SELECT 1 FROM maintenance_staff m WHERE m.emp_id = e.emp_id
);

-- =========================
-- 7. ROUTES
-- =========================
INSERT INTO routes (source, destination, distance, base_fare) VALUES
('Mumbai', 'Pune', 150, 300),
('Sangli', 'Kolhapur', 50, 100)
ON CONFLICT DO NOTHING;

-- =========================
-- 8. STOPS
-- =========================
INSERT INTO stops (stop_name, location, latitude, longitude) VALUES
('Dadar', 'Mumbai', 19.018, 72.842),
('Lonavala', 'Pune Highway', 18.754, 73.407),
('Pune Station', 'Pune', 18.528, 73.874),
('Sangli Stop', 'Sangli', 16.852, 74.581),
('Kolhapur Stop', 'Kolhapur', 16.705, 74.243)
ON CONFLICT DO NOTHING;

-- =========================
-- 9. ROUTE STOPS (NO HARDCODED IDs)
-- =========================
INSERT INTO route_stops (route_id, stop_id, stop_sequence, arrival_time, departure_time)
SELECT 
    r.route_id,
    s.stop_id,
    seq.seq,
    seq.arrival,
    seq.departure
FROM routes r
JOIN (
    VALUES
    ('Mumbai','Pune','Dadar',1, TIME '08:00', TIME '08:05'),
    ('Mumbai','Pune','Lonavala',2, TIME '10:00', TIME '10:05'),
    ('Mumbai','Pune','Pune Station',3, TIME '12:00', TIME '12:10')
) AS seq(source,destination,stop_name,seq,arrival,departure)
ON r.source = seq.source AND r.destination = seq.destination
JOIN stops s ON s.stop_name = seq.stop_name;
-- =========================
-- 10. BUSES
-- =========================
INSERT INTO buses (bus_type, capacity, amenities, coordinator_id)
SELECT 
    'AC Sleeper', 40, '{"wifi": true, "charging": true}', u.user_id
FROM users u
WHERE role = 'coordinator'
LIMIT 1;

INSERT INTO buses (bus_type, capacity, amenities, coordinator_id)
SELECT 
    'Non-AC Seater', 50, '{"wifi": false}', u.user_id
FROM users u
WHERE role = 'coordinator'
LIMIT 1;

-- =========================
-- 11. TRIPS (DYNAMIC LOOKUPS)
-- =========================
INSERT INTO trips (
    bus_id, route_id, driver_id,
    departure_datetime, arrival_datetime,
    status, seats_available
)
SELECT 
    b.bus_id,
    r.route_id,
    d.emp_id,
    '2026-04-20 08:00:00',
    '2026-04-20 12:00:00',
    'scheduled',
    b.capacity
FROM buses b
JOIN routes r ON r.source='Mumbai' AND r.destination='Pune'
JOIN drivers d ON TRUE
LIMIT 1;

-- =========================
-- 12. BOOKINGS (NO HARDCODED IDs)
-- =========================
INSERT INTO bookings (
    user_id, trip_id, boarding_stop, dropping_stop,
    journey_date, seat_no, booking_status
)
SELECT 
    u.user_id,
    t.trip_id,
    s1.stop_id,
    s2.stop_id,
    '2026-04-20',
    ROW_NUMBER() OVER (),
    'confirmed'
FROM users u
JOIN trips t ON TRUE
JOIN stops s1 ON s1.stop_name = 'Dadar'
JOIN stops s2 ON s2.stop_name = 'Pune Station'
WHERE u.role = 'passenger'
LIMIT 3;

-- =========================
-- 13. TICKETS
-- =========================
INSERT INTO tickets (booking_id, fare, duration)
SELECT booking_id, 300, INTERVAL '4 hours'
FROM bookings b
WHERE NOT EXISTS (
    SELECT 1 FROM tickets t WHERE t.booking_id = b.booking_id
);

-- =========================
-- 14. PAYMENTS
-- =========================
INSERT INTO payments (booking_id, amount, payment_mode, payment_status)
SELECT booking_id, 300, 'upi', 'success'
FROM bookings b
WHERE NOT EXISTS (
    SELECT 1 FROM payments p WHERE p.booking_id = b.booking_id
);

-- =========================
-- 15. TICKET HISTORY
-- =========================
INSERT INTO ticket_history (ticket_no, status, changed_by, remarks)
SELECT 
    t.ticket_no,
    'issued',
    (SELECT user_id FROM users WHERE role='coordinator' LIMIT 1),
    'Ticket generated'
FROM tickets t
WHERE NOT EXISTS (
    SELECT 1 FROM ticket_history th WHERE th.ticket_no = t.ticket_no
);

-- ================================================================
-- END
-- ================================================================