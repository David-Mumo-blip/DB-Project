-- Run once on an EXISTING Hunger database (re-running actualsql.sql would wipe your data).
-- Adds the 'admin' role and a test admin account.
USE Hunger;

ALTER TABLE users MODIFY role ENUM('student', 'vendor', 'admin') NOT NULL;

-- Same password as the other seeded test accounts (copied from the test student).
INSERT INTO users (name, email, password_hash, role)
SELECT 'Admin', 'admin@test.com', password_hash, 'admin'
FROM users WHERE email = 'student@test.com'
AND NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@test.com');
