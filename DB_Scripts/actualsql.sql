-- ======================================================================
-- Hunger Hunt: database setup
-- Makes registration and login work exactly like the current auth.py.
--
-- WARNING: the RESET section below DELETES these tables and their data.
-- Run the whole file in one go (same session) in MySQL Workbench.
-- ======================================================================

CREATE DATABASE IF NOT EXISTS hunger_hunt;
USE hunger_hunt;

-- ----------------------------------------------------------------------
-- RESET (removes the old structure so teammates start clean)
-- ----------------------------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS food;
DROP TABLE IF EXISTS menu_items;
DROP TABLE IF EXISTS vendor_specific;
DROP TABLE IF EXISTS vendor_overall;
DROP TABLE IF EXISTS vendors;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------------------
-- 1. Accounts (login + register read/write these)
-- ----------------------------------------------------------------------
CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('student', 'vendor') NOT NULL,
    balance DECIMAL(10, 2) NOT NULL DEFAULT 1000.00
);

-- register() inserts a row here for every new student
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- register() inserts a row here for every NEW vendor application
-- (pending until an admin approves; the admin side comes later)


-- ----------------------------------------------------------------------
-- 2. Vendor profiles (login reads this to find a vendor's overall_id)
-- ----------------------------------------------------------------------
CREATE TABLE vendor_overall (
    overall_id          INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    vendor_name_overall VARCHAR(50) NOT NULL,
    user_id             INT NULL UNIQUE,
    status              ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Menu items per vendor (many rows per vendor)
CREATE TABLE vendor_specific (
    vendor_id      INT AUTO_INCREMENT PRIMARY KEY,
    overall_id     INT NULL,
    vendor_name    VARCHAR(50) NOT NULL,
    vendor_product VARCHAR(50) NOT NULL,
    vendor_price   DECIMAL(10, 2) NOT NULL,
    stock          INT,
    location_name  VARCHAR(50) NOT NULL,
    image_filename VARCHAR(255) NULL,
    FOREIGN KEY (overall_id) REFERENCES vendor_overall(overall_id)
);

-- ----------------------------------------------------------------------
-- 3. Ordering tables (same as before; customer_id now points at students)
-- ----------------------------------------------------------------------
CREATE TABLE menu_items (
    id             INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    vendor_id      INT NOT NULL,
    food_name           VARCHAR(100) NOT NULL,
    price               DECIMAL(10, 2) NOT NULL,
    category            ENUM('appetizer', 'main_course', 'dessert', 'beverage') NOT NULL,
    availability_status ENUM('available', 'unavailable') DEFAULT 'available',
    quantity_available  INT NOT NULL DEFAULT 0,
    image_filename VARCHAR(255) NOT NULL DEFAULT 'image1.jpeg',
    CONSTRAINT chk_menu_price
        CHECK (price >= 0),

    CONSTRAINT chk_menu_quantity
        CHECK (quantity_available >= 0),

    CONSTRAINT fk_menu_vendor
        FOREIGN KEY (vendor_id)
        REFERENCES vendor_specific(vendor_id)
        ON DELETE CASCADE
);

CREATE TABLE orders (
    order_id     INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    customer_id  INT NOT NULL,
    vendor_id    INT NOT NULL,
    food_id      INT NOT NULL,
    order_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    status       ENUM('pending', 'processing', 'completed', 'cancelled') DEFAULT 'pending',
    FOREIGN KEY (customer_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (vendor_id)   REFERENCES vendor_specific(vendor_id) ON DELETE CASCADE,
    FOREIGN KEY (food_id)     REFERENCES menu_items(id) ON DELETE CASCADE,
    CONSTRAINT chk_total_amount CHECK (total_amount >= 0)
);

CREATE TABLE payments (
    payment_id     INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    order_id       INT NOT NULL,
    amount         DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('wallet') NOT NULL,
    payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    created_at     TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    KEY fk_payments_order (order_id),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    CONSTRAINT chk_payment_amount CHECK (amount >= 0)
);

-- ----------------------------------------------------------------------
-- 4. Starter data: one test student and the four approved vendors
--    All test accounts share one password (the hash from the old snapshot).
-- ----------------------------------------------------------------------
SET @pw = 'scrypt:32768:8:1$KZuhywpFzVPf9lvL$eb3723ba14f7d58bdf8b36b7bbd0844be3143f0daa0358be992a32c7bbe66a98196819d0c33f1aa7c6c4e9c9a9e99e446671f12ded5cff63b483abca85c0e4c9';

INSERT INTO users (id, name, email, password_hash, role) VALUES
    (1, 'Test Student', 'student@test.com',   @pw, 'student'),
    (2, 'Pate',         'pate@test.com',      @pw, 'vendor'),
    (3, 'Georgie',      'georgies@test.com',  @pw, 'vendor'),
    (4, 'Kerinton',     'kerinton@test.com',  @pw, 'vendor'),
    (5, 'Upesi Joint',  'upesi@test.com',     @pw, 'vendor');

INSERT INTO students (user_id) VALUES (1);

-- overall_id values 5-8 are set on purpose: VENDOR_HOME and the
-- @vendor_only(...) decorators in auth.py use these exact numbers.
INSERT INTO vendor_overall (overall_id, vendor_name_overall, user_id, status) VALUES
    (5, 'Pate Cafeteria', 2, 'approved'),
    (6, 'Georgie',        3, 'approved'),
    (7, 'Upesi Joint',    5, 'approved'),
    (8, 'Kerinton',       4, 'approved');

INSERT INTO vendor_specific (overall_id, vendor_name, vendor_product, vendor_price, stock, location_name) VALUES
    (5, 'Pate',    'Pizza', 130.00, 40, 'STC first floor'),
    (6, 'Georgie', 'Pilau', 180.00, 30, 'STC rooftop');

-- ----------------------------------------------------------------------
-- Insert Approved Vendors into the `vendors` table (needed for menu_items FK)
-- ----------------------------------------------------------------------
INSERT INTO vendors (id, user_id, name, location_description, campus_status, approval_status) VALUES
    (1, 2, 'Pate Cafeteria', 'STC first floor', 'on-campus', 'approved'),
    (2, 3, 'Georgies', 'STC rooftop', 'on-campus', 'approved'),
    (3, 4, 'Kerinton', 'Student Center', 'on-campus', 'approved'),
    (4, 5, 'Upesi Joint', 'Main Gate', 'on-campus', 'approved');


-- ----------------------------------------------------------------------
-- Insert Menu Items (3 items per vendor, price as specified, initial quantity = 20)
-- ----------------------------------------------------------------------
INSERT INTO menu_items (vendor_id, food_name, price, category, availability_status, quantity_available, image_filename) VALUES
    -- Pate (vendor_id = 1)
    (1, 'Chapati', 20.00, 'main_course', 'available', 20, 'image1.jpeg'),
    (1, 'Samosa', 50.00, 'appetizer', 'available', 20, 'image2.jpeg'),
    (1, 'Mandazi', 10.00, 'dessert', 'available', 20, 'image3.jpeg'),

    -- Georgies (vendor_id = 2)
    (2, 'Smocha', 70.00, 'main_course', 'available', 20, 'image1.jpeg'),
    (2, 'Mayai Pasua', 30.00, 'appetizer', 'available', 20, 'image2.jpeg'),
    (2, 'Smokie Pasua', 40.00, 'appetizer', 'available', 20, 'image3.jpeg'),

    -- Kerinton (vendor_id = 3)
    (3, 'Bhajia', 70.00, 'appetizer', 'available', 20, 'image1.jpeg'),
    (3, 'Fried Chicken', 250.00, 'main_course', 'available', 20, 'image2.jpeg'),
    (3, 'Fresh juice', 70.00, 'beverage', 'available', 20, 'image3.jpeg'),

    -- Upesi Joint (vendor_id = 4)
    (4, 'Pilau', 100.00, 'main_course', 'available', 20, 'image1.jpeg'),
    (4, 'Chicken stew', 150.00, 'main_course', 'available', 20, 'image2.jpeg'),
    (4, 'Chips', 100.00, 'main_course', 'available', 20, 'image3.jpeg');
-- ----------------------------------------------------------------------
-- 5. Quick check: every vendor row should show a user and 'approved'
-- ----------------------------------------------------------------------
SELECT u.id AS user_id, u.email, u.role, v.overall_id, v.vendor_name_overall, v.status
FROM users u
LEFT JOIN vendor_overall v ON v.user_id = u.id;