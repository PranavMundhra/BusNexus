-- ================================================================
-- BusNexus — Other Features (Fixed)
-- File: sql/other_features.sql
-- Run after: schema.sql, functions.sql, triggers.sql, procedures.sql
--
-- Fixes applied:
--   1. ticket_full_history view — removed stale join on
--      th.booking_id (column no longer exists in ticket_history).
--      booking_id now reached via tickets.booking_id join.
--      Removed th.booking_id from SELECT list.
--   2. Removed CREATE INDEX idx_history_booking ON ticket_history(booking_id)
--      — column does not exist, would ERROR on execution.
--   3. All indexes use IF NOT EXISTS — safe for re-runs.
--   4. trip_with_stops view — status cast to TEXT for safe comparison.
-- ================================================================


-- ================================================================
-- VIEWS
-- ================================================================

-- Drop existing views before recreating (handles column changes)
DROP VIEW IF EXISTS ticket_full_history;
DROP VIEW IF EXISTS booking_summary;
DROP VIEW IF EXISTS trip_with_stops;
DROP VIEW IF EXISTS available_trips;


-- ----------------------------------------------------------------
-- 1. BOOKING_SUMMARY
--    Shows stop names (not IDs) for boarding and dropping.
-- ----------------------------------------------------------------
CREATE VIEW booking_summary AS
SELECT
    b.booking_id,
    u.name                AS passenger_name,
    r.source,
    r.destination,
    bs.stop_name          AS boarding_stop_name,
    ds.stop_name          AS dropping_stop_name,
    b.seat_no,
    b.journey_date,
    b.booking_status,
    b.booking_time,
    t.departure_datetime,
    t.arrival_datetime
FROM bookings b
JOIN users  u  ON b.user_id       = u.user_id
JOIN trips  t  ON b.trip_id       = t.trip_id
JOIN routes r  ON t.route_id      = r.route_id
JOIN stops  bs ON b.boarding_stop = bs.stop_id
JOIN stops  ds ON b.dropping_stop = ds.stop_id;


-- ----------------------------------------------------------------
-- 2. TRIP_WITH_STOPS
--    Full stop list per trip with names and times.
--    Used by UI to populate boarding/dropping dropdowns.
-- ----------------------------------------------------------------
CREATE VIEW trip_with_stops AS
SELECT
    t.trip_id,
    r.source,
    r.destination,
    t.departure_datetime,
    t.arrival_datetime,
    t.seats_available,
    t.status::TEXT        AS status,
    s.stop_id,
    s.stop_name,
    s.location,
    rs.stop_sequence,
    rs.arrival_time,
    rs.departure_time,
    b.bus_type,
    b.capacity,
    b.amenities
FROM trips t
JOIN routes      r  ON t.route_id  = r.route_id
JOIN route_stops rs ON r.route_id  = rs.route_id
JOIN stops       s  ON rs.stop_id  = s.stop_id
JOIN buses       b  ON t.bus_id    = b.bus_id
WHERE t.status = 'scheduled'::trip_status
ORDER BY t.trip_id, rs.stop_sequence;


-- ----------------------------------------------------------------
-- 3. TICKET_FULL_HISTORY
--    Complete temporal audit trail per ticket.
--
--    FIX: th.booking_id removed (column does not exist in schema v5).
--         booking_id now fetched via tickets.booking_id.
--         Join condition simplified to th.ticket_no = tk.ticket_no only.
-- ----------------------------------------------------------------
CREATE VIEW ticket_full_history AS
SELECT
    th.history_id,
    th.ticket_no,
    tk.booking_id,            -- reached via tickets, not ticket_history
    u.name                AS passenger_name,
    r.source,
    r.destination,
    t.departure_datetime,
    tk.fare,
    tk.issued_at          AS ticket_issued_at,
    th.status             AS event_status,
    th.changed_at         AS event_time,
    th.remarks
FROM ticket_history th
JOIN tickets  tk ON th.ticket_no  = tk.ticket_no    -- FIX: single-column join
JOIN bookings b  ON tk.booking_id = b.booking_id
JOIN users    u  ON b.user_id     = u.user_id
JOIN trips    t  ON b.trip_id     = t.trip_id
JOIN routes   r  ON t.route_id    = r.route_id
ORDER BY th.changed_at DESC;


-- ----------------------------------------------------------------
-- 4. AVAILABLE_TRIPS
--    Only future scheduled trips — date filter at DB level.
--    Exposes boolean JSONB amenity flags for UI filtering.
-- ----------------------------------------------------------------
CREATE VIEW available_trips AS
SELECT
    t.trip_id,
    r.route_id,
    r.source,
    r.destination,
    r.distance,
    r.base_fare,
    t.departure_datetime,
    t.arrival_datetime,
    t.seats_available,
    b.bus_type,
    b.capacity,
    b.amenities,
    (b.amenities->>'wifi')::boolean     AS has_wifi,
    (b.amenities->>'ac')::boolean       AS has_ac,
    (b.amenities->>'charging')::boolean AS has_charging,
    (b.amenities->>'blanket')::boolean  AS has_blanket
FROM trips t
JOIN routes r ON t.route_id = r.route_id
JOIN buses  b ON t.bus_id   = b.bus_id
WHERE t.status = 'scheduled'::trip_status
  AND DATE(t.departure_datetime) >= CURRENT_DATE
ORDER BY t.departure_datetime;


-- ================================================================
-- INDEXES  (IF NOT EXISTS — safe for re-runs)
-- ================================================================

-- users
CREATE INDEX IF NOT EXISTS idx_users_email        ON users(email);

-- accounts
CREATE INDEX IF NOT EXISTS idx_accounts_email     ON accounts(email);

-- bookings
CREATE INDEX IF NOT EXISTS idx_bookings_user      ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_trip      ON bookings(trip_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status    ON bookings(booking_status);

-- trips
CREATE INDEX IF NOT EXISTS idx_trips_datetime     ON trips(departure_datetime);
CREATE INDEX IF NOT EXISTS idx_trips_route        ON trips(route_id);
CREATE INDEX IF NOT EXISTS idx_trips_bus          ON trips(bus_id);

-- routes
CREATE INDEX IF NOT EXISTS idx_routes_source      ON routes(source);
CREATE INDEX IF NOT EXISTS idx_routes_dest        ON routes(destination);

-- route_stops
CREATE INDEX IF NOT EXISTS idx_route_stops_route  ON route_stops(route_id);

-- payments
CREATE INDEX IF NOT EXISTS idx_payments_booking   ON payments(booking_id);

-- ticket_history (ticket_no only — booking_id column does not exist)
CREATE INDEX IF NOT EXISTS idx_history_ticket     ON ticket_history(ticket_no);

-- JSONB GIN index
CREATE INDEX IF NOT EXISTS idx_buses_amenities    ON buses USING GIN (amenities);


-- ================================================================
-- CURSORS
-- ================================================================

-- ----------------------------------------------------------------
-- Cursor 1: Trip availability report
-- ----------------------------------------------------------------
DO $$
DECLARE
    trip_cursor CURSOR FOR
        SELECT
            t.trip_id,
            r.source,
            r.destination,
            t.departure_datetime,
            t.seats_available
        FROM trips t
        JOIN routes r ON t.route_id = r.route_id
        WHERE t.status = 'scheduled'::trip_status
          AND DATE(t.departure_datetime) >= CURRENT_DATE
        ORDER BY t.departure_datetime;

    rec RECORD;
BEGIN
    OPEN trip_cursor;
    LOOP
        FETCH trip_cursor INTO rec;
        EXIT WHEN NOT FOUND;
        RAISE NOTICE 'Trip %: % → % | Departs: % | Seats left: %',
            rec.trip_id,
            rec.source,
            rec.destination,
            rec.departure_datetime,
            rec.seats_available;
    END LOOP;
    CLOSE trip_cursor;
END;
$$;


-- ----------------------------------------------------------------
-- Cursor 2: Passenger booking history
-- ----------------------------------------------------------------
DO $$
DECLARE
    booking_cursor CURSOR FOR
        SELECT
            u.name,
            b.booking_id,
            r.source,
            r.destination,
            b.journey_date,
            b.booking_status
        FROM bookings b
        JOIN users  u ON b.user_id  = u.user_id
        JOIN trips  t ON b.trip_id  = t.trip_id
        JOIN routes r ON t.route_id = r.route_id
        ORDER BY u.name, b.journey_date;

    rec RECORD;
BEGIN
    OPEN booking_cursor;
    LOOP
        FETCH booking_cursor INTO rec;
        EXIT WHEN NOT FOUND;
        RAISE NOTICE 'Passenger: % | Booking %: % → % on % [%]',
            rec.name,
            rec.booking_id,
            rec.source,
            rec.destination,
            rec.journey_date,
            rec.booking_status;
    END LOOP;
    CLOSE booking_cursor;
END;
$$;