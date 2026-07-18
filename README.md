# 📚 Library Management System

A simple, full-stack Library Management System built with **Flask** and **MySQL**. Supports role-based access (Admin/Student), book CRUD, and an issue/return workflow with due dates.

## Features

- 🔐 User authentication (register/login) with hashed passwords
- 👥 Role-based access: **Admin** and **Student**
- 📖 Book catalog with search (by title/author)
- ➕ Admin: Add / Edit / Delete books
- 📦 Student: Issue available books (auto 14-day due date)
- 🔄 Return tracking with overdue status
- 📊 Dashboard with live stats (total books, available copies, active issues)

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS (Jinja2 templates)
- **Auth:** Werkzeug password hashing

## Project Structure

```
library-management-system/
├── app.py                 # Main Flask app & routes
├── schema.sql              # Database schema + seed data
├── requirements.txt
├── static/css/style.css
└── templates/
    ├── base.html
    ├── login.html
    ├── register.html
    ├── admin_dashboard.html
    ├── student_dashboard.html
    ├── books.html
    ├── add_book.html
    ├── edit_book.html
    └── issued_books.html
```

## Setup Instructions

1. **Clone the repo**
   ```bash
   git clone <your-repo-url>
   cd library-management-system
   ```

2. **Create a virtual environment & install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up MySQL database**
   ```bash
   mysql -u root -p < schema.sql
   ```
   Update `db_config` in `app.py` with your MySQL username/password.

4. **Create an admin user**

   The seed script inserts a placeholder admin row — replace its password hash before using it. In a Python shell:
   ```python
   from werkzeug.security import generate_password_hash
   print(generate_password_hash("admin123"))
   ```
   Copy the output and update the `admin@library.com` row in the `users` table (or just register normally and manually set that user's `role` to `'admin'` in MySQL).

5. **Run the app**
   ```bash
   python app.py
   ```
   Visit `http://127.0.0.1:5000`

## Future Improvements

- Fine calculation for overdue books
- Email notifications for due dates
- Book cover image upload
- Pagination for large catalogs
- Export issued-books report as PDF

## License

MIT
