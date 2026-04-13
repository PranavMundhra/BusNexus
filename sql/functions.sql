-- ================================================================
-- BusNexus — Functions (Fixed)
-- File: sql/functions.sql
-- Run after: schema.sql
--
-- Fixes applied:
--   1. get_stops_for_trip — removed dead IF NOT FOUND block after
--      RETURN QUERY (NOT FOUND does not work after RETURN QUERY
--      in PostgreSQL — it only works after SELECT INTO).
--      Replaced with explicit count check.
--   2. get_seat_map — ENUM cast for booking_status comparison
--      made explicit ('cancelled'::booking_status_enum).
--   3. All functions retain exception handling.
-- ================================================================


-- ================================================================
-- 1. CALCULATE_FARE
--    Returns fare for a route + seat type surcharge.
--    Used by generate_ticket_on_confirmation trigger.
-- ================================================================
CREATE OR REPLACE FUNCTION calculate_fare(r_id INT, seat_type TEXT)
RETURNS NUMERIC AS $$
DECLARE
    base NUMERIC;
BEGIN
    SELECT base_fare INTO base
    FROM routes
    WHERE route_id = r_id;

    IF base IS NULL THEN
        RAISE EXCEPTION 'Route % not found', r_id;
    END IF;

    RETURN CASE seat_type
        WHEN 'AC'      THEN base + 100
        WHEN 'Sleeper' THEN base + 200
        ELSE                base
    END;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'calculate_fare error: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;


-- ================================================================
-- 2. GET_AVAILABLE_SEATS
--    Returns seats_available for a trip.
-- ================================================================
CREATE OR REPLACE FUNCTION get_available_seats(t_id INT)
RETURNS INT AS $$
DECLARE
    seats INT;
BEGIN
    SELECT seats_available INTO seats
    FROM trips
    WHERE trip_id = t_id;

    IF seats IS NULL THEN
        RAISE EXCEPTION 'Trip % not found', t_id;
    END IF;

    RETURN seats;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'get_available_seats error: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;


-- ================================================================
-- 3. PASSENGER_BOOKING_COUNT
--    Returns total booking count for a user.
-- ================================================================
CREATE OR REPLACE FUNCTION passenger_booking_count(u_id INT)
RETURNS INT AS $$
DECLARE
    cnt INT;
BEGIN
    SELECT COUNT(*) INTO cnt
    FROM bookings
    WHERE user_id = u_id;

    RETURN COALESCE(cnt, 0);

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'passenger_booking_count error: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;


-- ================================================================
-- 4. GET_SEAT_MAP
--    Returns one row per seat (1 to bus capacity) with status
--    'available' or 'booked'. Cancelled bookings free the seat.
--
--    UI renders this as a seat grid:
--      SELECT * FROM get_seat_map(trip_id);
-- ================================================================
CREATE OR REPLACE FUNCTION get_seat_map(t_id INT)
RETURNS TABLE (seat_no INT, status TEXT) AS $$
DECLARE
    total_capacity INT;
BEGIN
    SELECT b.capacity INTO total_capacity
    FROM trips t
    JOIN buses b ON t.bus_id = b.bus_id
    WHERE t.trip_id = t_id;

    IF total_capacity IS NULL THEN
        RAISE EXCEPTION 'Trip % not found', t_id;
    END IF;

    RETURN QUERY
    SELECT
        gs.seat_no,
        CASE
            WHEN bk.seat_no IS NOT NULL THEN 'booked'::TEXT
            ELSE 'available'::TEXT
        END AS status
    FROM generate_series(1, total_capacity) AS gs(seat_no)
    LEFT JOIN bookings bk
        ON  bk.seat_no        = gs.seat_no
        AND bk.trip_id        = t_id
        AND bk.booking_status != 'cancelled'::booking_status_enum
    ORDER BY gs.seat_no;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'get_seat_map error: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;


-- ================================================================
-- 5. GET_STOPS_FOR_TRIP
--    Returns ordered named stops for a trip's route.
--    UI uses this to populate boarding/dropping dropdowns.
--
--    FIX: removed IF NOT FOUND after RETURN QUERY (does not work
--         in PostgreSQL — NOT FOUND is only set by SELECT INTO).
--         Replaced with explicit row count check.
--
--    UI usage:
--      SELECT * FROM get_stops_for_trip(trip_id);
-- ================================================================
CREATE OR REPLACE FUNCTION get_stops_for_trip(t_id INT)
RETURNS TABLE (
    stop_id       INT,
    stop_name     TEXT,
    location      TEXT,
    stop_sequence INT
) AS $$
DECLARE
    stop_count INT;
BEGIN
    -- Explicit check: does this trip exist and have stops?
    SELECT COUNT(*) INTO stop_count
    FROM trips t
    JOIN route_stops rs ON t.route_id = rs.route_id
    WHERE t.trip_id = t_id;

    IF stop_count = 0 THEN
        RAISE EXCEPTION 'No stops found for trip %', t_id;
    END IF;

    RETURN QUERY
    SELECT
        s.stop_id,
        s.stop_name,
        s.location,
        rs.stop_sequence
    FROM trips t
    JOIN route_stops rs ON t.route_id = rs.route_id
    JOIN stops s        ON rs.stop_id = s.stop_id
    WHERE t.trip_id = t_id
    ORDER BY rs.stop_sequence;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'get_stops_for_trip error: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;