-- =========================
-- 5. VIEW
-- =========================

CREATE VIEW booking_summary AS
SELECT b.booking_id, u.name, r.source, r.destination, b.seat_no, b.booking_status
FROM Booking b
JOIN "User" u ON b.user_id = u.user_id
JOIN Trip t ON b.trip_id = t.trip_id
JOIN Route r ON t.route_id = r.route_id;

-- =========================
-- 6. INDEX
-- =========================

CREATE INDEX idx_booking_user ON Booking(user_id);
CREATE INDEX idx_booking_trip ON Booking(trip_id);

-- =========================
-- 7. SAMPLE TRANSACTION
-- =========================

-- BEGIN;
-- CALL create_booking(1, 1, 1, 2, 5);
-- COMMIT;