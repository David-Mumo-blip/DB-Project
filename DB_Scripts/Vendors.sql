USE hunger_hunt;
CREATE TABLE vendor_specific (
    vendor_id       INT AUTO_INCREMENT  PRIMARY KEY,
    vendor_name     VARCHAR(50)   NOT NULL,
    vendor_product  VARCHAR(50)   NOT NULL,
    vendor_price    INT NOT NULL,
    stock           INT ,
    location_name   VARCHAR(50)   NOT NULL
);

INSERT INTO vendor_specific (vendor_name, vendor_product, vendor_price, stock, location_name)
 VALUES
('Pate', 'Pizza', 130.00, 40, 'STC first floor'),
('Kilimanjaro', 'Pilau', 180.00, 30, 'STC rooftop');


CREATE TABLE vendor_overall (
    overall_id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    vendor_name_overall varchar(50) NOT NULL,
    vendor_id int DEFAULT NULL,
    KEY vendor_id (vendor_id),
    CONSTRAINT vendor_overall_ibfk_1 FOREIGN KEY (vendor_id) REFERENCES vendor_specific (vendor_id)
)