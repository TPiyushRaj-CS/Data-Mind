import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path


# ============================================================
# DATABASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATABASE_DIR / "auth.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    """
    Securely hash a password using PBKDF2-HMAC-SHA256.
    """

    salt = secrets.token_bytes(32)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    return (
        f"pbkdf2_sha256$600000$"
        f"{salt.hex()}$"
        f"{password_hash.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against its stored hash.
    """

    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations)

        salt = bytes.fromhex(salt_hex)

        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash
        )

    except (ValueError, TypeError):
        return False


# ============================================================
# REGISTER USER
# ============================================================

def register_user(name: str, email: str, password: str):
    """
    Register a new user.

    Returns:
        (True, success message)
        (False, error message)
    """

    name = name.strip()
    email = email.strip().lower()

    if not name:
        return False, "Please enter your full name."

    if not email:
        return False, "Please enter your email address."

    if not password:
        return False, "Please enter a password."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    password_hash = hash_password(password)

    connection = get_connection()

    try:

        connection.execute(
            """
            INSERT INTO users
            (name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                password_hash,
                datetime.now().isoformat(timespec="seconds")
            )
        )

        connection.commit()

        return True, "Account created successfully."

    except sqlite3.IntegrityError:

        return False, "An account with this email already exists."

    finally:

        connection.close()


# ============================================================
# LOGIN USER
# ============================================================

def login_user(email: str, password: str):
    """
    Authenticate a user.

    Returns:
        user dictionary if successful
        None if unsuccessful
    """

    email = email.strip().lower()

    connection = get_connection()

    user = connection.execute(
        """
        SELECT id, name, email, password_hash, created_at
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    connection.close()

    if user is None:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"]
    }


# ============================================================
# SESSION HELPERS
# ============================================================

def initialize_auth_session(st):
    """
    Initialize Streamlit authentication session state.
    """

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user" not in st.session_state:
        st.session_state.user = None


def login_session(st, user):
    """
    Store authenticated user in Streamlit session.
    """

    st.session_state.authenticated = True
    st.session_state.user = user


def logout_session(st):
    """
    Remove authenticated user from session.
    """

    st.session_state.authenticated = False
    st.session_state.user = None


# ============================================================
# AUTH STATUS
# ============================================================

def is_logged_in(st):
    return (
        st.session_state.get("authenticated", False)
        and st.session_state.get("user") is not None
    )


# ============================================================
# USER INITIALS
# ============================================================

def get_initials(name: str) -> str:

    parts = name.strip().split()

    if not parts:
        return "G"

    if len(parts) == 1:
        return parts[0][0].upper()

    return (
        parts[0][0] +
        parts[-1][0]
    ).upper()