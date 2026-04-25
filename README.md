# Aurus Jewels — End-to-End E-Commerce Platform with Business Analytics Dashboard

> **Fine hallmarked jewellery, priced live from the official IBJA gold rate.**  
> Every product price is calculated in real time — metal value + making charges + GST — no fixed tags, no manual updates.

---

## Overview

Aurus Jewels is a full-stack e-commerce platform built for India's fine jewellery market. The platform's core innovation is its **live pricing engine**: every product's price is dynamically calculated from the daily IBJA (India Bullion and Jewellers Association) gold rate, fetched automatically each morning. Customers see a complete, transparent price breakdown — metal value, making charges, and GST — on every product page.


---

## Features

### Customer Storefront
- **Home** — Hero slider, live gold rate ticker, featured products, loyalty tiers, category grid
- **Catalogue** — Filter by category, metal, karat; sort by price/featured; pagination
- **Product Detail** — CSS-only image gallery, full live price breakdown (metal + making + GST)
- **Cart** — Quantity controls, promo codes, loyalty discount, stock validation
- **Wishlist** — Save items, move to cart, price-drop indicator
- **Checkout** — Address management, COD/UPI payment, order confirmation
- **Profile** — Order history, address book, loyalty tier progress, account settings

### Admin Panel
- **Dashboard** — Live KPI cards, low-stock alerts, recent orders
- **Products** — Full CRUD with image management, activate/deactivate
- **Orders** — Status management (pending → confirmed → shipped → delivered)
- **Gold Rates** — Live IBJA display, manual override
- **Analytics** — 8 interactive Plotly charts: seasonal demand, gold rate trends, revenue correlation, category performance, loyalty distribution

### Data & Automation
- Daily IBJA rate fetch via APScheduler (9 AM IST) with multi-source fallback
- GST-compliant PDF invoice generation (ReportLab) with CGST + SGST breakdown
- Automated email dispatch with invoice attached (SMTP/Gmail)
- JWT authentication with browser cookie persistence across page navigations
- 4-tier loyalty programme (Member → Silver → Gold → Platinum)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend + Routing | Python + Streamlit |
| Backend Logic | Python (core/ modules) |
| Database | MySQL 8.0 |
| Authentication | JWT (PyJWT) + bcrypt |
| Session Persistence | extra-streamlit-components (cookies) |
| Charts | Plotly |
| PDF Generation | ReportLab |
| Email | smtplib (SMTP/Gmail) |
| Rate Scheduling | APScheduler |
| Rate Scraping | Requests + BeautifulSoup |
| DB Connector | mysql-connector-python |

---

## Project Structure

```
AurusJewels/
├── Home.py                    # Entry point
├── config.py                  # All config loaded from .env
├── .env                       # Credentials (not in repo)
├── pages/
│   ├── Catalogue.py
│   ├── Product.py
│   ├── Cart.py
│   ├── Wishlist.py
│   ├── Checkout.py
│   ├── Profile.py
│   ├── Login.py
│   └── Admin.py
├── core/
│   ├── pricing_engine.py      # Live price calculation
│   ├── rate_fetcher.py        # IBJA scraper + fallback
│   ├── scheduler.py           # APScheduler 9AM daily
│   ├── auth.py                # bcrypt + JWT
│   ├── session.py             # Cookie-based session
│   ├── invoice.py             # ReportLab PDF generation
│   ├── mailer.py              # SMTP email dispatch
│   └── styles.py              # Shared CSS
├── database/
│   └── db.py                  # MySQL connection pool
├── static/
│   └── images/                # Product + hero images
└── invoices/                  # Generated PDF invoices (gitignored)
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- MySQL 8.0
- Gmail account with App Password enabled

### 1. Clone the repository
```bash
git clone https://github.com/your-username/AurusJewels.git
cd AurusJewels
```

### 2. Install dependencies
```bash
pip install streamlit mysql-connector-python pandas plotly PyJWT bcrypt \
            reportlab APScheduler requests beautifulsoup4 \
            extra-streamlit-components python-dotenv
```

### 3. Configure environment
Create a `.env` file in the project root:
```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=AurusJewels

# JWT
JWT_SECRET=your-secret-key
JWT_EXPIRY_DAYS=7

# SMTP (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_gmail@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx

# Business
SMTP_FROM_NAME=Aurus Jewels
```

> **Gmail App Password**: Go to Google Account → Security → 2-Step Verification → App Passwords. Generate one for "Mail" and use it as `SMTP_PASS`.

### 4. Set up the database
```bash
mysql -u root -p -e "CREATE DATABASE AurusJewels;"
mysql -u root -p AurusJewels < schema.sql
mysql -u root -p AurusJewels < dummy_orders.sql
```

### 5. Run
```bash
python -m streamlit run Home.py
```

Open `http://localhost:8501`

---

## Live Pricing Formula

Every product price is calculated fresh on every page load:

```
Rate        = IBJA gold rate for the day (per gram, for 22K/18K/925)
Metal Value = Weight (g) × Rate
Making      = Metal Value × Making %
Pre-GST     = Metal Value + Making
GST (5%)    = Pre-GST × 0.05
Final Price = Pre-GST + GST
              split as CGST 2.5% + SGST 2.5%
```

---

## Analytics Highlights

The Admin Analytics dashboard reveals insights about the Indian jewellery market:

- **Seasonal demand**: Sales peak during Dhanteras, Diwali, and the wedding season (Oct–Feb), accounting for ~68% of annual revenue
- **Gold rate correlation**: Demand is **event-driven, not price-sensitive** — sales peak even when gold rates are at annual highs
- **Category performance**: Chains and Bracelets (higher weight) lead revenue; Bracelets command highest making charges (margin)
- **Day-of-week**: Saturday and Sunday see highest order volumes

---

## Key Engineering Decisions

| Challenge | Solution |
|---|---|
| Streamlit strips JavaScript | All interactions via CSS tricks + href query params |
| Session lost on page navigation | JWT stored in browser cookie via extra-streamlit-components |
| Links open in new tab (iframe) | `<base target="_parent">` in separate `st.markdown()` call |
| MySQL `only_full_group_by` | GROUP BY uses exact same expression as SELECT |
| Admin tab resets on action | Custom HTML tab bar + `session_state["admin_section"]` |
| IBJA scraper fails silently | Multi-source fallback + DB carry-forward of last known rate |
| PDF rupee symbol shows as box | Helvetica has no ₹ glyph — replaced with `Rs.` formatter |

---

## Database Schema

12 tables following a dimensional model:

| Table | Type | Description |
|---|---|---|
| dim_products | Dimension | 48 SKUs with weight, making%, karat |
| dim_categories | Dimension | 5 categories |
| dim_customers | Dimension | Customers with loyalty tier |
| dim_addresses | Dimension | Delivery addresses |
| dim_gold_rates | Fact/Dim | Daily IBJA rate time series |
| customer_cart | Fact | Active cart items |
| customer_wishlist | Fact | Saved items |
| fact_orders | Fact | Orders with gold rate snapshot |
| fact_order_items | Fact | Line items with full price breakdown |
| stock_log | Fact | Stock movement log |
| email_log | Fact | Email dispatch log |

---

## .gitignore

```
.env
invoices/
__pycache__/
*.pyc
.streamlit/secrets.toml
fix_base_tag.py
fix_invoice.py
fix_invoice_display.py
test_invoice.py
```

---

## License

This project was developed as part of an academic internship. All rights reserved.