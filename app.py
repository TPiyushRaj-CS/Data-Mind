import streamlit as st
from pathlib import Path
import hashlib
import hmac
import html
import re
import secrets
import sqlite3
from datetime import datetime, timezone


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="DataMind AI",
    page_icon=":material/database:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
CSS_PATH = BASE_DIR / "styles" / "main.css"


# ============================================================
# AUTHENTICATION / DATABASE
# ============================================================

DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "datamind.db"


def get_db_connection():
    """Return a SQLite connection for the DataMind AI user database."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    """Create the users table if it does not already exist."""
    with get_db_connection() as connection:
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


def normalize_email(email):
    return email.strip().lower()


def hash_password(password):
    """Hash a password with PBKDF2-HMAC-SHA256 and a random salt."""
    salt = secrets.token_bytes(16)
    iterations = 310_000
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password, stored_hash):
    """Verify a password against a stored PBKDF2 hash."""
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False

        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def get_user_by_email(email):
    """Return a user by normalized email, or None."""
    normalized = normalize_email(email)

    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, email, password_hash
            FROM users
            WHERE email = ?
            """,
            (normalized,),
        ).fetchone()

    return dict(row) if row else None


def create_user(name, email, password):
    """Create a user. Returns the user dict, or None for duplicate email."""
    clean_name = " ".join(name.strip().split())
    normalized = normalize_email(email)
    password_hash = hash_password(password)

    try:
        with get_db_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    clean_name,
                    normalized,
                    password_hash,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            connection.commit()

            return {
                "id": cursor.lastrowid,
                "name": clean_name,
                "email": normalized,
            }
    except sqlite3.IntegrityError:
        return None


def authenticate_user(email, password):
    """Authenticate a user by email and password."""
    user = get_user_by_email(email)

    if not user or not verify_password(password, user["password_hash"]):
        return None

    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
    }


def init_auth_state():
    """Initialize guest/authenticated session state."""
    defaults = {
        "logged_in": False,
        "user_id": None,
        "user_name": None,
        "user_email": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_logged_in(user):
    st.session_state.logged_in = True
    st.session_state.user_id = user["id"]
    st.session_state.user_name = user["name"]
    st.session_state.user_email = user["email"]


def logout_user():
    for key in (
        "logged_in",
        "user_id",
        "user_name",
        "user_email",
    ):
        st.session_state.pop(key, None)

    init_auth_state()
    st.rerun()


def get_initials(name):
    """Return initials for the account avatar."""
    parts = name.strip().split()

    if not parts:
        return "GU"

    if len(parts) == 1:
        return parts[0][:2].upper()

    return f"{parts[0][0]}{parts[-1][0]}".upper()


def valid_email(email):
    return bool(
        re.fullmatch(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            email.strip(),
        )
    )


# Create the local database and initialize the current visitor as Guest.
init_database()
init_auth_state()


# ============================================================
# LOAD DATAMIND AI THEME
# ============================================================

if CSS_PATH.exists():
    with open(CSS_PATH, "r", encoding="utf-8") as css_file:
        st.html(f"<style>{css_file.read()}</style>")


# ============================================================
# MATERIAL SYMBOLS
# ============================================================

st.html(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200'
    );

    [data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded' !important;
        font-weight: normal !important;
        font-style: normal !important;
        font-variation-settings:
            'FILL' 0,
            'wght' 400,
            'GRAD' 0,
            'opsz' 24 !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        white-space: nowrap !important;
        -webkit-font-smoothing: antialiased;
    }

    .dm-card-icon {
        font-family: 'Material Symbols Rounded' !important;
        font-weight: normal !important;
        font-style: normal !important;
        font-variation-settings:
            'FILL' 1,
            'wght' 500,
            'GRAD' 0,
            'opsz' 32 !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        white-space: nowrap !important;
        -webkit-font-smoothing: antialiased;
    }

    .dm-inline-icon {
        font-family: 'Material Symbols Rounded' !important;
        font-weight: normal !important;
        font-style: normal !important;
        font-variation-settings:
            'FILL' 1,
            'wght' 500,
            'GRAD' 0,
            'opsz' 24 !important;
        line-height: 1 !important;
        vertical-align: middle;
    }

    /* ========================================================
       HOME PAGE ENHANCEMENTS
       ======================================================== */

    .dm-status-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        margin: 4px 0 20px 0;
    }

    .dm-ai-status {
        display: inline-flex;
        align-items: center;
        gap: 9px;
        padding: 8px 14px;
        border-radius: 999px;
        background: rgba(139, 92, 246, 0.08);
        border: 1px solid rgba(139, 92, 246, 0.16);
        color: #6d28d9;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.01em;
    }

    .dm-status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #8b5cf6;
        box-shadow: 0 0 0 5px rgba(139, 92, 246, 0.10);
    }

    .dm-platform-label {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 600;
    }

    .dm-metrics {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin: 24px 0 38px 0;
    }

    .dm-metric-card {
        position: relative;
        overflow: hidden;
        padding: 20px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid #e7e5ef;
        box-shadow: 0 8px 25px rgba(76, 29, 149, 0.055);
        transition: all 0.25s ease;
    }

    .dm-metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 32px rgba(76, 29, 149, 0.09);
        border-color: #ddd6fe;
    }

    .dm-metric-icon {
        width: 38px;
        height: 38px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 11px;
        background: #f5f3ff;
        color: #7c3aed;
        margin-bottom: 12px;
    }

    .dm-metric-value {
        font-size: 24px;
        line-height: 1.1;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 5px;
    }

    .dm-metric-label {
        color: #64748b;
        font-size: 12px;
        font-weight: 600;
    }

    .dm-how-section {
        margin-top: 52px;
        padding: 32px;
        border-radius: 24px;
        background:
            linear-gradient(
                135deg,
                rgba(255,255,255,0.96),
                rgba(248,250,252,0.92)
            );
        border: 1px solid #e2e8f0;
        box-shadow: 0 12px 35px rgba(30, 41, 59, 0.05);
    }

    .dm-how-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 18px;
        margin-top: 24px;
    }

    .dm-how-card {
        padding: 22px;
        border-radius: 18px;
        background: #ffffff;
        border: 1px solid #e8eaf0;
        transition: all 0.25s ease;
    }

    .dm-how-card:hover {
        transform: translateY(-3px);
        border-color: #ddd6fe;
        box-shadow: 0 12px 28px rgba(76, 29, 149, 0.07);
    }

    .dm-how-number {
        width: 34px;
        height: 34px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 10px;
        background: #ede9fe;
        color: #6d28d9;
        font-weight: 800;
        font-size: 13px;
        margin-bottom: 14px;
    }

    .dm-how-card h3 {
        margin: 0 0 7px 0;
        color: #1e293b;
        font-size: 16px;
    }

    .dm-how-card p {
        margin: 0;
        color: #64748b;
        font-size: 13px;
        line-height: 1.6;
    }

    .dm-bottom-cta {
        margin: 42px 0 20px 0;
        padding: 30px;
        border-radius: 22px;
        background:
            linear-gradient(
                135deg,
                #f5f3ff 0%,
                #eef2ff 52%,
                #ecfeff 100%
            );
        border: 1px solid #ddd6fe;
        text-align: center;
    }

    .dm-bottom-cta h2 {
        margin: 0 0 8px 0;
        color: #1e293b;
        font-size: 24px;
        font-weight: 800;
    }

    .dm-bottom-cta p {
        margin: 0;
        color: #64748b;
        font-size: 14px;
    }

    .dm-footer {
        text-align: center;
        padding: 24px 0 34px 0;
        color: #94a3b8;
        font-size: 12px;
    }

    .dm-footer strong {
        color: #7c3aed;
    }

    @media (max-width: 900px) {

        .dm-metrics {
            grid-template-columns: repeat(2, 1fr);
        }

        .dm-how-grid {
            grid-template-columns: 1fr;
        }

    }

    @media (max-width: 600px) {

        .dm-metrics {
            grid-template-columns: 1fr;
        }

        .dm-how-section {
            padding: 22px;
        }

    }

    </style>
    """
)


# ============================================================
# PAGE REGISTRY
# ============================================================
# Declared before page functions so Pylance knows that PAGES exists.
# The actual st.Page objects are populated below before st.navigation runs.

PAGES = {}


# ============================================================
# PAGE FUNCTIONS
# ============================================================

def home_page():

    # --------------------------------------------------------
    # TOP STATUS
    # --------------------------------------------------------

    st.html(
        """
        <div class="dm-status-row">

            <div class="dm-ai-status">
                <span class="dm-status-dot"></span>
                AI Workspace Ready
            </div>

            <div class="dm-platform-label">
                Intelligent Data Analysis Platform
            </div>

        </div>
        """
    )

    # --------------------------------------------------------
    # HERO SECTION
    # --------------------------------------------------------

    st.html(
        """
        <section class="dm-hero">

            <div class="dm-hero-copy">

                <div class="dm-eyebrow">
                    WELCOME TO DATAMIND AI
                </div>

                <h1>
                    Your AI-Powered<br>
                    <span>Data Workspace</span>
                </h1>

                <p>
                    Analyze data, build dashboards, get AI insights and
                    make better decisions — all in one intelligent workspace.
                </p>

                <div style="
                    display:flex;
                    flex-wrap:wrap;
                    gap:10px;
                    margin-top:22px;
                ">

                    <div style="
                        padding:8px 13px;
                        border-radius:999px;
                        background:#f5f3ff;
                        border:1px solid #ddd6fe;
                        color:#6d28d9;
                        font-size:12px;
                        font-weight:700;
                    ">
                        AI Analysis
                    </div>

                    <div style="
                        padding:8px 13px;
                        border-radius:999px;
                        background:#eef2ff;
                        border:1px solid #c7d2fe;
                        color:#4338ca;
                        font-size:12px;
                        font-weight:700;
                    ">
                        Smart Dashboards
                    </div>

                    <div style="
                        padding:8px 13px;
                        border-radius:999px;
                        background:#ecfeff;
                        border:1px solid #a5f3fc;
                        color:#0e7490;
                        font-size:12px;
                        font-weight:700;
                    ">
                        PDF Intelligence
                    </div>

                </div>

            </div>

            <div class="dm-hero-visual" aria-hidden="true">

                <div class="dm-orbit dm-orbit-one"></div>
                <div class="dm-orbit dm-orbit-two"></div>

                <div class="dm-db dm-db-top">
                    DATA
                </div>

                <div class="dm-db dm-db-left">
                    SQL
                </div>

                <div class="dm-db dm-db-right">
                    AI
                </div>

                <div class="dm-laptop">

                    <div class="dm-laptop-screen">

                        <div class="dm-chart-bar b1"></div>
                        <div class="dm-chart-bar b2"></div>
                        <div class="dm-chart-bar b3"></div>
                        <div class="dm-chart-bar b4"></div>

                        <div class="dm-chart-line"></div>

                        <div class="dm-screen-panel"></div>

                    </div>

                    <div class="dm-laptop-base"></div>

                </div>

            </div>

        </section>
        """
    )

    # --------------------------------------------------------
    # METRICS / CAPABILITIES
    # --------------------------------------------------------

    st.html(
        """
        <div class="dm-metrics">

            <div class="dm-metric-card">

                <div class="dm-metric-icon">
                    <span class="dm-inline-icon">apps</span>
                </div>

                <div class="dm-metric-value">
                    4
                </div>

                <div class="dm-metric-label">
                    AI-Powered Tools
                </div>

            </div>


            <div class="dm-metric-card">

                <div class="dm-metric-icon">
                    <span class="dm-inline-icon">table_chart</span>
                </div>

                <div class="dm-metric-value">
                    CSV / Excel
                </div>

                <div class="dm-metric-label">
                    Data File Support
                </div>

            </div>


            <div class="dm-metric-card">

                <div class="dm-metric-icon">
                    <span class="dm-inline-icon">auto_awesome</span>
                </div>

                <div class="dm-metric-value">
                    AI Insights
                </div>

                <div class="dm-metric-label">
                    Intelligent Analysis
                </div>

            </div>


            <div class="dm-metric-card">

                <div class="dm-metric-icon">
                    <span class="dm-inline-icon">picture_as_pdf</span>
                </div>

                <div class="dm-metric-value">
                    PDF
                </div>

                <div class="dm-metric-label">
                    Document Intelligence
                </div>

            </div>

        </div>
        """
    )

    # --------------------------------------------------------
    # WORKSPACE SECTION HEADING
    # --------------------------------------------------------
    
    st.html(
        """
        <div class="dm-section-heading">
    
            <h2>
                Explore Your Workspace
            </h2>
    
            <p>
                Choose a tool and start working with your data.
            </p>
    
        </div>
        """
    )
    
    
    
    # --------------------------------------------------------
    # WORKSPACE CARDS
    # --------------------------------------------------------

    cards = [
        (
            "ai_assistant",
            "AI Assistant",
            "Ask questions, get insights and analyze your data using natural language.",
            "#8b5cf6",
            "chat_bubble_outline",
        ),
        (
            "ai_dashboard",
            "AI Dashboard",
            "Create interactive dashboards and transform raw data into visual insights.",
            "#6366f1",
            "analytics",
        ),
        (
            "data_analyst",
            "Data Analyst",
            "Explore datasets, identify patterns and understand your data quickly.",
            "#06b6d4",
            "database",
        ),
        (
            "pdf_intelligence",
            "PDF Intelligence",
            "Extract information, search documents and ask questions from PDFs.",
            "#a855f7",
            "picture_as_pdf",
        ),
    ]

    cols = st.columns(4, gap="medium")

    for col, (key, title, description, accent, icon) in zip(cols, cards):

        with col:

            # Use the actual URL registered by st.Page.
            # The whole visual card is the navigation link.
            page_url = PAGES[key].url_path or ""

            st.html(
                f"""
                <a
                    href="./{page_url}"
                    target="_self"
                    class="dm-workspace-card-link"
                    aria-label="Open {title}"
                >
                    <div
                        class="dm-workspace-card"
                        style="--card-accent:{accent};"
                    >
                        <div class="dm-card-icon">
                            {icon}
                        </div>

                        <h3>
                            {title}
                        </h3>

                        <p>
                            {description}
                        </p>

                        <div class="dm-card-arrow" aria-hidden="true">
                            →
                        </div>
                    </div>
                </a>
                """
            )

    # --------------------------------------------------------
    # HOW DATAMIND AI WORKS
    # --------------------------------------------------------

    st.html(
        """
        <section class="dm-how-section">

            <div class="dm-section-heading" style="margin-bottom:0;">

                <h2>
                    How DataMind AI Works
                </h2>

                <p>
                    Turn your raw information into meaningful insights in three simple steps.
                </p>

            </div>


            <div class="dm-how-grid">

                <div class="dm-how-card">

                    <div class="dm-how-number">
                        01
                    </div>

                    <h3>
                        Upload Your Data
                    </h3>

                    <p>
                        Upload CSV, Excel or PDF files and bring your
                        data into the DataMind AI workspace.
                    </p>

                </div>


                <div class="dm-how-card">

                    <div class="dm-how-number">
                        02
                    </div>

                    <h3>
                        Analyze With AI
                    </h3>

                    <p>
                        Ask questions, explore patterns and use AI-powered
                        analysis to understand your information.
                    </p>

                </div>


                <div class="dm-how-card">

                    <div class="dm-how-number">
                        03
                    </div>

                    <h3>
                        Discover Insights
                    </h3>

                    <p>
                        Build dashboards, generate insights and use the
                        results to make better data-driven decisions.
                    </p>

                </div>

            </div>

        </section>
        """
    )

    # --------------------------------------------------------
    # BOTTOM CTA
    # --------------------------------------------------------

    st.html(
        """
        <div class="dm-bottom-cta">

            <h2>
                Ready to explore your data?
            </h2>

            <p>
                Choose one of the workspace tools above and start analyzing.
            </p>

        </div>
        """
    )

        # --------------------------------------------------------
    # FOUNDER SECTION — LAST HOME CONTENT
    # --------------------------------------------------------

    st.html(
        """
        <section class="dm-founder-section">

            <div class="dm-founder-glow dm-founder-glow-1"></div>
            <div class="dm-founder-glow dm-founder-glow-2"></div>

            <div class="dm-founder-inner">

                <div class="dm-founder-profile">

                    <div class="dm-founder-avatar-ring">
                        <div class="dm-founder-avatar">
                            P
                        </div>
                    </div>

                    <div class="dm-founder-status">
                        <span></span>
                        Building DataMind AI
                    </div>

                </div>

                <div class="dm-founder-info">

                    <div class="dm-founder-eyebrow">
                        <span class="dm-founder-line"></span>
                        MEET THE FOUNDER
                    </div>

                    <h2>
                        Piyush Thakur
                    </h2>

                    <div class="dm-founder-role">
                        Founder & Creator of
                        <span>DataMind AI</span>
                    </div>

                    <p class="dm-founder-bio">
                        Passionate about data, artificial intelligence and
                        building meaningful technology. DataMind AI was created
                        to make data analysis smarter, simpler and accessible
                        to everyone.
                    </p>

                    <div class="dm-founder-tags">

                        <div class="dm-founder-tag">
                            <span class="dm-inline-icon">analytics</span>
                            Data & AI
                        </div>

                        <div class="dm-founder-tag">
                            <span class="dm-inline-icon">code</span>
                            Technology
                        </div>

                        <div class="dm-founder-tag">
                            <span class="dm-inline-icon">lightbulb</span>
                            Innovation
                        </div>

                    </div>

                </div>

            </div>

            <div class="dm-founder-message">
                <span class="dm-quote-mark">“</span>
                Turning ideas into intelligent solutions, one dataset at a time.
                <span class="dm-quote-mark">”</span>
            </div>

        </section>
        """
    )
        # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    st.html(
        """
        <div class="dm-footer">

            <div class="dm-footer-brand">
                <strong>DataMind AI</strong>
                <span>·</span>
                Intelligent Data Analysis Workspace
            </div>

            <div class="dm-footer-tech">
                Built with Python · Streamlit · Gemini AI
            </div>

            <div class="dm-footer-copy">
                © 2026 DataMind AI · Created by Piyush Thakur
            </div>

        </div>

        <div class="dm-home-bottom-space"></div>
        """
    )


    


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():
    if st.session_state.logged_in:
        st.switch_page(PAGES["home"])
        return

    st.html(
        """
        <div class="dm-auth-wrap">
            <div class="dm-auth-card">
                <div class="dm-eyebrow">
                    DATAMIND AI
                </div>
                <h1>
                    Welcome back
                </h1>
                <p>
                    Sign in to continue to your DataMind AI workspace.
                </p>
            </div>
        </div>
        """
    )

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "Email",
            placeholder="you@example.com",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
        )

        submitted = st.form_submit_button(
            "Login",
            type="primary",
            width="stretch",
        )

    if submitted:
        if not email.strip() or not password:
            st.error("Please enter your email and password.")
            return

        if not valid_email(email):
            st.error("Please enter a valid email address.")
            return

        user = authenticate_user(email, password)

        if user:
            set_logged_in(user)
            st.success("Login successful. Welcome back!")
            st.switch_page(PAGES["home"])
        else:
            st.error("Invalid email or password. Please try again.")


# ============================================================
# REGISTER PAGE
# ============================================================

def register_page():
    if st.session_state.logged_in:
        st.switch_page(PAGES["home"])
        return

    st.html(
        """
        <div class="dm-auth-wrap">
            <div class="dm-auth-card">
                <div class="dm-eyebrow">
                    DATAMIND AI
                </div>
                <h1>
                    Create your account
                </h1>
                <p>
                    Register when you are ready. You can keep using
                    the workspace without registering.
                </p>
            </div>
        </div>
        """
    )

    with st.form("register_form", clear_on_submit=False):
        name = st.text_input(
            "Full Name",
            placeholder="Piyush Raj",
        )

        email = st.text_input(
            "Email",
            placeholder="you@example.com",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Minimum 8 characters",
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password",
        )

        submitted = st.form_submit_button(
            "Create Account",
            type="primary",
            width="stretch",
        )

    if submitted:
        clean_name = " ".join(name.strip().split())
        normalized_email = normalize_email(email)

        if not clean_name:
            st.error("Please enter your full name.")
            return

        if len(clean_name) < 2:
            st.error("Please enter a valid name.")
            return

        if not normalized_email:
            st.error("Please enter your email address.")
            return

        if not valid_email(normalized_email):
            st.error("Please enter a valid email address.")
            return

        if len(password) < 8:
            st.error("Password must be at least 8 characters long.")
            return

        if password != confirm_password:
            st.error("Passwords do not match.")
            return

        if get_user_by_email(normalized_email):
            st.error(
                "An account with this email already exists. "
                "Please use Login instead."
            )
            return

        user = create_user(
            clean_name,
            normalized_email,
            password,
        )

        if user:
            set_logged_in(user)
            st.success(
                "Account created successfully. "
                "Welcome to DataMind AI!"
            )
            st.switch_page(PAGES["home"])
        else:
            st.error(
                "This email is already registered. "
                "Please use Login instead."
            )


# ============================================================
# SETTINGS PAGE
# ============================================================

def settings_page():

    st.html(
        """
        <div class="dm-page-heading">

            <div class="dm-eyebrow">
                DATAMIND AI
            </div>

            <h1>
                Settings
            </h1>

            <p>
                Manage your workspace preferences.
            </p>

        </div>
        """
    )

    st.toggle(
        "Remember my workspace preferences",
        value=True,
    )

    st.selectbox(
        "Default workspace",
        [
            "AI Assistant",
            "AI Dashboard",
            "Data Analyst",
            "PDF Intelligence",
        ],
    )

    st.selectbox(
        "Interface density",
        [
            "Comfortable",
            "Compact",
        ],
    )


# ============================================================
# HELP PAGE
# ============================================================

def help_page():

    st.html(
        """
        <div class="dm-page-heading">

            <div class="dm-eyebrow">
                DATAMIND AI
            </div>

            <h1>
                Help & Support
            </h1>

            <p>
                Find guidance for using the DataMind AI workspace.
            </p>

        </div>
        """
    )

    with st.expander(
        "How do I upload data?",
        expanded=True,
    ):

        st.write(
            "Open Data Analyst or AI Dashboard and upload a CSV or Excel file."
        )

    with st.expander(
        "How do I use the AI Assistant?"
    ):

        st.write(
            "Open AI Assistant, optionally upload a dataset, "
            "and ask your question in natural language."
        )

    with st.expander(
        "How does PDF Intelligence work?"
    ):

        st.write(
            "Upload a PDF, let DataMind AI index it, "
            "then search or ask questions about the document."
        )


# ============================================================
# NAVIGATION
# ============================================================

PAGES.update({

    # IMPORTANT:
    # No url_path is specified for Home so that Home becomes
    # the root/default page.

    "home": st.Page(
        home_page,
        title="Home",
        icon=":material/home:",
        default=True,
    ),

    "ai_assistant": st.Page(
        "pages/ai_assistant.py",
        title="AI Assistant",
        icon=":material/chat_bubble_outline:",
        url_path="ai-assistant",
    ),

    "ai_dashboard": st.Page(
        "pages/ai_dashboard.py",
        title="AI Dashboard",
        icon=":material/analytics:",
        url_path="ai-dashboard",
    ),

    "data_analyst": st.Page(
        "pages/data_analyst.py",
        title="Data Analyst",
        icon=":material/database:",
        url_path="data-analyst",
    ),

    "pdf_intelligence": st.Page(
        "pages/pdf_intelligence.py",
        title="PDF Intelligence",
        icon=":material/picture_as_pdf:",
        url_path="pdf-intelligence",
    ),

    "settings": st.Page(
        settings_page,
        title="Settings",
        icon=":material/settings:",
        url_path="settings",
    ),

    "help": st.Page(
        help_page,
        title="Help & Support",
        icon=":material/help_outline:",
        url_path="help-support",
    ),

    "login": st.Page(
        login_page,
        title="Login",
        icon=":material/login:",
        url_path="login",
    ),

    "register": st.Page(
        register_page,
        title="Register",
        icon=":material/person_add:",
        url_path="register",
    ),
})


# ============================================================
# HIDDEN NATIVE NAVIGATION
# ============================================================

pg = st.navigation(
    list(PAGES.values()),
    position="hidden",
)


# ============================================================
# SHARED SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    st.html(
        """
        <div class="dm-brand">

            <div class="dm-brand-mark">
                D
            </div>

            <div>

                <div class="dm-brand-name">
                    DataMind AI
                </div>

                <div class="dm-brand-tagline">
                    Turn Your Data Into Insights
                </div>

            </div>

        </div>
        """
    )

    st.markdown(
        '<div class="dm-sidebar-divider"></div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # MAIN NAVIGATION
    # --------------------------------------------------------

    st.page_link(
        PAGES["home"],
        label="Home",
        icon=":material/home:",
        width="stretch",
    )

    st.page_link(
        PAGES["ai_assistant"],
        label="AI Assistant",
        icon=":material/chat_bubble_outline:",
        width="stretch",
    )

    st.page_link(
        PAGES["ai_dashboard"],
        label="AI Dashboard",
        icon=":material/analytics:",
        width="stretch",
    )

    st.page_link(
        PAGES["data_analyst"],
        label="Data Analyst",
        icon=":material/database:",
        width="stretch",
    )

    st.page_link(
        PAGES["pdf_intelligence"],
        label="PDF Intelligence",
        icon=":material/picture_as_pdf:",
        width="stretch",
    )

    # --------------------------------------------------------
    # SECONDARY NAVIGATION
    # --------------------------------------------------------

    st.markdown(
        '<div class="dm-sidebar-divider dm-sidebar-divider-lower"></div>',
        unsafe_allow_html=True,
    )

    st.page_link(
        PAGES["settings"],
        label="Settings",
        icon=":material/settings:",
        width="stretch",
    )

    st.page_link(
        PAGES["help"],
        label="Help & Support",
        icon=":material/help_outline:",
        width="stretch",
    )

    # --------------------------------------------------------
    # ACCOUNT
    # --------------------------------------------------------

    st.markdown(
        '<div class="dm-sidebar-divider dm-sidebar-divider-lower"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="dm-auth-links-title">ACCOUNT</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.logged_in:
        safe_name = html.escape(st.session_state.user_name or "User")
        safe_email = html.escape(st.session_state.user_email or "")
        initials = html.escape(get_initials(st.session_state.user_name or "User"))

        st.html(
            f"""
            <div class="dm-profile">
                <div class="dm-avatar">{initials}</div>
                <div class="dm-profile-text">
                    <div class="dm-profile-name">{safe_name}</div>
                    <div class="dm-profile-email">{safe_email}</div>
                </div>
            </div>
            """
        )

        if st.button(
            "Log Out",
            key="logout_button",
            width="stretch",
        ):
            logout_user()

    else:
        st.html(
            """
            <div class="dm-guest">
                <div class="dm-avatar dm-avatar-guest">GU</div>
                <div class="dm-profile-text">
                    <div class="dm-profile-name">Guest</div>
                    <div class="dm-profile-email">Not signed in</div>
                </div>
            </div>
            """
        )

        auth_cols = st.columns(2, gap="small")

        with auth_cols[0]:
            st.page_link(
                PAGES["login"],
                label="Login",
                icon=":material/login:",
                width="stretch",
            )

        with auth_cols[1]:
            st.page_link(
                PAGES["register"],
                label="Register",
                icon=":material/person_add:",
                width="stretch",
            )



# ============================================================
# RUN CURRENT PAGE
# ============================================================

pg.run()
