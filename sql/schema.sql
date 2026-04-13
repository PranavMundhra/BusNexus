-- ================================================================
-- BusNexus ADBMS — Schema (v5 Fixed)
-- ================================================================


-- ================================================================
-- 0. ENUM TYPES
-- ================================================================
CREATE TYPE user_role           AS ENUM ('passenger', 'coordinator');
CREATE TYPE trip_status         AS ENUM ('scheduled', 'completed', 'cancelled');
CREATE TYPE booking_status_enum AS ENUM ('confirmed', 'cancelled', 'waitlisted');
CREATE TYPE payment_mode_enum   AS ENUM ('card', 'upi', 'cash');
CREATE TYPE payment_status_enum AS ENUM ('success', 'failed', 'pending');


-- ================================================================
-- 1. USERS
-- ================================================================
CREATE TABLE users (
    user_id    SERIAL       PRIMARY KEY,
    name       TEXT         NOT NULL,
    email      TEXT         NOT NULL UNIQUE,
    contact_no TEXT,
    role       user_role    NOT NULL
);


-- ================================================================
-- 2. ACCOUNTS (AUTHENTICATION)
--    Separates login credentials from user profile.
--    email is NOT NULL so chk_username_or_email is always satisfied
--    by email alone — username remains optional for flexibility.
-- ================================================================
CREATE TABLE accounts (
    account_id    SERIAL    PRIMARY KEY,
    user_id       INT       NOT NULL UNIQUE
                            REFERENCES users(user_id) ON DELETE CASCADE,
    username      TEXT      UNIQUE,
    email         TEXT      NOT NULL UNIQUE,
    password_hash TEXT      NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_username_or_email
        CHECK (username IS NOT NULL OR email IS NOT NULL)
);


-- ================================================================
-- 3. PASSENGERS  (subtype of users)
-- ================================================================
CREATE TABLE passengers (
    user_id INT PRIMARY KEY
        REFERENCES users(user_id) ON DELETE CASCADE
);


-- ================================================================
-- 4. COORDINATORS  (subtype of users)
-- ================================================================
CREATE TABLE coordinators (
    user_id INT PRIMARY KEY
        REFERENCES users(user_id) ON DELETE CASCADE
);


-- ================================================================
-- 5. EMPLOYEES  (superclass)
-- ================================================================
CREATE TABLE employees (
    emp_id     SERIAL PRIMARY KEY,
    name       TEXT   NOT NULL,
    contact_no TEXT
);


-- ================================================================
-- 6. DRIVERS  (subtype of employees)
-- ================================================================
CREATE TABLE drivers (
    emp_id       INT          PRIMARY KEY
                              REFERENCES employees(emp_id) ON DELETE CASCADE,
    phone_number VARCHAR(15)
);

-- ================================================================
-- 7. MAINTENANCE_STAFF  (subtype of employees)
-- ================================================================
CREATE TABLE maintenance_staff (
    emp_id         INT         PRIMARY KEY
                               REFERENCES employees(emp_id) ON DELETE CASCADE,
    specialization VARCHAR(50),
    shift          VARCHAR(20)
);


-- ================================================================
-- 8. BUSES
--    coordinator_id → FK to coordinators ensures only a coordinator
--    can own a bus (subtype constraint enforced at DB level).
-- ================================================================
CREATE TABLE buses (
    bus_id         SERIAL  PRIMARY KEY,
    bus_type       TEXT    NOT NULL,
    capacity       INT     NOT NULL CHECK (capacity > 0),
    amenities      JSONB,
    coordinator_id INT     NOT NULL
                           REFERENCES coordinators(user_id) ON DELETE RESTRICT
);


-- ================================================================
-- 9. ROUTES
-- ================================================================
CREATE TABLE routes (
    route_id    SERIAL  PRIMARY KEY,
    source      TEXT    NOT NULL,
    destination TEXT    NOT NULL,
    distance    INT     CHECK (distance > 0),
    base_fare   NUMERIC NOT NULL CHECK (base_fare >= 0)
);


-- ================================================================
-- 10. STOPS
-- ================================================================
CREATE TABLE stops (
    stop_id   SERIAL  PRIMARY KEY,
    stop_name TEXT    NOT NULL,
    location  TEXT    NOT NULL,
    latitude  NUMERIC,
    longitude NUMERIC
);


-- ================================================================
-- 11. ROUTE_STOPS  (associative entity — routes M:N stops)
--    PK is (route_id, stop_sequence) — allows same stop on
--    different sequences (loop routes), but each position is unique.
-- ================================================================
CREATE TABLE route_stops (
    route_id       INT  NOT NULL REFERENCES routes(route_id) ON DELETE CASCADE,
    stop_id        INT  NOT NULL REFERENCES stops(stop_id)   ON DELETE CASCADE,
    stop_sequence  INT  NOT NULL,
    arrival_time   TIME,
    departure_time TIME,

    PRIMARY KEY (route_id, stop_sequence),
    UNIQUE (route_id, stop_id, stop_sequence)
);


-- ================================================================
-- 12. TRIPS
--    FIX: added missing comma between seats_available and
--         the table-level CHECK constraint.
-- ================================================================
CREATE TABLE trips (
    trip_id            SERIAL       PRIMARY KEY,
    bus_id             INT          NOT NULL REFERENCES buses(bus_id)    ON DELETE RESTRICT,
    route_id           INT          NOT NULL REFERENCES routes(route_id) ON DELETE RESTRICT,
    driver_id          INT          NOT NULL REFERENCES drivers(emp_id)  ON DELETE RESTRICT,
    departure_datetime TIMESTAMP    NOT NULL,
    arrival_datetime   TIMESTAMP    NOT NULL,
    status             trip_status  NOT NULL,
    seats_available    INT          NOT NULL CHECK (seats_available >= 0),

    CHECK (arrival_datetime > departure_datetime)   -- ← comma was missing before this line
);


-- ================================================================
-- 13. BOOKINGS
-- ================================================================
CREATE TABLE bookings (
    booking_id     SERIAL               PRIMARY KEY,
    user_id        INT                  NOT NULL REFERENCES users(user_id)  ON DELETE RESTRICT,
    trip_id        INT                  NOT NULL REFERENCES trips(trip_id)  ON DELETE RESTRICT,
    boarding_stop  INT                  NOT NULL REFERENCES stops(stop_id)  ON DELETE RESTRICT,
    dropping_stop  INT                  NOT NULL REFERENCES stops(stop_id)  ON DELETE RESTRICT,
    journey_date   DATE                 NOT NULL,
    seat_no        INT                  NOT NULL CHECK (seat_no > 0),
    booking_status booking_status_enum  NOT NULL,
    booking_time   TIMESTAMP            DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (trip_id, seat_no)
);


-- ================================================================
-- 14. TICKETS  (weak entity — existence depends on bookings)
--    ticket_no is sole PK (not composite).
--    booking_id UNIQUE enforces strict 1:1 booking → ticket.
-- ================================================================
CREATE TABLE tickets (
    ticket_no  SERIAL  PRIMARY KEY,
    booking_id INT     NOT NULL UNIQUE
                       REFERENCES bookings(booking_id) ON DELETE CASCADE,
    fare       NUMERIC NOT NULL CHECK (fare >= 0),
    duration   INTERVAL,
    issued_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ================================================================
-- 15. TICKET_HISTORY  (temporal audit trail)
--    References tickets(ticket_no) only — booking_id removed
--    (reach booking via tickets.booking_id join).
-- ================================================================
CREATE TABLE ticket_history (
    history_id SERIAL PRIMARY KEY,
    ticket_no  INT    NOT NULL
                      REFERENCES tickets(ticket_no) ON DELETE CASCADE,
    status     TEXT   NOT NULL CHECK (status IN ('issued', 'cancelled', 'modified')),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by INT    REFERENCES users(user_id) ON DELETE SET NULL,
    remarks    TEXT
);


-- ================================================================
-- 16. PAYMENTS
-- ================================================================
CREATE TABLE payments (
    payment_id     SERIAL              PRIMARY KEY,
    booking_id     INT                 NOT NULL REFERENCES bookings(booking_id) ON DELETE RESTRICT,
    amount         NUMERIC             NOT NULL CHECK (amount > 0),
    payment_mode   payment_mode_enum   NOT NULL,
    payment_status payment_status_enum NOT NULL,
    payment_date   TIMESTAMP           DEFAULT CURRENT_TIMESTAMP
);


-- ================================================================
-- 17. INDEXES
-- ================================================================

-- users
CREATE INDEX idx_users_email          ON users(email);

-- accounts
CREATE INDEX idx_accounts_email       ON accounts(email);

-- bookings
CREATE INDEX idx_bookings_user        ON bookings(user_id);
CREATE INDEX idx_bookings_trip        ON bookings(trip_id);
CREATE INDEX idx_bookings_status      ON bookings(booking_status);

-- trips
CREATE INDEX idx_trips_route          ON trips(route_id);
CREATE INDEX idx_trips_bus            ON trips(bus_id);
CREATE INDEX idx_trips_datetime       ON trips(departure_datetime);

-- routes
CREATE INDEX idx_routes_source        ON routes(source);
CREATE INDEX idx_routes_dest          ON routes(destination);

-- route_stops
CREATE INDEX idx_route_stops_route    ON route_stops(route_id);

-- payments
CREATE INDEX idx_payments_booking     ON payments(booking_id);

-- ticket_history
CREATE INDEX idx_history_ticket       ON ticket_history(ticket_no);

-- JSONB GIN index for amenities queries
CREATE INDEX idx_buses_amenities      ON buses USING GIN (amenities);