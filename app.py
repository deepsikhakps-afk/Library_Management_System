from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

# ---------------- DB CONFIG ----------------
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

def get_db():
    return mysql.connector.connect(**db_config)

# ---------------- DECORATORS ----------------
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Access denied.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ---------------- AUTH ----------------
@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        role = "student"  # public signup is always student; admin created manually/seed

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s)",
                (name, email, password, role)
            )
            db.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("Email already registered.", "danger")
        finally:
            cursor.close()
            db.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required()
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM books")
    total_books = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM books WHERE available_copies > 0")
    available_books = cursor.fetchone()["total"]

    if session["role"] == "admin":
        cursor.execute("SELECT COUNT(*) AS total FROM issued_books WHERE return_date IS NULL")
        active_issues = cursor.fetchone()["total"]
        cursor.close()
        db.close()
        return render_template("admin_dashboard.html",
                                total_books=total_books,
                                available_books=available_books,
                                active_issues=active_issues)
    else:
        cursor.execute("""
            SELECT b.title, ib.issue_date, ib.due_date
            FROM issued_books ib
            JOIN books b ON b.id = ib.book_id
            WHERE ib.user_id=%s AND ib.return_date IS NULL
        """, (session["user_id"],))
        my_books = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template("student_dashboard.html",
                                total_books=total_books,
                                available_books=available_books,
                                my_books=my_books)

# ---------------- BOOKS (ADMIN CRUD) ----------------
@app.route("/books")
@login_required()
def books():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    search = request.args.get("q", "")
    if search:
        cursor.execute(
            "SELECT * FROM books WHERE title LIKE %s OR author LIKE %s",
            (f"%{search}%", f"%{search}%")
        )
    else:
        cursor.execute("SELECT * FROM books")
    all_books = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("books.html", books=all_books, search=search)

@app.route("/books/add", methods=["GET", "POST"])
@login_required(role="admin")
def add_book():
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        copies = int(request.form["copies"])

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (%s,%s,%s,%s,%s)",
            (title, author, isbn, copies, copies)
        )
        db.commit()
        cursor.close()
        db.close()
        flash("Book added successfully.", "success")
        return redirect(url_for("books"))
    return render_template("add_book.html")

@app.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
@login_required(role="admin")
def edit_book(book_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        total_copies = int(request.form["total_copies"])

        cursor.execute("SELECT total_copies, available_copies FROM books WHERE id=%s", (book_id,))
        current = cursor.fetchone()
        issued_count = current["total_copies"] - current["available_copies"]
        new_available = total_copies - issued_count

        cursor.execute(
            "UPDATE books SET title=%s, author=%s, isbn=%s, total_copies=%s, available_copies=%s WHERE id=%s",
            (title, author, isbn, total_copies, new_available, book_id)
        )
        db.commit()
        cursor.close()
        db.close()
        flash("Book updated.", "success")
        return redirect(url_for("books"))

    cursor.execute("SELECT * FROM books WHERE id=%s", (book_id,))
    book = cursor.fetchone()
    cursor.close()
    db.close()
    return render_template("edit_book.html", book=book)

@app.route("/books/delete/<int:book_id>")
@login_required(role="admin")
def delete_book(book_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM books WHERE id=%s", (book_id,))
    db.commit()
    cursor.close()
    db.close()
    flash("Book deleted.", "info")
    return redirect(url_for("books"))

# ---------------- ISSUE / RETURN ----------------
@app.route("/books/issue/<int:book_id>")
@login_required(role="student")
def issue_book(book_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT available_copies FROM books WHERE id=%s", (book_id,))
    book = cursor.fetchone()

    if not book or book["available_copies"] <= 0:
        flash("Book not available.", "danger")
        cursor.close()
        db.close()
        return redirect(url_for("books"))

    issue_date = datetime.now().date()
    due_date = issue_date + timedelta(days=14)

    cursor.execute(
        "INSERT INTO issued_books (book_id, user_id, issue_date, due_date) VALUES (%s,%s,%s,%s)",
        (book_id, session["user_id"], issue_date, due_date)
    )
    cursor.execute(
        "UPDATE books SET available_copies = available_copies - 1 WHERE id=%s",
        (book_id,)
    )
    db.commit()
    cursor.close()
    db.close()
    flash(f"Book issued. Due date: {due_date}", "success")
    return redirect(url_for("dashboard"))

@app.route("/books/return/<int:issue_id>")
@login_required()
def return_book(issue_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT book_id FROM issued_books WHERE id=%s", (issue_id,))
    record = cursor.fetchone()

    if record:
        cursor.execute(
            "UPDATE issued_books SET return_date=%s WHERE id=%s",
            (datetime.now().date(), issue_id)
        )
        cursor.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id=%s",
            (record["book_id"],)
        )
        db.commit()
        flash("Book returned successfully.", "success")

    cursor.close()
    db.close()
    return redirect(url_for("dashboard"))

@app.route("/issued")
@login_required(role="admin")
def issued_books():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT ib.id, b.title, u.name, ib.issue_date, ib.due_date, ib.return_date
        FROM issued_books ib
        JOIN books b ON b.id = ib.book_id
        JOIN users u ON u.id = ib.user_id
        ORDER BY ib.return_date IS NULL DESC, ib.due_date ASC
    """)
    records = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("issued_books.html", records=records, today=datetime.now().date())

if __name__ == "__main__":
    app.run(debug=True)
