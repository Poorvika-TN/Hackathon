import sqlite3
from datetime import datetime

DB_NAME = "offline_events.db"


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = sqlite3.connect(DB_NAME)

    # -----------------------------------------------------
    # OFFLINE EVENTS TABLE
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS offline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            task TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        )
    """)

    # -----------------------------------------------------
    # USERS TABLE
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # OTP TABLE
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# USER FUNCTIONS
# =========================================================

def create_user(
    email,
    password_hash
):

    conn = sqlite3.connect(DB_NAME)

    try:

        conn.execute("""
            INSERT INTO users
            (email, password_hash, created_at)
            VALUES (?, ?, ?)
        """, (
            email,
            password_hash,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


def get_user(email):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute("""
        SELECT id, email, password_hash
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    conn.close()

    return user


# =========================================================
# OTP FUNCTIONS
# =========================================================

def save_otp(
    email,
    otp,
    expires_at
):

    conn = sqlite3.connect(DB_NAME)

    # Remove previous OTPs
    conn.execute("""
        DELETE FROM otp_codes
        WHERE email = ?
    """, (email,))

    conn.execute("""
        INSERT INTO otp_codes
        (email, otp, expires_at, verified, created_at)
        VALUES (?, ?, ?, 0, ?)
    """, (
        email,
        otp,
        expires_at.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    conn.commit()
    conn.close()


def verify_otp(
    email,
    otp
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute("""
        SELECT id, otp, expires_at
        FROM otp_codes
        WHERE email = ?
        AND verified = 0
        ORDER BY id DESC
        LIMIT 1
    """, (email,))

    record = cursor.fetchone()

    if not record:

        conn.close()

        return False, "OTP not found."


    otp_id = record[0]

    stored_otp = record[1]

    expires_at = datetime.strptime(
        record[2],
        "%Y-%m-%d %H:%M:%S"
    )


    # Check OTP
    if stored_otp != otp:

        conn.close()

        return False, "Invalid OTP."


    # Check expiry
    if datetime.now() > expires_at:

        conn.close()

        return False, "OTP has expired."


    # Mark OTP verified
    conn.execute("""
        UPDATE otp_codes
        SET verified = 1
        WHERE id = ?
    """, (otp_id,))

    conn.commit()
    conn.close()

    return True, "OTP verified successfully."


# =========================================================
# OFFLINE EVENT STORAGE
# =========================================================

def add_event(
    event_type,
    task,
    status
):

    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        INSERT INTO offline_events
        (event_type, task, status, created_at, synced)
        VALUES (?, ?, ?, ?, 0)
    """, (
        event_type,
        task,
        status,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    conn.commit()
    conn.close()


# =========================================================
# GET UNSYNCED EVENTS
# =========================================================

def get_unsynced_events():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute("""
        SELECT id,
               event_type,
               task,
               status,
               created_at
        FROM offline_events
        WHERE synced = 0
        ORDER BY id
    """)

    events = cursor.fetchall()

    conn.close()

    return events


# =========================================================
# MARK EVENTS AS SYNCED
# =========================================================

def mark_all_synced():

    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        UPDATE offline_events
        SET synced = 1
        WHERE synced = 0
    """)

    conn.commit()
    conn.close()


# =========================================================
# COUNT UNSYNCED EVENTS
# =========================================================

def count_unsynced():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute("""
        SELECT COUNT(*)
        FROM offline_events
        WHERE synced = 0
    """)

    count = cursor.fetchone()[0]

    conn.close()

    return count