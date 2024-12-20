import pytest
import sqlite3
from app import app, db_path


@pytest.fixture
def client():
    # Setup: Create a test client and temporary database
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            # Reinitialize the database for tests
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users")
            cursor.execute("DELETE FROM notes")
            conn.commit()
            conn.close()
        yield client


def test_registration_redirects_to_login(client):
    # Attempt to register a new user
    response = client.post(
        "/register", data={"username": "newuser", "password": "newpass"}
    )

    # Assert redirection to the login page
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_login_success(client):
    # Register the user first
    client.post("/register", data={"username": "testuser", "password": "testpass"})

    # Attempt login with correct credentials
    response = client.post(
        "/login", data={"username": "testuser", "password": "testpass"}
    )

    # Assert redirection to the dashboard (at `/`)
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

def test_access_restrictions(client):
    # Dashboard should not be accessible without login
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

def test_create_note(client):
    # Step 1: Register and log in the user
    client.post("/register", data={"username": "testuser", "password": "testpass"})
    client.post("/login", data={"username": "testuser", "password": "testpass"})

    # Step 2: Add a new note
    note_data = {"title": "Test Note", "description": "This is a test note"}
    response = client.post("/add_note", data=note_data)

    # Step 3: Assert that the response redirects to the dashboard
    assert response.status_code == 302
    assert "/" in response.headers["Location"]

    # Step 4: Verify the note is added (check if the note appears in the dashboard)
    dashboard_response = client.get("/")

    # Step 5: Assert that the newly added note is visible in the dashboard
    assert b"Test Note" in dashboard_response.data
    assert b"This is a test note" in dashboard_response.data
