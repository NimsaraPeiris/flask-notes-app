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

# Initiate the db_path
# For Docker
if os.path.exists('/.dockerenv'):
    db_path = '/app/database/database.db'  # Docker volume path
else:
    # For local
    db_folder = os.path.join(os.getcwd(), 'database')

    # Check if the folder exists, create if not
    if not os.path.exists(db_folder):
        os.makedirs(db_folder)
    db_path = os.path.join(db_folder, 'database.db')

    app.logger.info(f"Database path is ready at: {db_path}")

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
            title TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
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
def get_db():
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
        with get_db() as conn:
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
        with get_db() as conn:
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
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        )
        user_notes = cursor.fetchall()

    return render_template("dashboard.html", notes=user_notes)


@app.route("/add_note", methods=["POST"])
def add_note():
    # Check if the user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    task = request.form["title"]
    category = request.form.get("description")
    user_id = session["user_id"]

    # Insert the new note into the database
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notes (title, user_id, description) VALUES (?, ?, ?)",
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
    with get_db() as conn:
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

@app.route("/edit_note/<int:note_id>", methods=["POST"])
def edit_note(note_id):
    # Check if the user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]

    with get_db() as conn:
        cursor = conn.cursor()

        # Check if the selected note is available
        cursor.execute(
            "SELECT title, description FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id)
        )
        note = cursor.fetchone()
        if not note:
            flash("Note not found", "danger")

        # Pass the details and render the edit_note view
        return render_template("edit_note.html", note_id=note_id, title=note[0], description=note[1])

@app.route('/update_note/<int:note_id>', methods=["POST"])
def update_note(note_id):
    # Check if the user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]

    # Get updated data from the form
    updated_title = request.form["title"]
    updated_description = request.form["description"]

    with get_db() as conn:
        cursor = conn.cursor()

        # Update the note in the database
        cursor.execute(
            "UPDATE notes SET title = ?, description = ? WHERE id = ? AND user_id = ?",
            (updated_title, updated_description, note_id, user_id),
        )
        conn.commit()

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
