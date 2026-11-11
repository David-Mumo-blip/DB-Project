-- Brings an EXISTING Hunger database up to date WITHOUT wiping data.
-- Run this whole file once in MySQL Workbench (after admin_migration.sql if you haven't run that).
-- If a line fails with "Duplicate column name", that column already exists: ignore it and
-- run the remaining lines.
USE Hunger;

-- Vendor money: balance starts at 0, goal drives the dashboard progress bar
ALTER TABLE vendors ADD COLUMN balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00;
ALTER TABLE vendors ADD COLUMN revenue_goal DECIMAL(10, 2) NOT NULL DEFAULT 10000.00;

-- Orders: how many were ordered, and vendor self-orders have no student (NULL customer)
ALTER TABLE orders MODIFY customer_id INT NULL;
ALTER TABLE orders ADD COLUMN quantity INT NOT NULL DEFAULT 1;

-- Notifications (new order for the vendor, order ready for the student)
CREATE TABLE IF NOT EXISTS notifications (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    order_id INT NULL,
    message VARCHAR(255) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE SET NULL
);
