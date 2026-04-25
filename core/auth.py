"""
core/auth.py — Authentication for Aurus Jewels.
Supports Google OAuth + Email/Password login.
"""
import bcrypt
import jwt
import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from database.db import execute_one, execute_write


# ── Password helpers ─────────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── JWT helpers ──────────────────────────────────────────────
def generate_token(customer: dict) -> str:
    payload = {
        "customer_id": customer["customer_id"],
        "email":       customer["email"],
        "role":        customer["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(
            days=config.JWT_EXPIRY_DAYS
        ),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None


# ── Email / Password login ───────────────────────────────────
def login_customer(email: str, password: str) -> tuple:
    """Returns (customer_dict, error_message)."""
    if not email or not password:
        return None, "Please enter email and password."
    row = execute_one(
        "SELECT * FROM dim_customers WHERE email=%s AND is_active=1",
        (email.strip().lower(),)
    )
    if not row:
        return None, "No account found with this email."
    if not row["password_hash"]:
        return None, "This account uses Google Sign-In. Please use Google login."
    if not verify_password(password, row["password_hash"]):
        return None, "Incorrect password."
    return row, ""


# ── Email / Password register ────────────────────────────────
def register_customer(
    full_name: str, email: str, phone: str, password: str
) -> tuple:
    """Returns (customer_dict, error_message)."""
    if len(full_name.strip()) < 2:
        return None, "Please enter your full name."
    if "@" not in email or "." not in email:
        return None, "Please enter a valid email address."
    if len(password) < 8:
        return None, "Password must be at least 8 characters."

    existing = execute_one(
        "SELECT customer_id FROM dim_customers WHERE email=%s",
        (email.strip().lower(),)
    )
    if existing:
        return None, "An account with this email already exists."

    hashed = hash_password(password)
    new_id = execute_write(
        """INSERT INTO dim_customers
             (full_name, email, phone, password_hash)
           VALUES (%s, %s, %s, %s)""",
        (full_name.strip(), email.strip().lower(), phone.strip(), hashed)
    )
    if not new_id:
        return None, "Registration failed. Please try again."

    customer = execute_one(
        "SELECT * FROM dim_customers WHERE customer_id=%s", (new_id,)
    )
    return customer, ""


# ── Google OAuth login / register ────────────────────────────
def google_login_or_register(google_user: dict) -> tuple:
    """
    Called after successful Google OAuth.
    google_user dict contains: email, name, picture (from Google)
    Returns (customer_dict, error_message).
    """
    email = google_user.get("email", "").strip().lower()
    name  = google_user.get("name", "").strip()

    if not email:
        return None, "Could not retrieve email from Google."

    # Check if customer already exists
    existing = execute_one(
        "SELECT * FROM dim_customers WHERE email=%s AND is_active=1",
        (email,)
    )
    if existing:
        return existing, ""

    # New customer — register automatically
    new_id = execute_write(
        """INSERT INTO dim_customers
             (full_name, email, password_hash)
           VALUES (%s, %s, %s)""",
        (name, email, "")   # empty password_hash = Google-only account
    )
    if not new_id:
        return None, "Failed to create account. Please try again."

    customer = execute_one(
        "SELECT * FROM dim_customers WHERE customer_id=%s", (new_id,)
    )
    return customer, ""


# ── Loyalty tier updater ─────────────────────────────────────
def update_loyalty_tier(customer_id: int) -> str:
    """Recalculate loyalty tier from total_spend and update DB."""
    row = execute_one(
        "SELECT total_spend FROM dim_customers WHERE customer_id=%s",
        (customer_id,)
    )
    if not row:
        return "member"

    spend = float(row["total_spend"] or 0)

    if spend >= config.TIER_PLATINUM:
        tier = "platinum"
    elif spend >= config.TIER_GOLD:
        tier = "gold"
    elif spend >= config.TIER_SILVER:
        tier = "silver"
    else:
        tier = "member"

    execute_write(
        "UPDATE dim_customers SET loyalty_tier=%s WHERE customer_id=%s",
        (tier, customer_id)
    )
    return tier