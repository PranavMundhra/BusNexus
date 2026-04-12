-- =========================
-- 4. TRIGGERS
-- =========================

-- Validate Stops
CREATE OR REPLACE FUNCTION validate_stops()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.boarding_stop = NEW.dropping_stop THEN
        RAISE EXCEPTION 'Boarding and dropping stops cannot be same';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER stop_validation
BEFORE INSERT ON Booking
FOR EACH ROW
EXECUTE FUNCTION validate_stops();

-- Generate Ticket
CREATE OR REPLACE FUNCTION generate_ticket()
RETURNS TRIGGER AS $$
DECLARE r_id INT;
DECLARE fare_amt NUMERIC;
BEGIN
    SELECT route_id INTO r_id
    FROM Trip
    WHERE trip_id = NEW.trip_id;

    fare_amt := calculate_fare(r_id, 'AC');

    INSERT INTO Ticket(booking_id, fare, duration)
    VALUES (
        NEW.booking_id,
        fare_amt,
        (SELECT arrival_datetime - departure_datetime FROM Trip WHERE trip_id = NEW.trip_id)
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ticket_trigger
AFTER INSERT ON Booking
FOR EACH ROW
EXECUTE FUNCTION generate_ticket();

-- Auto Update Trip Status
CREATE OR REPLACE FUNCTION update_trip_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.departure_datetime < CURRENT_TIMESTAMP THEN
        NEW.status := 'completed';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trip_status_trigger
BEFORE UPDATE ON Trip
FOR EACH ROW
EXECUTE FUNCTION update_trip_status();