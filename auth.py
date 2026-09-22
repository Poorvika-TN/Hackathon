import os
import random
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash


# =========================================================
# EMAIL CONFIGURATION
# =========================================================

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


# =========================================================
# PASSWORD FUNCTIONS
# =========================================================

def hash_password(password):

    return generate_password_hash(password)


def verify_password(password, password_hash):

    return check_password_hash(
        password_hash,
        password
    )


# =========================================================
# OTP GENERATION
# =========================================================

def generate_otp():

    return str(
        random.randint(
            100000,
            999999
        )
    )


# =========================================================
# OTP EXPIRY
# =========================================================

def otp_expiry():

    return datetime.now() + timedelta(
        minutes=5
    )


# =========================================================
# SEND OTP EMAIL
# =========================================================

def send_otp_email(receiver_email, otp):

    # If email credentials are not configured,
    # print OTP in terminal for testing.

    if not SMTP_EMAIL or not SMTP_PASSWORD:

        print(
            "\n================================"
        )

        print(
            "OTP FOR DEMO:",
            otp
        )

        print(
            "================================\n"
        )

        return True


    message = EmailMessage()

    message["Subject"] = (
        "Your AI Scheduler Login OTP"
    )

    message["From"] = SMTP_EMAIL

    message["To"] = receiver_email

    message.set_content(
        f"""
Hello,

Your OTP for the Carbon-Aware AI Scheduler login is:

{otp}

This OTP is valid for 5 minutes.

If you did not request this OTP,
please ignore this email.

Thank you.
"""
    )


    try:

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT
        ) as server:

            server.starttls()

            server.login(
                SMTP_EMAIL,
                SMTP_PASSWORD
            )

            server.send_message(
                message
            )

        return True


    except Exception as error:

        print(
            "Email error:",
            error
        )

        return False