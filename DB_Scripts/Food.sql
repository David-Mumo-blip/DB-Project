USE hunger_hunt;

CREATE TABLE food (
    food_id int NOT NULL AUTO_INCREMENT,
    food_name varchar(100) NOT NULL,
    price decimal(10, 2) NOT NULL,
    category enum(
        'appetizer', 
        'main_course',
        'dessert',
        'beverage'
    ) NOT NULL,
    availability_status enum('available', 'unavailable') DEFAULT 'available',
    PRIMARY KEY (food_id),
    CONSTRAINT chk_food_price CHECK ((price >= 0))
)   