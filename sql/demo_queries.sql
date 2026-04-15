SELECT * FROM users;
SELECT * FROM passengers;
SELECT * FROM coordinators;
SELECT * FROM employees;
SELECT * FROM drivers;
SELECT * FROM maintenance_staff;

SELECT p.*
FROM passengers p
LEFT JOIN users u ON p.user_id = u.user_id
WHERE u.user_id IS NULL;
-- should return 0 queries

SELECT d.emp_id
FROM drivers d
JOIN maintenance_staff m ON d.emp_id = m.emp_id;
-- should return 0 queries

SELECT u.user_id, u.role, 
       CASE 
           WHEN p.user_id IS NOT NULL THEN 'passenger'
           WHEN c.user_id IS NOT NULL THEN 'coordinator'
       END AS subtype
FROM users u
LEFT JOIN passengers p ON u.user_id = p.user_id
LEFT JOIN coordinators c ON u.user_id = c.user_id;
-- role matche