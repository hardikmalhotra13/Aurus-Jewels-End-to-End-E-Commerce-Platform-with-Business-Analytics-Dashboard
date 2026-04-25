"""
config.py — Loads all configuration from .env for Aurus Jewels
"""
import os
from dotenv import load_dotenv

# Force load .env from the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ── Database ────────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", 3306))
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "hardik1305")
DB_NAME     = os.getenv("DB_NAME", "AurusJewels")

# ── JWT ─────────────────────────────────────────────────────
JWT_SECRET      = os.getenv("JWT_SECRET", "aurusjewels-dev-secret")
JWT_EXPIRY_DAYS = int(os.getenv("JWT_EXPIRY_DAYS", 7))

# ── SMTP ────────────────────────────────────────────────────
SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", 587))
SMTP_USER      = os.getenv("SMTP_USER", "")
SMTP_PASS      = os.getenv("SMTP_PASS", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Aurus Jewels")

# ── Loyalty Tier Thresholds (INR) ───────────────────────────
TIER_SILVER   = float(os.getenv("TIER_SILVER",   50000))
TIER_GOLD     = float(os.getenv("TIER_GOLD",    150000))
TIER_PLATINUM = float(os.getenv("TIER_PLATINUM", 500000))

# ── Loyalty Discounts ───────────────────────────────────────
LOYALTY_DISC = {
    "member":   0.00,
    "silver":   0.03,
    "gold":     0.05,
    "platinum": 0.05,
}

# ── Business Info ───────────────────────────────────────────
GSTIN         = "07AABCS1429B1Z6"
BUSINESS_NAME = "Aurus Jewels"
BUSINESS_ADDR = "New Delhi, India — 110001"

# ── Invoice Storage ─────────────────────────────────────────
INVOICE_DIR = os.path.join(BASE_DIR, "invoices")
os.makedirs(INVOICE_DIR, exist_ok=True)



# ── Google OAuth ─────────────────────────────────────────────
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")