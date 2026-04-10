-- ================================================================
-- BusNexus ADBMS — Sample Data
-- File: sql/sample_data.sql
--
-- Run order:
--   1. schema.sql
--   2. functions.sql
--   3. triggers.sql        (ticket auto-generates on Booking insert)
--   4. procedures.sql
--   5. other_features.sql
--   6. sample_data.sql     ← this file
--
-- NOTE: Ticket inserts are NOT here — the generate_ticket trigger
--       fires automatically AFTER INSERT on Booking and handles it.
-- ================================================================


-- ================================================================
-- 1. USERS  (superclass)
-- ================================================================
INSERT INTO "User" (name, email, contact_no) VALUES
('Anushka Sharma',    'anushka@busnexus.com',  '9876543201'),
('Pranav Mundhra',    'pranav@busnexus.com',   '9876543202'),
('Riya Desai',        'riya@busnexus.com',     '9876543203'),
('Karan Mehta',       'karan@busnexus.com',    '9876543204'),
('Sneha Patil',       'sneha@busnexus.com',    '9876543205'),
('Rahul Joshi',       'rahul@busnexus.com',    '9876543206'),
('Meera Kapoor',      'meera@busnexus.com',    '9876543207');


-- ================================================================
-- 2. PASSENGERS  (subclass — users 1-5)
-- ================================================================
INSERT INTO Passenger (user_id) VALUES (1),(2),(3),(4),(5);


-- ================================================================
-- 3. COORDINATORS  (subclass — users 6-7)
-- ================================================================
INSERT INTO Coordinator (user_id) VALUES (6),(7);


-- ================================================================
-- 4. EMPLOYEES  (superclass)
-- ================================================================
INSERT INTO Employee (name, contact_no) VALUES
('Suresh Naik',    '9112233440'),
('Ramesh Tiwari',  '9112233441'),
('Vijay Rao',      '9112233442'),
('Manoj Pawar',    '9112233443');


-- ================================================================
-- 5. DRIVERS  (subclass — employees 1-3)
-- ================================================================
INSERT INTO Driver (emp_id) VALUES (1),(2),(3);


-- ================================================================
-- 6. BUSES
--    amenities = JSONB  (semi-structured data)
--    user_id   = coordinator who owns this bus
-- ================================================================
INSERT INTO Bus (bus_type, capacity, amenities, user_id) VALUES
('AC Sleeper',     40, '{"wifi": true,  "ac": true,  "charging": true,  "blanket": true}',  6),
('AC Seater',      50, '{"wifi": true,  "ac": true,  "charging": true,  "blanket": false}', 6),
('Non-AC Sleeper', 36, '{"wifi": false, "ac": false, "charging": true,  "blanket": true}',  7),
('Non-AC Seater',  55, '{"wifi": false, "ac": false, "charging": false, "blanket": false}', 7);


-- ================================================================
-- 7. ROUTES
-- ================================================================
INSERT INTO Route (source, destination, distance, base_fare) VALUES
('Mumbai',  'Pune',       150,  250.00),
('Pune',    'Nashik',     210,  350.00),
('Mumbai',  'Nashik',     170,  300.00),
('Nashik',  'Aurangabad', 110,  200.00),
('Mumbai',  'Aurangabad', 340,  500.00);


-- ================================================================
-- 8. STOPS
-- ================================================================
INSERT INTO Stop (stop_name, location) VALUES
('Mumbai Central',       'Mumbai'),
('Dadar',                'Mumbai'),
('Khopoli',              'Raigad'),
('Pune Station',         'Pune'),
('Shivajinagar',         'Pune'),
('Nashik Road',          'Nashik'),
('Nashik CBS',           'Nashik'),
('Aurangabad Bus Stand', 'Aurangabad');


-- ================================================================
-- 9. ROUTE_STOP  (associative entity — Route M:N Stop)
-- ================================================================

-- Route 1: Mumbai to Pune
INSERT INTO Route_Stop (route_id, stop_id, stop_sequence, arrival_time, departure_time) VALUES
(1, 1, 1, '06:00:00', '06:00:00'),
(1, 2, 2, '06:30:00', '06:35:00'),
(1, 3, 3, '07:45:00', '07:50:00'),
(1, 4, 4, '09:00:00', '09:00:00');

-- Route 2: Pune to Nashik
INSERT INTO Route_Stop (route_id, stop_id, stop_sequence, arrival_time, departure_time) VALUES
(2, 4, 1, '10:00:00', '10:00:00'),
(2, 5, 2, '10:20:00', '10:25:00'),
(2, 6, 3, '13:30:00', '13:35:00'),
(2, 7, 4, '14:00:00', '14:00:00');

-- Route 3: Mumbai to Nashik
INSERT INTO Route_Stop (route_id, stop_id, stop_sequence, arrival_time, departure_time) VALUES
(3, 1, 1, '07:00:00', '07:00:00'),
(3, 2, 2, '07:30:00', '07:35:00'),
(3, 7, 3, '11:00:00', '11:00:00');


-- ================================================================
-- 10. TRIPS
-- ================================================================
INSERT INTO Trip (bus_id, route_id, driver_id, departure_datetime, arrival_datetime, seats_available, status) VALUES
(1, 1, 1, '2026-04-15 06:00:00', '2026-04-15 09:00:00', 40, 'scheduled'),
(2, 1, 2, '2026-04-15 14:00:00', '2026-04-15 17:00:00', 50, 'scheduled'),
(3, 2, 3, '2026-04-16 10:00:00', '2026-04-16 14:00:00', 36, 'scheduled'),
(4, 3, 1, '2026-04-17 07:00:00', '2026-04-17 11:00:00', 55, 'scheduled'),
(1, 3, 2, '2026-04-18 21:00:00', '2026-04-19 01:00:00', 40, 'scheduled');


-- ================================================================
-- 11. BOOKINGS
--
--  Two triggers fire automatically on each INSERT:
--    BEFORE INSERT -> stop_validation  (blocks boarding = dropping)
--    AFTER  INSERT -> ticket_trigger   (creates Ticket row with fare)
--
--  booking_time is filled automatically by DEFAULT CURRENT_TIMESTAMP
-- ================================================================

INSERT INTO Booking (user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
VALUES (1, 1, 1, 4, '2026-04-15', 5,  'confirmed');

INSERT INTO Booking (user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
VALUES (2, 1, 2, 4, '2026-04-15', 8,  'confirmed');

INSERT INTO Booking (user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
VALUES (3, 2, 1, 4, '2026-04-15', 3,  'confirmed');

INSERT INTO Booking (user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
VALUES (4, 3, 4, 7, '2026-04-16', 12, 'confirmed');

INSERT INTO Booking (user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
VALUES (5, 4, 1, 7, '2026-04-17', 2,  'confirmed');

INSERT INTO Booking (user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
VALUES (1, 5, 1, 7, '2026-04-18', 10, 'confirmed');

INSERT INTO Booking (user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
VALUES (2, 3, 4, 6, '2026-04-16', 15, 'confirmed');


-- ================================================================
-- 12. PAYMENTS
--     One payment per booking (UNIQUE constraint on booking_id)
--     payment_date is filled by DEFAULT CURRENT_TIMESTAMP
-- ================================================================
INSERT INTO Payment (booking_id, amount, payment_mode) VALUES
(1, 350.00, 'UPI'),
(2, 350.00, 'Card'),
(3, 250.00, 'UPI'),
(4, 450.00, 'Cash'),
(5, 400.00, 'Net Banking'),
(6, 400.00, 'UPI'),
(7, 300.00, 'Card');


-- ================================================================
-- QUICK VERIFY after running this file:
--   SELECT COUNT(*) FROM "User";    -- expect 7
--   SELECT COUNT(*) FROM Booking;   -- expect 7
--   SELECT COUNT(*) FROM Ticket;    -- expect 7 (trigger auto-created)
--   SELECT COUNT(*) FROM Payment;   -- expect 7
-- ================================================================
