SELECT * FROM users;
SELECT * FROM passengers;
SELECT * FROM coordinators;
SELECT * FROM employees;
SELECT * FROM drivers;
SELECT * FROM maintenance_staff;

SELECT p.*
FROM passengers p
LEFT JOIN users u ON p.user_id = u.user_id
WHERE u.user_id IS NULL;
-- should return 0 queries

SELECT d.emp_id
FROM drivers d
JOIN maintenance_staff m ON d.emp_id = m.emp_id;
-- should return 0 queries

SELECT u.user_id, u.role, 
       CASE 
           WHEN p.user_id IS NOT NULL THEN 'passenger'
           WHEN c.user_id IS NOT NULL THEN 'coordinator'
       END AS subtype
FROM users u
LEFT JOIN passengers p ON u.user_id = p.user_id
LEFT JOIN coordinators c ON u.user_id = c.user_id;
-- role matches subtype

SELECT r.source, r.destination, s.stop_name, rs.stop_sequence
FROM route_stops rs
JOIN routes r ON rs.route_id = r.route_id
JOIN stops s ON rs.stop_id = s.stop_id
ORDER BY rs.stop_sequence;

SELECT 
    t.trip_id,
    r.source || ' → ' || r.destination AS route,
    t.departure_datetime,
    t.arrival_datetime,
    t.seats_available
FROM trips t
JOIN routes r ON t.route_id = r.route_id;

SELECT 
    u.name,
    r.source || ' → ' || r.destination AS route,
    s1.stop_name AS boarding,
    s2.stop_name AS dropping,
    b.seat_no,
    b.booking_status
FROM bookings b
JOIN users u ON b.user_id = u.user_id
JOIN trips t ON b.trip_id = t.trip_id
JOIN routes r ON t.route_id = r.route_id
JOIN stops s1 ON b.boarding_stop = s1.stop_id
JOIN stops s2 ON b.dropping_stop = s2.stop_id;

SELECT 
    u.name,
    p.amount,
    p.payment_mode,
    t.fare,
    t.duration
FROM payments p
JOIN bookings b ON p.booking_id = b.booking_id
JOIN users u ON b.user_id = u.user_id
JOIN tickets t ON b.booking_id = t.booking_id;

SELECT 
    r.source || ' → ' || r.destination AS route,
    SUM(p.amount) AS total_revenue
FROM payments p
JOIN bookings b ON p.booking_id = b.booking_id
JOIN trips t ON b.trip_id = t.trip_id
JOIN routes r ON t.route_id = r.route_id
GROUP BY route;

SELECT 
    t.trip_id,
    t.seats_available,
    COUNT(b.booking_id) AS booked_seats,
    (COUNT(b.booking_id)::FLOAT / t.seats_available) * 100 AS occupancy_percent
FROM trips t
LEFT JOIN bookings b ON t.trip_id = b.trip_id
GROUP BY t.trip_id, t.seats_available;

INSERT INTO bookings (user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
VALUES (999, 1, 1, 2, '2026-04-20', 10, 'confirmed');
-- should fail

SELECT 
    tgname AS trigger_name,
    relname AS table_name
FROM pg_trigger t
JOIN pg_class c ON t.tgrelid = c.oid
WHERE NOT t.tgisinternal;

INSERT INTO bookings (
    user_id, trip_id, boarding_stop, dropping_stop,
    journey_date, seat_no, booking_status
)
SELECT 
    u.user_id,
    t.trip_id,
    s1.stop_id,
    s2.stop_id,
    CURRENT_DATE - INTERVAL '1 day',
    5,
    'confirmed'
FROM users u
JOIN trips t ON TRUE
JOIN stops s1 ON s1.stop_name='Dadar'
JOIN stops s2 ON s2.stop_name='Pune Station'
WHERE u.role='passenger'
LIMIT 1;

INSERT INTO bookings (
    user_id, trip_id, boarding_stop, dropping_stop,
    journey_date, seat_no, booking_status
)
SELECT 
    u.user_id,
    t.trip_id,
    s2.stop_id,  -- Pune
    s1.stop_id,  -- Dadar (wrong)
    CURRENT_DATE + 1,
    6,
    'confirmed'
FROM users u
JOIN trips t ON TRUE
JOIN stops s1 ON s1.stop_name='Dadar'
JOIN stops s2 ON s2.stop_name='Pune Station'
WHERE u.role='passenger'
LIMIT 1;

SELECT trip_id, seats_available FROM trips;

UPDATE bookings
SET booking_status = 'cancelled'
WHERE booking_id = (SELECT booking_id FROM bookings LIMIT 1);

SELECT trip_id, seats_available FROM trips;

SELECT COUNT(*) FROM tickets;

SELECT COUNT(*) FROM ticket_history;

UPDATE bookings
SET booking_status = 'cancelled'
WHERE booking_id = (SELECT booking_id FROM bookings LIMIT 1);

SELECT proname, pg_get_function_arguments(p.oid) AS args
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public';

SELECT proname, pg_get_function_arguments(p.oid) AS args
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
AND p.prokind = 'p';

SELECT get_available_seats(
    (SELECT trip_id FROM trips LIMIT 1)
);

SELECT calculate_fare(
    (SELECT route_id FROM routes WHERE source='Mumbai' AND destination='Pune'),
    'AC'
);

SELECT passenger_booking_count(
    (SELECT user_id FROM users WHERE role='passenger' LIMIT 1)
);

SELECT * FROM get_stops_for_trip(
    (SELECT trip_id FROM trips LIMIT 1)
);

SELECT * FROM get_seat_map(
    (SELECT trip_id FROM trips LIMIT 1)
);

DO $$
DECLARE
    v_user_id INT;
    v_trip_id INT;
    v_board INT;
    v_drop INT;
BEGIN
    SELECT user_id INTO v_user_id 
    FROM users WHERE role='passenger' LIMIT 1;

    SELECT trip_id INTO v_trip_id 
    FROM trips LIMIT 1;

    SELECT stop_id INTO v_board 
    FROM stops WHERE stop_name='Dadar';

    SELECT stop_id INTO v_drop 
    FROM stops WHERE stop_name='Pune Station';

    CALL create_booking(
        v_user_id,
        v_trip_id,
        v_board,
        v_drop,
        15
    );
END $$;

SELECT * FROM bookings ORDER BY booking_id DESC LIMIT 1;
SELECT * FROM tickets ORDER BY ticket_no DESC LIMIT 1;
SELECT seats_available FROM trips;