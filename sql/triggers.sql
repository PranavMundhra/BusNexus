-- ================================================================
-- BusNexus — Triggers (Fixed)
-- File: sql/triggers.sql
-- Run after: schema.sql, functions.sql
--
-- Fixes applied:
--   1. generate_ticket_on_confirmation now fires on BOTH INSERT
--      and UPDATE — INSERT handles direct 'confirmed' bookings,
--      UPDATE handles waitlisted → confirmed promotions.
--   2. log_booking_status_change now guards on status actually
--      changing (OLD.booking_status != NEW.booking_status) to
--      prevent spurious 'modified' entries on unrelated updates.
--   3. update_seats_on_booking REMOVED the post-decrement check
--      (race condition) — the schema CHECK (seats_available >= 0)
--      and the procedure's pre-check are sufficient guards.
--   4. ENUM casts made consistent throughout ('confirmed'::booking_status_enum).
-- ================================================================


-- ================================================================
-- 1. VALIDATE JOURNEY DATE
--    BEFORE INSERT on bookings
--    Blocks past-date bookings at DB level regardless of UI input.
-- ================================================================
CREATE OR REPLACE FUNCTION validate_journey_date()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.journey_date < CURRENT_DATE THEN
        RAISE EXCEPTION
            'Journey date cannot be in the past. Requested: %, Today: %',
            NEW.journey_date, CURRENT_DATE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_journey_date
BEFORE INSERT ON bookings
FOR EACH ROW
EXECUTE FUNCTION validate_journey_date();


-- ================================================================
-- 2. AUTO TICKET GENERATION
--    Fires on AFTER INSERT (direct confirmed booking) AND
--    AFTER UPDATE (waitlisted → confirmed promotion).
--
--    FIX: was AFTER UPDATE only — missed direct confirmed INSERTs.
--    FIX: fare now computed via calculate_fare() instead of 0.
-- ================================================================
CREATE OR REPLACE FUNCTION generate_ticket_on_confirmation()
RETURNS TRIGGER AS $$
DECLARE
    r_id     INT;
    fare_amt NUMERIC;
BEGIN
    -- On INSERT: only act if status is confirmed
    -- On UPDATE: only act when transitioning INTO confirmed
    IF (TG_OP = 'INSERT' AND NEW.booking_status = 'confirmed'::booking_status_enum)
    OR (TG_OP = 'UPDATE'
        AND NEW.booking_status = 'confirmed'::booking_status_enum
        AND OLD.booking_status IS DISTINCT FROM 'confirmed'::booking_status_enum)
    THEN
        -- Guard: don't create duplicate ticket if one already exists
        IF EXISTS (SELECT 1 FROM tickets WHERE booking_id = NEW.booking_id) THEN
            RETURN NEW;
        END IF;

        -- Compute fare via function
        SELECT route_id INTO r_id
        FROM trips
        WHERE trip_id = NEW.trip_id;

        fare_amt := calculate_fare(r_id, 'AC');

        INSERT INTO tickets (booking_id, fare, duration, issued_at)
        VALUES (
            NEW.booking_id,
            fare_amt,
            (SELECT arrival_datetime - departure_datetime
             FROM trips WHERE trip_id = NEW.trip_id),
            CURRENT_TIMESTAMP
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Fires on both INSERT and UPDATE
CREATE TRIGGER trg_generate_ticket_insert
AFTER INSERT ON bookings
FOR EACH ROW
EXECUTE FUNCTION generate_ticket_on_confirmation();

CREATE TRIGGER trg_generate_ticket_update
AFTER UPDATE ON bookings
FOR EACH ROW
EXECUTE FUNCTION generate_ticket_on_confirmation();


-- ================================================================
-- 3. LOG TICKET ISSUED
--    AFTER INSERT on tickets
--    Auto-logs 'issued' event into ticket_history.
-- ================================================================
CREATE OR REPLACE FUNCTION log_ticket_issued()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO ticket_history (ticket_no, status, remarks, changed_at)
    VALUES (
        NEW.ticket_no,
        'issued',
        'Ticket auto-generated after booking confirmation',
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ticket_issued
AFTER INSERT ON tickets
FOR EACH ROW
EXECUTE FUNCTION log_ticket_issued();


-- ================================================================
-- 4. LOG BOOKING STATUS CHANGE
--    AFTER UPDATE on bookings
--    Logs 'cancelled' or 'modified' into ticket_history.
--
--    FIX: added guard so trigger only acts when booking_status
--         actually changes — prevents spurious logs on other
--         column updates (seat_no, journey_date, etc.).
-- ================================================================
CREATE OR REPLACE FUNCTION log_booking_status_change()
RETURNS TRIGGER AS $$
DECLARE
    t_no INT;
BEGIN
    -- Only act if booking_status actually changed
    IF OLD.booking_status = NEW.booking_status THEN
        RETURN NEW;
    END IF;

    -- Find ticket for this booking
    SELECT ticket_no INTO t_no
    FROM tickets
    WHERE booking_id = NEW.booking_id;

    -- No ticket = waitlisted booking, nothing to log
    IF t_no IS NULL THEN
        RETURN NEW;
    END IF;

    INSERT INTO ticket_history (ticket_no, status, remarks, changed_at)
    VALUES (
        t_no,
        CASE
            WHEN NEW.booking_status = 'cancelled'::booking_status_enum THEN 'cancelled'
            ELSE 'modified'
        END,
        'Booking status changed from ' || OLD.booking_status::TEXT
            || ' to ' || NEW.booking_status::TEXT,
        CURRENT_TIMESTAMP
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_booking_status_change
AFTER UPDATE ON bookings
FOR EACH ROW
EXECUTE FUNCTION log_booking_status_change();


-- ================================================================
-- 5. UPDATE SEATS ON BOOKING INSERT
--    AFTER INSERT on bookings
--    Decrements seats_available for confirmed bookings.
--
--    FIX: removed post-decrement negative check (race condition).
--    The schema CHECK (seats_available >= 0) and the procedure's
--    pre-check together are the correct guards.
--    The trigger handles cases where bookings are inserted
--    directly (bypassing the procedure).
-- ================================================================
CREATE OR REPLACE FUNCTION update_seats_on_booking()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.booking_status = 'confirmed'::booking_status_enum THEN
        UPDATE trips
        SET seats_available = seats_available - 1
        WHERE trip_id = NEW.trip_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_seats_booking
AFTER INSERT ON bookings
FOR EACH ROW
EXECUTE FUNCTION update_seats_on_booking();


-- ================================================================
-- 6. UPDATE SEATS ON CANCELLATION
--    AFTER UPDATE on bookings
--    Restores seats_available when a confirmed booking is cancelled.
-- ================================================================
CREATE OR REPLACE FUNCTION update_seats_on_cancel()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.booking_status = 'confirmed'::booking_status_enum
       AND NEW.booking_status = 'cancelled'::booking_status_enum THEN

        UPDATE trips
        SET seats_available = seats_available + 1
        WHERE trip_id = NEW.trip_id;

    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_seats_cancel
AFTER UPDATE ON bookings
FOR EACH ROW
EXECUTE FUNCTION update_seats_on_cancel();


-- ================================================================
-- 7. VALIDATE BOARDING vs DROPPING STOP ORDER
--    BEFORE INSERT on bookings
--    Ensures boarding stop comes before dropping stop in
--    the route sequence — prevents logically invalid bookings.
-- ================================================================
CREATE OR REPLACE FUNCTION validate_stop_sequence()
RETURNS TRIGGER AS $$
DECLARE
    board_seq INT;
    drop_seq  INT;
BEGIN
    SELECT rs.stop_sequence INTO board_seq
    FROM route_stops rs
    JOIN trips t ON t.route_id = rs.route_id
    WHERE rs.stop_id = NEW.boarding_stop
      AND t.trip_id  = NEW.trip_id;

    SELECT rs.stop_sequence INTO drop_seq
    FROM route_stops rs
    JOIN trips t ON t.route_id = rs.route_id
    WHERE rs.stop_id = NEW.dropping_stop
      AND t.trip_id  = NEW.trip_id;

    IF board_seq IS NULL OR drop_seq IS NULL THEN
        RAISE EXCEPTION
            'Boarding or dropping stop does not belong to this trip''s route';
    END IF;

    IF board_seq >= drop_seq THEN
        RAISE EXCEPTION
            'Invalid stop order: boarding stop (sequence %) must come before dropping stop (sequence %)',
            board_seq, drop_seq;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_stop_sequence
BEFORE INSERT ON bookings
FOR EACH ROW
EXECUTE FUNCTION validate_stop_sequence();