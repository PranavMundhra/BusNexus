-- ================================================================
-- BusNexus — Procedures (Fixed)
-- File: sql/procedures.sql
-- Run after: schema.sql, functions.sql, triggers.sql
--
-- Fixes applied:
--   1. create_booking — REMOVED manual seats_available decrement.
--      trigger trg_update_seats_booking handles it.
--      Both doing it caused double decrement (seats went down by 2).
--   2. create_booking — added p_journey_date parameter so UI can
--      book for any future date, not just CURRENT_DATE always.
--   3. cancel_booking — prev_status declared as booking_status_enum
--      (matches column type) instead of TEXT.
--   4. Both procedures retain full exception handling.
-- ================================================================


-- ================================================================
-- 1. CREATE_BOOKING
--
--    Steps:
--      a) Verify user exists and is a passenger
--      b) Verify trip exists and is scheduled
--      c) Explicit seat double-booking check (belt over UNIQUE)
--      d) Row-level lock FOR UPDATE (concurrency control)
--      e) seats > 0 → 'confirmed', else → 'waitlisted'
--
--    NOTE: DO NOT decrement seats here.
--    trg_update_seats_booking fires AFTER INSERT and handles it.
--    Doing it here AND in the trigger causes double decrement.
--
--    Triggers that auto-fire after INSERT on bookings:
--      trg_validate_journey_date  → blocks past dates
--      trg_validate_stop_sequence → blocks wrong stop order
--      trg_update_seats_booking   → decrements seats_available
--      trg_generate_ticket_insert → creates ticket if confirmed
--      trg_ticket_issued          → logs 'issued' to ticket_history
-- ================================================================
CREATE OR REPLACE PROCEDURE create_booking(
    u_id          INT,
    t_id          INT,
    board         INT,
    drop_stop     INT,
    seat          INT,
    p_journey_date DATE DEFAULT CURRENT_DATE
)
LANGUAGE plpgsql
AS $$
DECLARE
    seats       INT;
    u_role      user_role;
    t_status    trip_status;
BEGIN
    -- Step a: Verify user exists and is a passenger
    SELECT role INTO u_role
    FROM users
    WHERE user_id = u_id;

    IF u_role IS NULL THEN
        RAISE EXCEPTION 'User % does not exist', u_id;
    END IF;

    IF u_role != 'passenger'::user_role THEN
        RAISE EXCEPTION
            'Only passengers can make bookings. User % has role: %',
            u_id, u_role;
    END IF;

    -- Step b: Verify trip exists and is scheduled
    SELECT status INTO t_status
    FROM trips
    WHERE trip_id = t_id;

    IF t_status IS NULL THEN
        RAISE EXCEPTION 'Trip % does not exist', t_id;
    END IF;

    IF t_status != 'scheduled'::trip_status THEN
        RAISE EXCEPTION
            'Trip % is not available for booking (status: %)', t_id, t_status;
    END IF;

    -- Step c: Explicit seat check (safety net on top of UNIQUE constraint)
    IF EXISTS (
        SELECT 1 FROM bookings
        WHERE trip_id        = t_id
          AND seat_no        = seat
          AND booking_status != 'cancelled'::booking_status_enum
    ) THEN
        RAISE EXCEPTION 'Seat % on trip % is already booked', seat, t_id;
    END IF;

    -- Step d: Row-level lock (concurrency control)
    SELECT seats_available INTO seats
    FROM trips
    WHERE trip_id = t_id
    FOR UPDATE;

    -- Step e: Insert booking — trigger handles seat decrement
    IF seats > 0 THEN
        INSERT INTO bookings (
            user_id, trip_id, boarding_stop, dropping_stop,
            journey_date, seat_no, booking_status
        )
        VALUES (
            u_id, t_id, board, drop_stop,
            p_journey_date, seat, 'confirmed'::booking_status_enum
        );
    ELSE
        -- Waitlisted — no ticket generated (trigger guards on status)
        INSERT INTO bookings (
            user_id, trip_id, boarding_stop, dropping_stop,
            journey_date, seat_no, booking_status
        )
        VALUES (
            u_id, t_id, board, drop_stop,
            p_journey_date, seat, 'waitlisted'::booking_status_enum
        );
    END IF;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'create_booking failed: %', SQLERRM;
END;
$$;


-- ================================================================
-- 2. CANCEL_BOOKING
--
--    Steps:
--      a) Verify booking exists and belongs to requesting user
--      b) Guard against double cancellation
--      c) Update status → 'cancelled'
--         (trg_update_seats_cancel restores seat automatically)
--         (trg_booking_status_change logs to ticket_history)
--
--    NOTE: DO NOT restore seats here.
--    trg_update_seats_cancel fires AFTER UPDATE and handles it.
-- ================================================================
CREATE OR REPLACE PROCEDURE cancel_booking(b_id INT, u_id INT)
LANGUAGE plpgsql
AS $$
DECLARE
    prev_status  booking_status_enum;   -- FIX: correct ENUM type
    owner_id     INT;
    t_id         INT;
BEGIN
    -- Step a: Verify booking exists and belongs to this user
    SELECT user_id, booking_status, trip_id
    INTO owner_id, prev_status, t_id
    FROM bookings
    WHERE booking_id = b_id;

    IF owner_id IS NULL THEN
        RAISE EXCEPTION 'Booking % does not exist', b_id;
    END IF;

    IF owner_id != u_id THEN
        RAISE EXCEPTION
            'Booking % does not belong to user %', b_id, u_id;
    END IF;

    -- Step b: Guard against double cancellation
    IF prev_status = 'cancelled'::booking_status_enum THEN
        RAISE EXCEPTION 'Booking % is already cancelled', b_id;
    END IF;

    -- Step c: Update status
    -- Triggers fire automatically:
    --   trg_update_seats_cancel   → restores seat if was confirmed
    --   trg_booking_status_change → logs 'cancelled' to ticket_history
    UPDATE bookings
    SET booking_status = 'cancelled'::booking_status_enum
    WHERE booking_id = b_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'cancel_booking failed: %', SQLERRM;
END;
$$;