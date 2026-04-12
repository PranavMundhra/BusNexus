-- =========================
-- 2. FUNCTIONS
-- =========================

-- Fare Calculation
CREATE OR REPLACE FUNCTION calculate_fare(r_id INT, seat_type TEXT)
RETURNS NUMERIC AS $$
DECLARE base NUMERIC;
BEGIN
    SELECT base_fare INTO base FROM Route WHERE route_id = r_id;

    IF seat_type = 'AC' THEN
        RETURN base + 100;
    ELSIF seat_type = 'Sleeper' THEN
        RETURN base + 200;
    ELSE
        RETURN base;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Available Seats
CREATE OR REPLACE FUNCTION get_available_seats(t_id INT)
RETURNS INT AS $$
DECLARE seats INT;
BEGIN
    SELECT seats_available INTO seats FROM Trip WHERE trip_id = t_id;
    RETURN seats;
END;
$$ LANGUAGE plpgsql;

-- Booking Count
CREATE OR REPLACE FUNCTION passenger_booking_count(u_id INT)
RETURNS INT AS $$
DECLARE cnt INT;
BEGIN
    SELECT COUNT(*) INTO cnt FROM Booking WHERE user_id = u_id;
    RETURN cnt;
END;
$$ LANGUAGE plpgsql;