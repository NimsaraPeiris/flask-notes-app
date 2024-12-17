import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables from .env file
load_dotenv()

# Initialize the flask app
app = Flask(__name__)

# Load Secret keys
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')
flask_env = os.getenv('FLASK_ENV', 'production')

# Enable Debugging only in Development
if flask_env == 'development':
    app.config['DEBUG'] = True
    app.config['ENV'] = 'development'
else:
    app.config['DEBUG'] = False
    app.config['ENV'] = 'production'

# Enable Flask's logging in production
if not app.debug:
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

# Get the current working directory and append database/database.db path
#db_path = os.path.join(os.getcwd(), "database", "database.db")
if os.path.exists('/.dockerenv'):  # Check if running in Docker
    db_path = '/app/database/database.db'  # Path to the volume in Docker
else:
    db_path = os.path.join(os.getcwd(), 'database', 'database.db')

def init_db():    
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
            )
        """
        )
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
        )
        conn.commit()
        conn.close()
        app.logger.info("Database and tables created successfully!")
    else:
        app.logger.info("Database already exists")


# Initialize the databse
with app.app_context():
    init_db()


# Function to connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Connect to the db and insert the user
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check if the given username is taken
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("username already exists!", "danger")
                return redirect(url_for("registration"))

            # Insert the new user to db
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password),
            )
            conn.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    return render_template("registration.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check the user credentails
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")


# Main route
@app.route("/", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Fetch the notes for the logged-in user
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE user_id = ?", (user_id,))
        user_notes = cursor.fetchall()

    return render_template("dashboard.html", notes=user_notes)


@app.route("/add_note", methods=["POST"])
def add_note():
    # Check if the user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    task = request.form["task"]
    category = request.form.get("category", "General")  # Default to 'General' if no category provided
    user_id = session["user_id"]

    # Insert the new note into the database
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notes (task, user_id, category) VALUES (?, ?, ?)",
            (task, user_id, category),
        )
        conn.commit()

    return redirect(url_for("dashboard"))


@app.route("/delete_note/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    # Check if the user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]

    # Remove selected note from the database
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # check if the note exists and belongs to the user
        cursor.execute(
            "SELECT * FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id)
        )
        note = cursor.fetchone()
        if note:
            cursor.execute(
                "DELETE FROM notes WHERE id = ? AND user_id = ?",(note_id, user_id) 
                )
            conn.commit()
            flash("Note deleted successfully!", "success")
        else:
            flash("Note not found", "danger")

    return redirect(url_for("dashboard"))

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    return redirect(url_for('login'))

# Health check route (not used in the k8s deployment.yml)
@app.route('/_status/healthz', methods=['GET'])
def healthz():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
