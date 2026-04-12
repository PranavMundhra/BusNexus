-- =========================
-- 3. PROCEDURES
-- =========================

-- Create Booking (with locking)
CREATE OR REPLACE PROCEDURE create_booking(
    u_id INT,
    t_id INT,
    board INT,
    drop_stop INT,
    seat INT
)
LANGUAGE plpgsql
AS $$
DECLARE seats INT;
BEGIN
    -- Lock row (Concurrency Control)
    SELECT seats_available INTO seats
    FROM Trip
    WHERE trip_id = t_id
    FOR UPDATE;

    IF seats > 0 THEN
        INSERT INTO Booking(user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
        VALUES (u_id, t_id, board, drop_stop, CURRENT_DATE, seat, 'confirmed');

        UPDATE Trip
        SET seats_available = seats_available - 1
        WHERE trip_id = t_id;
    ELSE
        INSERT INTO Booking(user_id, trip_id, boarding_stop, dropping_stop, journey_date, seat_no, booking_status)
        VALUES (u_id, t_id, board, drop_stop, CURRENT_DATE, seat, 'waitlisted');
    END IF;
END;
$$;

-- Cancel Booking
CREATE OR REPLACE PROCEDURE cancel_booking(b_id INT)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE Booking
    SET booking_status = 'cancelled'
    WHERE booking_id = b_id;

    UPDATE Trip
    SET seats_available = seats_available + 1
    WHERE trip_id = (
        SELECT trip_id FROM Booking WHERE booking_id = b_id
    );
END;
$$;