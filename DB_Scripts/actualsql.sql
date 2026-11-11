CREATE DATABASE IF NOT EXISTS Hunger;
USE Hunger;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS menu_items;
DROP TABLE IF EXISTS vendors;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Accounts
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'vendor', 'admin') NOT NULL
);

CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
	balance DECIMAL(10, 2) NOT NULL DEFAULT 1000.00,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 2. Master Vendors Table (Replaces vendor_overall and vendor_specific duplication)
CREATE TABLE vendors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    location_description VARCHAR(255) NULL,
    campus_status ENUM('on-campus', 'off-campus') NOT NULL,
    approval_status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'approved',
    image_filename VARCHAR(255) NOT NULL DEFAULT 'default_vendor.jpeg',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Unified Menu Items Table (Replaces vendor_specific and food)
CREATE TABLE menu_items (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    vendor_id INT NOT NULL,
    food_name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category ENUM('appetizer', 'main_course', 'dessert', 'beverage') NOT NULL,
    availability_status ENUM('available', 'unavailable') DEFAULT 'available',
    quantity_available INT NOT NULL DEFAULT 20,
    image_filename VARCHAR(255) NOT NULL DEFAULT 'image1.jpeg',

    CONSTRAINT chk_menu_price CHECK (price >= 0),
    CONSTRAINT chk_menu_quantity CHECK (quantity_available >= 0),
    CONSTRAINT fk_menu_vendor FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
);

-- 4. Orders & Payments
CREATE TABLE orders (
    order_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NULL,            -- NULL = the vendor ordered their own product
    vendor_id INT NOT NULL,
    food_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'cancelled') DEFAULT 'pending',
    
    FOREIGN KEY (customer_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
    FOREIGN KEY (food_id) REFERENCES menu_items(id) ON DELETE CASCADE,
    CONSTRAINT chk_total_amount CHECK (total_amount >= 0)
);

CREATE TABLE payments (
    payment_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('wallet') NOT NULL,
    payment_status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    CONSTRAINT chk_payment_amount CHECK (amount >= 0)
);
CREATE TABLE notifications (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    order_id INT NULL,
    message VARCHAR(255) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE SET NULL
);

ALTER TABLE vendors ADD COLUMN balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00;
ALTER TABLE vendors ADD COLUMN revenue_goal DECIMAL(10, 2) NOT NULL DEFAULT 10000.00;
-- 5. Starter Data & Inserts
SET @pw = 'scrypt:32768:8:1$KZuhywpFzVPf9lvL$eb3723ba14f7d58bdf8b36b7bbd0844be3143f0daa0358be992a32c7bbe66a98196819d0c33f1aa7c6c4e9c9a9e99e446671f12ded5cff63b483abca85c0e4c9';

INSERT INTO users (id, name, email, password_hash, role) VALUES
    (1, 'Test Student', 'student@test.com', @pw, 'student'),
    (2, 'Pate', 'pate@test.com', @pw, 'vendor'),
    (3, 'Georgie', 'georgies@test.com', @pw, 'vendor'),
    (4, 'Kerinton', 'kerinton@test.com', @pw, 'vendor'),
    (5, 'Upesi Joint', 'upesi@test.com', @pw, 'vendor'),
    (6, 'Admin', 'admin@test.com', @pw, 'admin');

INSERT INTO students (user_id) VALUES (1);

-- Insert Master Vendors
INSERT INTO vendors (id, user_id, name, location_description, campus_status, approval_status, image_filename) VALUES
    (1, 2, 'Pate Cafeteria', 'STC first floor', 'on-campus', 'approved', 'pate.jpeg'),
    (2, 3, 'Georgies', 'Siwaka', 'off-campus', 'approved', 'georgies.jpeg'),
    (3, 4, 'Kireton', 'Near Siwaka', 'off-campus', 'approved', 'kireton.jpeg'),
    (4, 5, 'Upesi Joint', 'STC First floor', 'on-campus', 'approved', 'upesi.jpeg');

-- Insert Menu Items (3 items per vendor, stock = 20)
INSERT INTO menu_items (vendor_id, food_name, price, category, availability_status, quantity_available, image_filename) VALUES
    -- Pate (vendor_id = 1)
    (1, 'Chapati', 20.00, 'main_course', 'available', 20, 'chapo.jpg'),
    (1, 'Samosa', 50.00, 'appetizer', 'available', 20, 'samosa.jpeg'),
    (1, 'Mandazi', 10.00, 'dessert', 'available', 20, 'mandazi.jpeg'),

    -- Georgies (vendor_id = 2)
    (2, 'Smocha', 70.00, 'main_course', 'available', 20, 'smocha.jpeg'),
    (2, 'Mayai Pasua', 30.00, 'appetizer', 'available', 20, 'egg.jpeg'),
    (2, 'Smokie Pasua', 40.00, 'appetizer', 'available', 20, 'smokie.jpeg'),

    -- Kerinton (vendor_id = 3)
    (3, 'Bhajia', 70.00, 'appetizer', 'available', 20, 'bhajia.jpeg'),
    (3, 'Fried Chicken', 250.00, 'main_course', 'available', 20, 'chicken.jpeg'),
    (3, 'Fresh juice', 70.00, 'beverage', 'available', 20, 'juice.jpeg'),

    -- Upesi Joint (vendor_id = 4)
    (4, 'Pilau', 100.00, 'main_course', 'available', 20, 'pilau.jpeg'),
    (4, 'Chicken stew', 150.00, 'main_course', 'available', 20, 'chickenstew.jpeg'),
    (4, 'Chips', 100.00, 'main_course', 'available', 20, 'fries.jpeg');