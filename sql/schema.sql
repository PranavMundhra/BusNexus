-- =========================
-- 1. TABLE CREATION
-- =========================

CREATE TABLE "User" (
    user_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    contact_no TEXT
);

CREATE TABLE Passenger (
    user_id INT PRIMARY KEY REFERENCES "User"(user_id)
);

CREATE TABLE Coordinator (
    user_id INT PRIMARY KEY REFERENCES "User"(user_id)
);

CREATE TABLE Employee (
    emp_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    contact_no TEXT
);

CREATE TABLE Driver (
    emp_id INT PRIMARY KEY REFERENCES Employee(emp_id)
);

CREATE TABLE Bus (
    bus_id SERIAL PRIMARY KEY,
    bus_type TEXT,
    capacity INT CHECK (capacity > 0),
    amenities JSONB,
    user_id INT REFERENCES Coordinator(user_id)
);

CREATE TABLE Route (
    route_id SERIAL PRIMARY KEY,
    source TEXT,
    destination TEXT,
    distance INT,
    base_fare NUMERIC
);

CREATE TABLE Stop (
    stop_id SERIAL PRIMARY KEY,
    stop_name TEXT,
    location TEXT
);

CREATE TABLE Route_Stop (
    route_id INT REFERENCES Route(route_id),
    stop_id INT REFERENCES Stop(stop_id),
    stop_sequence INT,
    arrival_time TIME,
    departure_time TIME,
    PRIMARY KEY (route_id, stop_id)
);

CREATE TABLE Trip (
    trip_id SERIAL PRIMARY KEY,
    bus_id INT REFERENCES Bus(bus_id),
    route_id INT REFERENCES Route(route_id),
    driver_id INT REFERENCES Driver(emp_id),
    departure_datetime TIMESTAMP,
    arrival_datetime TIMESTAMP,
    seats_available INT,
    status TEXT CHECK (status IN ('scheduled','completed'))
);

CREATE TABLE Booking (
    booking_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES "User"(user_id),
    trip_id INT REFERENCES Trip(trip_id),
    boarding_stop INT REFERENCES Stop(stop_id),
    dropping_stop INT REFERENCES Stop(stop_id),
    journey_date DATE,
    seat_no INT CHECK (seat_no > 0),
    booking_status TEXT CHECK (booking_status IN ('confirmed','cancelled','waitlisted')),
    booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Ticket (
    ticket_no SERIAL,
    booking_id INT REFERENCES Booking(booking_id),
    fare NUMERIC,
    duration INTERVAL,
    PRIMARY KEY (ticket_no, booking_id)
);

CREATE TABLE Payment (
    payment_id SERIAL PRIMARY KEY,
    booking_id INT UNIQUE REFERENCES Booking(booking_id),
    amount NUMERIC,
    payment_mode TEXT,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);