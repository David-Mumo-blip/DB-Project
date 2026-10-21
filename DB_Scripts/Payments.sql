USE hunger_hunt;

CREATE TABLE payments (
    payment_id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    order_id int NOT NULL,
    amount decimal(10, 2) NOT NULL,
    payment_method enum('wallet') NOT NULL,
    payment_status enum('pending', 'completed', 'failed') DEFAULT 'pending', 
    created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
    KEY fk_payments_order (order_id),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE,
    CONSTRAINT chk_payment_amount CHECK ((amount >= 0))
)  