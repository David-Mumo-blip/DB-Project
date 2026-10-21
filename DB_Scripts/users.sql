USE hunger_hunt;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'vendor') NOT NULL
);

INSERT INTO users (name, email, password_hash, role)
VALUES
    ('Test Student', 'student@test.com', 'scrypt:32768:8:1$KZuhywpFzVPf9lvL$eb3723ba14f7d58bdf8b36b7bbd0844be3143f0daa0358be992a32c7bbe66a98196819d0c33f1aa7c6c4e9c9a9e99e446671f12ded5cff63b483abca85c0e4c9', 'student'),
    ('Pate', 'pate@test.com', 'scrypt:32768:8:1$KZuhywpFzVPf9lvL$eb3723ba14f7d58bdf8b36b7bbd0844be3143f0daa0358be992a32c7bbe66a98196819d0c33f1aa7c6c4e9c9a9e99e446671f12ded5cff63b483abca85c0e4c9', 'vendor'),
    ('Kilimanjaro', 'georgies@test.com', 'scrypt:32768:8:1$KZuhywpFzVPf9lvL$eb3723ba14f7d58bdf8b36b7bbd0844be3143f0daa0358be992a32c7bbe66a98196819d0c33f1aa7c6c4e9c9a9e99e446671f12ded5cff63b483abca85c0e4c9', 'vendor')