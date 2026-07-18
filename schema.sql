CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'student') DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(150) NOT NULL,
    isbn VARCHAR(50) UNIQUE,
    total_copies INT NOT NULL DEFAULT 1,
    available_copies INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS issued_books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    user_id INT NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE DEFAULT NULL,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Seed admin user: email=admin@library.com password=admin123
-- (password hash generated with werkzeug generate_password_hash - regenerate if it doesn't match your werkzeug version)
INSERT INTO users (name, email, password, role)
VALUES ('Admin', 'admin@library.com', 'pbkdf2:sha256:600000$placeholderscript$replace_this_hash', 'admin')
ON DUPLICATE KEY UPDATE email=email;

-- Sample books
INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES
('Introduction to Algorithms', 'Cormen, Leiserson, Rivest', '9780262033848', 3, 3),
('Clean Code', 'Robert C. Martin', '9780132350884', 2, 2),
('The Pragmatic Programmer', 'Andrew Hunt', '9780201616224', 2, 2);
