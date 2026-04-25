"""
pages/Checkout.py — Aurus Jewels Checkout Page
Flow: Cart Review → Address → Payment → Confirmation
"""
import streamlit as st
import sys, os
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.session        import init_session, require_login
from core.pricing_engine import get_all_rates, format_inr
# Safe imports — these are optional; checkout works even if they fail
try:
    from core.invoice import generate_invoice_pdf, generate_invoice_number, save_invoice_path
    INVOICE_OK = True
except ImportError:
    INVOICE_OK = False

try:
    from core.mailer import send_invoice_email
    MAILER_OK = True
except ImportError:
    MAILER_OK = False
from database.db         import execute_query, execute_write, execute_one

st.set_page_config(
    page_title            = "Checkout — Aurus Jewels",
    page_icon             = "✦",
    layout                = "wide",
    initial_sidebar_state = "collapsed",
)

init_session()
require_login()

cid       = st.session_state.get("customer_id")
full_name = st.session_state.get("full_name", "")
email     = st.session_state.get("email", "")
role      = st.session_state.get("role", "customer")
tier      = st.session_state.get("loyalty_tier", "member")

# ── Navigation handler ────────────────────────────────────────
PAGE_MAP = {
    "Home"     : "Home.py",
    "Catalogue": "pages/Catalogue.py",
    "Product"  : "pages/Product.py",
    "Cart"     : "pages/Cart.py",
    "Checkout" : "pages/Checkout.py",
    "Profile"  : "pages/Profile.py",
    "Login"    : "pages/Login.py",
    "Admin"    : "pages/Admin.py",
    "Wishlist" : "pages/Wishlist.py",
}
_nav = st.query_params.get("_nav", "")
if _nav and _nav in PAGE_MAP:
    st.query_params.clear()
    st.switch_page(PAGE_MAP[_nav])

# ── Session state defaults ────────────────────────────────────
for k, v in [
    ("checkout_step",       "checkout"),   # "checkout" | "confirmed"
    ("selected_address_id", None),
    ("payment_method",      "cod"),
    ("upi_id",              ""),
    ("show_add_addr",       False),
    ("placed_order_id",     None),
    ("invoice_path",        None),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Action handlers ───────────────────────────────────────────
action = st.query_params.get("action", "")
act_id = st.query_params.get("id", "")

if action == "select_address" and act_id:
    st.session_state["selected_address_id"] = int(act_id)
    st.query_params.clear(); st.rerun()

if action == "select_payment":
    method = st.query_params.get("method", "cod")
    st.session_state["payment_method"] = method
    st.query_params.clear(); st.rerun()

if action == "delete_address" and act_id:
    execute_write(
        "DELETE FROM dim_addresses WHERE address_id=%s AND customer_id=%s",
        (act_id, cid)
    )
    if str(st.session_state.get("selected_address_id")) == act_id:
        st.session_state["selected_address_id"] = None
    st.query_params.clear(); st.rerun()

if action == "show_add_addr":
    st.session_state["show_add_addr"] = True
    st.query_params.clear(); st.rerun()

# ── Live rates ────────────────────────────────────────────────
rates = get_all_rates()
r22k  = rates.get(("gold",   "22K"), 6850.0)
r18k  = rates.get(("gold",   "18K"), 5600.0)
r925  = rates.get(("silver", "925"),   85.0)

def get_rate(metal_type, karat):
    return float(rates.get((metal_type, karat), 6850.0))

def calc_price(weight_g, making_pct, metal_type, karat):
    rate      = get_rate(metal_type, karat)
    metal_val = float(weight_g) * rate
    making    = metal_val * float(making_pct)
    pre_gst   = metal_val + making
    return {
        "rate"       : rate,
        "metal_value": round(metal_val, 2),
        "making"     : round(making, 2),
        "pre_gst"    : round(pre_gst, 2),
        "gst"        : round(pre_gst * 0.05, 2),
        "cgst"       : round(pre_gst * 0.025, 2),
        "sgst"       : round(pre_gst * 0.025, 2),
        "total"      : round(pre_gst * 1.05, 2),
    }

# ── Loyalty discount rates ────────────────────────────────────
LOYALTY_DISC = {"member": 0.0, "silver": 0.03, "gold": 0.05, "platinum": 0.05}
loyalty_pct  = LOYALTY_DISC.get(tier, 0.0)

# ── Cart items ────────────────────────────────────────────────
cart_items = execute_query(
    "SELECT ca.cart_id, ca.quantity, p.product_id, p.name, p.sku, "
    "p.metal_type, p.karat, p.weight_g, p.making_pct, "
    "p.image_main, c.name AS category_name "
    "FROM customer_cart ca "
    "JOIN dim_products p ON ca.product_id=p.product_id "
    "JOIN dim_categories c ON p.category_id=c.category_id "
    "WHERE ca.customer_id=%s AND p.is_active=1",
    (cid,)
) or []

if not cart_items and st.session_state["checkout_step"] == "checkout":
    st.switch_page("pages/Cart.py")

# ── Pricing calculation ───────────────────────────────────────
for item in cart_items:
    p = calc_price(item["weight_g"], item["making_pct"],
                   item["metal_type"], item["karat"])
    item["unit_price"] = p["total"]
    item["line_total"] = round(p["total"] * int(item["quantity"]), 2)
    item["pricing"]    = p

subtotal       = sum(i["line_total"] for i in cart_items)
loyalty_disc   = round(subtotal * loyalty_pct, 2)
final_total    = round(subtotal - loyalty_disc, 2)
gst_total      = round(sum(
    i["pricing"]["gst"] * int(i["quantity"]) for i in cart_items
), 2)
cgst_total     = round(gst_total / 2, 2)
sgst_total     = round(gst_total / 2, 2)
item_count     = sum(int(i["quantity"]) for i in cart_items)

# ── Addresses ─────────────────────────────────────────────────
addresses = execute_query(
    "SELECT * FROM dim_addresses WHERE customer_id=%s ORDER BY is_default DESC, address_id DESC",
    (cid,)
) or []

# Auto-select default address if none selected
if st.session_state["selected_address_id"] is None and addresses:
    default = next((a for a in addresses if a["is_default"]), addresses[0])
    st.session_state["selected_address_id"] = int(default["address_id"])

# ── Counts for navbar ─────────────────────────────────────────
cart_count = len(cart_items)
wish_row   = execute_one("SELECT COUNT(*) AS c FROM customer_wishlist WHERE customer_id=%s", (cid,))
wish_count = int(wish_row["c"]) if wish_row else 0

# ── Image helper ──────────────────────────────────────────────
def img_url(path):
    if not path: return ""
    return path.replace("\\", "/").replace("static/", "/app/static/")

# ── Place order function ──────────────────────────────────────
def place_order():
    addr_id = st.session_state["selected_address_id"]
    method  = st.session_state["payment_method"]
    if not addr_id:
        return None, "Please select a delivery address."

    addr = execute_one("SELECT * FROM dim_addresses WHERE address_id=%s", (addr_id,))
    if not addr:
        return None, "Invalid address."

    # Insert order first (no invoice number yet — generated after we have order_id)
    order_id = execute_write(
        """INSERT INTO fact_orders
           (customer_id, shipping_address_id, order_status, subtotal,
            cgst_amount, sgst_amount, total_amount, loyalty_discount,
            gold_rate_22k, gold_rate_18k, silver_rate_925,
            created_at)
           VALUES (%s,%s,'confirmed',%s,%s,%s,%s,%s,%s,%s,%s,NOW())""",
        (cid, addr_id,
         round(subtotal - loyalty_disc + gst_total, 2) - loyalty_disc,
         cgst_total, sgst_total, final_total,
         loyalty_disc, r22k, r18k, r925)
    )
    if not order_id:
        return None, "Failed to place order. Please try again."

    # Generate invoice number using order_id (always unique)
    inv_no = "AJ" + datetime.now().strftime("%Y%m") + "-" + str(order_id).zfill(5)
    execute_write(
        "UPDATE fact_orders SET invoice_number=%s WHERE order_id=%s",
        (inv_no, order_id)
    )

    # Insert order items
    for item in cart_items:
        p   = item["pricing"]
        qty = int(item["quantity"])
        execute_write(
            """INSERT INTO fact_order_items
               (order_id, product_id, product_name, karat, metal_type,
                weight_g, quantity, gold_rate_used, metal_value,
                making_charge, pre_gst_amount, gst_amount,
                unit_price, line_total)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (order_id, item["product_id"], item["name"],
             item["karat"], item["metal_type"],
             float(item["weight_g"]), qty,
             p["rate"], p["metal_value"] * qty,
             p["making"] * qty, p["pre_gst"] * qty,
             p["gst"] * qty, item["unit_price"],
             item["line_total"])
        )
        # Deduct stock
        execute_write(
            "UPDATE dim_products SET stock_qty=GREATEST(0,stock_qty-%s) "
            "WHERE product_id=%s",
            (qty, item["product_id"])
        )
        # Stock log
        execute_write(
            "INSERT INTO stock_log (product_id, change_qty, reason) "
            "VALUES (%s,%s,'sale')",
            (item["product_id"], -qty)
        )

    # Update customer loyalty
    execute_write(
        "UPDATE dim_customers SET total_spend=total_spend+%s WHERE customer_id=%s",
        (final_total, cid)
    )
    new_spend = execute_one(
        "SELECT total_spend FROM dim_customers WHERE customer_id=%s", (cid,)
    )
    if new_spend:
        sp = float(new_spend["total_spend"])
        new_tier = "member"
        if sp >= 500000: new_tier = "platinum"
        elif sp >= 150000: new_tier = "gold"
        elif sp >= 50000: new_tier = "silver"
        execute_write(
            "UPDATE dim_customers SET loyalty_tier=%s WHERE customer_id=%s",
            (new_tier, cid)
        )
        st.session_state["loyalty_tier"] = new_tier

    # Clear cart
    execute_write(
        "DELETE FROM customer_cart WHERE customer_id=%s", (cid,)
    )

    # Generate PDF invoice
    inv_path = None
    inv_error = None
    try:
        if INVOICE_OK:
            order_data    = execute_one("SELECT * FROM fact_orders WHERE order_id=%s", (order_id,))
            items_data    = execute_query("SELECT * FROM fact_order_items WHERE order_id=%s", (order_id,))
            customer_data = execute_one("SELECT * FROM dim_customers WHERE customer_id=%s", (cid,))
            inv_path = generate_invoice_pdf(order_data, items_data, customer_data, addr)
            if inv_path and os.path.exists(inv_path):
                execute_write(
                    "UPDATE fact_orders SET invoice_path=%s WHERE order_id=%s",
                    (inv_path, order_id)
                )
            else:
                inv_path = None
    except Exception as e:
        inv_error = str(e)
        inv_path = None

    # Send confirmation email with invoice attached
    try:
        if MAILER_OK:
            send_invoice_email(
                to_email       = email,
                customer_name  = full_name,
                order_id       = order_id,
                invoice_number = inv_no,
                invoice_path   = inv_path
            )
    except Exception:
        pass  # Email failure never blocks order

    return order_id, None

# ════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════
st.markdown('<base target="_parent">', unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

#MainMenu,footer,header{display:none!important;}
.stApp{background:#FFFDF9!important;}
[data-testid="stAppViewContainer"]>.main{padding:0!important;}
[data-testid="stHeader"]{display:none!important;}
section[data-testid="stSidebar"]{display:none!important;}
.block-container{padding:0!important;max-width:100%!important;}
.element-container{margin:0!important;}
div[data-testid="stVerticalBlock"]>div{gap:0!important;}
*{box-sizing:border-box;}
a{text-decoration:none!important;}

/* ── Streamlit column split ──────────────────────────────── */
[data-testid="stHorizontalBlock"]{gap:0!important;align-items:flex-start!important;}
[data-testid="stHorizontalBlock"]>div{padding:0!important;}
[data-testid="stHorizontalBlock"]>div:first-child{
  border-right:1px solid #EDD9A3;background:#FFFDF9;
  padding:26px 32px 36px!important;min-height:60vh;
}
[data-testid="stHorizontalBlock"]>div:last-child{
  background:#FFF8EE;
  padding:26px 28px 36px!important;
}

/* ── NAVBAR ──────────────────────────────────────────────── */
.aj-nav{position:sticky;top:0;z-index:999;background:#FFFDF7;border-bottom:1.5px solid #E8D5A3;box-shadow:0 2px 20px rgba(184,134,11,.1);padding:0 5%;height:56px;display:flex;align-items:center;justify-content:space-between;}
.aj-logo{display:flex;flex-direction:column;align-items:flex-start;gap:2px;text-decoration:none!important;}
.aj-logo-main{font-family:'Cormorant Garamond',serif;font-size:1.25rem;font-weight:600;color:#B8860B;letter-spacing:.22em;display:flex;align-items:center;gap:6px;line-height:1;}
.aj-logo-d{width:5px;height:5px;background:#B8860B;transform:rotate(45deg);display:inline-block;}
.aj-logo-sub{font-family:'DM Sans',sans-serif;font-size:.42rem;color:#8B6914;letter-spacing:.3em;text-transform:uppercase;}
.aj-nav-links{display:flex;gap:22px;list-style:none;margin:0;padding:0;}
.aj-nav-links a{font-family:'DM Sans',sans-serif;font-size:.62rem;letter-spacing:.13em;text-transform:uppercase;color:#4A3728;transition:color .2s;padding-bottom:2px;border-bottom:1.5px solid transparent;}
.aj-nav-links a:hover{color:#B8860B;border-bottom-color:#B8860B;}
.aj-nav-right{display:flex;align-items:center;gap:12px;}
.aj-icon{font-size:1.05rem;color:#4A3728;display:flex;align-items:center;justify-content:center;width:26px;height:26px;position:relative;transition:color .2s;text-decoration:none!important;}
.aj-icon:hover{color:#B8860B;}
.aj-badge{position:absolute;top:-5px;right:-6px;background:#9B2335;color:#fff;font-size:.44rem;font-weight:700;border-radius:50%;width:13px;height:13px;display:flex;align-items:center;justify-content:center;}
.aj-btn-ac{font-family:'DM Sans',sans-serif;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;border:1.5px solid #B8860B;color:#B8860B!important;padding:6px 12px;border-radius:2px;transition:all .2s;}
.aj-btn-ac:hover{background:#B8860B;color:#fff!important;}
.aj-btn-si{font-family:'DM Sans',sans-serif;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;background:#1A1008;color:#FFFDF9!important;padding:7px 16px;border-radius:2px;transition:background .2s;}
.aj-btn-si:hover{background:#B8860B;}

/* ── TICKER ──────────────────────────────────────────────── */
.aj-ticker{background:#1A1008;padding:7px 5%;display:flex;align-items:center;justify-content:space-between;}
.aj-ticker-items{display:flex;align-items:center;}
.aj-ti{padding:0 16px;border-right:1px solid rgba(184,134,11,.28);display:flex;align-items:center;gap:6px;}
.aj-ti:first-child{padding-left:0;}.aj-ti:last-child{border:none;}
.aj-ti-l{font-family:'DM Sans',sans-serif;font-size:.54rem;color:rgba(255,253,249,.45);letter-spacing:.12em;text-transform:uppercase;}
.aj-ti-v{font-family:'DM Sans',sans-serif;font-size:.9rem;font-weight:600;color:#D4A843;}
.aj-ti-u{font-size:.5rem;color:rgba(212,168,67,.5);}
.aj-tr{display:flex;align-items:center;gap:7px;}
.aj-ld{width:5px;height:5px;border-radius:50%;background:#4CAF50;}
.aj-lt{font-family:'DM Sans',sans-serif;font-size:.52rem;color:rgba(255,253,249,.36);}
.aj-bis-pill{font-family:'DM Sans',sans-serif;font-size:.52rem;background:rgba(184,134,11,.16);color:#D4A843;border:1px solid rgba(184,134,11,.28);padding:2px 9px;border-radius:2px;}

/* ── STEPPER ─────────────────────────────────────────────── */
.co-steps{background:#FFF8EE;border-bottom:1px solid #EDD9A3;padding:16px 5%;display:flex;align-items:center;}
.co-step{display:flex;align-items:center;gap:8px;}
.co-step-num{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'DM Sans',sans-serif;font-size:.6rem;font-weight:600;flex-shrink:0;}
.co-step-num.done{background:#B8860B;color:#fff;}
.co-step-num.active{background:#1A1008;color:#E8C547;}
.co-step-num.todo{background:#EDD9A3;color:#8B6914;}
.co-step-lbl{font-family:'DM Sans',sans-serif;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;}
.co-step-lbl.done{color:#B8860B;}
.co-step-lbl.active{color:#1A1008;font-weight:600;}
.co-step-lbl.todo{color:#C8A96A;}
.co-step-line{flex:1;height:1.5px;margin:0 14px;}
.co-step-line.done{background:#B8860B;}
.co-step-line.todo{background:#EDD9A3;}

/* ── LEFT COLUMN — delivery + payment ───────────────────── */
.co-left{padding:24px 32px 36px;min-height:60vh;}

/* ── SECTION HEADERS ─────────────────────────────────────── */
.co-sec-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;padding-bottom:10px;border-bottom:2px solid #B8860B;}
.co-sec-title{font-family:'DM Sans',sans-serif;font-size:.85rem;color:#1A1008;letter-spacing:.1em;text-transform:uppercase;font-weight:600;}
.co-sec-link{font-family:'DM Sans',sans-serif;font-size:.65rem;color:#B8860B;border-bottom:1px solid rgba(184,134,11,.3);}
.co-section{margin-bottom:24px;}

/* ── ADDRESS CARDS ───────────────────────────────────────── */
.co-addr-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:6px;}
.co-addr-card{border:1.5px solid #EDD9A3;border-radius:6px;padding:14px 16px;cursor:pointer;position:relative;transition:border-color .2s;background:#fff;}
.co-addr-card:hover{border-color:#D4A843;}
.co-addr-card.sel{border-color:#B8860B;background:#FFFDF5;}
.co-addr-radio{position:absolute;top:12px;right:12px;width:16px;height:16px;border-radius:50%;border:1.5px solid #EDD9A3;display:flex;align-items:center;justify-content:center;}
.co-addr-radio.sel::after{content:'';width:8px;height:8px;border-radius:50%;background:#B8860B;display:block;}
.co-addr-card.sel .co-addr-radio{border-color:#B8860B;}
.co-addr-lbl{font-family:'DM Sans',sans-serif;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;color:#B8860B;margin-bottom:5px;font-weight:600;}
.co-addr-name{font-family:'DM Sans',sans-serif;font-size:.82rem;color:#1A1008;font-weight:600;margin-bottom:4px;}
.co-addr-txt{font-family:'DM Sans',sans-serif;font-size:.74rem;color:#8B6914;line-height:1.65;}
.co-addr-del{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#9B2335;margin-top:8px;display:inline-block;border-bottom:1px solid rgba(155,35,53,.25);}
.co-addr-add{border:1.5px dashed #EDD9A3;border-radius:6px;padding:20px 16px;display:flex;align-items:center;justify-content:center;gap:8px;cursor:pointer;transition:border-color .2s;background:#fff;}
.co-addr-add:hover{border-color:#B8860B;}
.co-addr-add-icon{width:22px;height:22px;border-radius:50%;border:1.5px solid #B8860B;display:flex;align-items:center;justify-content:center;font-size:.9rem;color:#B8860B;}
.co-addr-add-txt{font-family:'DM Sans',sans-serif;font-size:.68rem;color:#B8860B;letter-spacing:.1em;text-transform:uppercase;}

/* ── PAYMENT OPTIONS ─────────────────────────────────────── */
.co-pay-opts{display:flex;flex-direction:column;gap:10px;}
.co-pay-opt{border:1.5px solid #EDD9A3;border-radius:6px;padding:14px 18px;cursor:pointer;display:flex;align-items:center;gap:14px;transition:border-color .2s;background:#fff;}
.co-pay-opt:hover{border-color:#D4A843;}
.co-pay-opt.sel{border-color:#B8860B;background:#FFFDF5;}
.co-pay-radio{width:18px;height:18px;border-radius:50%;border:1.5px solid #EDD9A3;flex-shrink:0;display:flex;align-items:center;justify-content:center;}
.co-pay-opt.sel .co-pay-radio{border-color:#B8860B;}
.co-pay-opt.sel .co-pay-radio::after{content:'';width:8px;height:8px;border-radius:50%;background:#B8860B;display:block;}
.co-pay-info{flex:1;}
.co-pay-title{font-family:'DM Sans',sans-serif;font-size:.82rem;color:#1A1008;font-weight:600;margin-bottom:3px;}
.co-pay-sub{font-family:'DM Sans',sans-serif;font-size:.68rem;color:#8B6914;}
.co-pay-badge{font-family:'DM Sans',sans-serif;font-size:.6rem;letter-spacing:.1em;font-weight:600;color:#8B6914;background:#F5E6C8;border:1px solid #EDD9A3;border-radius:3px;padding:4px 12px;}

/* UPI input */
.co-upi-area{margin-top:12px;}
.co-upi-inner{background:#FFF8EE;border:1px solid #EDD9A3;border-radius:6px;padding:16px 18px;display:flex;gap:14px;align-items:flex-start;}
.co-upi-label{font-family:'DM Sans',sans-serif;font-size:.68rem;color:#8B6914;letter-spacing:.1em;text-transform:uppercase;margin-bottom:7px;}
.co-upi-or{font-family:'DM Sans',sans-serif;font-size:.62rem;color:#C8A96A;text-align:center;padding-top:24px;}
.co-qr-stub{width:60px;height:60px;background:#FFFDF9;border:1px solid #EDD9A3;border-radius:4px;display:grid;grid-template-columns:repeat(4,1fr);gap:2px;padding:7px;flex-shrink:0;}
.co-qr-cell{border-radius:1px;}

/* ── RIGHT COLUMN — order summary ───────────────────────── */
.co-right{padding:24px 28px 36px;}
.co-summary{background:transparent;}
.co-sum-hdr{margin-bottom:16px;padding-bottom:12px;border-bottom:2px solid #B8860B;}
.co-sum-title{font-family:'Cormorant Garamond',serif;font-size:1.3rem;font-weight:600;color:#1A1008;letter-spacing:.03em;}
.co-sum-items{margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid #EDD9A3;}
.co-sum-item{display:flex;align-items:flex-start;gap:12px;margin-bottom:14px;}
.co-sum-item:last-child{margin-bottom:0;}
.co-sum-img{width:54px;height:54px;border-radius:6px;overflow:hidden;flex-shrink:0;background:#F5E6C8;border:1px solid #EDD9A3;}
.co-sum-img img{width:100%;height:100%;object-fit:cover;}
.co-sum-info{flex:1;min-width:0;}
.co-sum-item-name{font-family:'DM Sans',sans-serif;font-size:.76rem;color:#1A1008;font-weight:600;line-height:1.35;margin-bottom:3px;}
.co-sum-item-sub{font-family:'DM Sans',sans-serif;font-size:.66rem;color:#8B6914;}
.co-sum-item-price{font-family:'DM Sans',sans-serif;font-size:.82rem;font-weight:700;color:#B8860B;white-space:nowrap;}
.co-sum-rows{display:flex;flex-direction:column;gap:10px;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid #EDD9A3;}
.co-sum-row{display:flex;justify-content:space-between;align-items:center;}
.co-sum-row-lbl{font-family:'DM Sans',sans-serif;font-size:.74rem;color:#8B6914;}
.co-sum-row-val{font-family:'DM Sans',sans-serif;font-size:.76rem;color:#1A1008;font-weight:500;}
.co-sum-row.disc .co-sum-row-val{color:#2E7D32;}
.co-sum-row.total{padding-top:10px;}
.co-sum-row.total .co-sum-row-lbl{font-family:'DM Sans',sans-serif;font-size:.8rem;color:#1A1008;font-weight:600;}
.co-sum-row.total .co-sum-row-val{font-family:'DM Sans',sans-serif;font-size:1.2rem;font-weight:700;color:#B8860B;}
.co-rate-note{padding:12px 0;display:flex;align-items:flex-start;gap:7px;margin-bottom:4px;}
.co-rate-dot{width:6px;height:6px;border-radius:50%;background:#4CAF50;flex-shrink:0;margin-top:3px;}
.co-rate-txt{font-family:'DM Sans',sans-serif;font-size:.66rem;color:#8B6914;line-height:1.6;}
.co-place-btn{display:block;background:linear-gradient(135deg,#B8860B,#9B7209);color:#FFFDF9!important;text-align:center;padding:16px;border-radius:4px;font-family:'DM Sans',sans-serif;font-size:.78rem;letter-spacing:.18em;text-transform:uppercase;font-weight:600;transition:all .2s;box-shadow:0 2px 12px rgba(184,134,11,.3);margin-bottom:10px;}
.co-place-btn:hover{background:linear-gradient(135deg,#9B7209,#7A5A07);box-shadow:0 4px 18px rgba(184,134,11,.45);}
.co-secure-note{text-align:center;font-family:'DM Sans',sans-serif;font-size:.6rem;color:#C8A96A;display:flex;align-items:center;justify-content:center;gap:5px;}
.co-err{background:#FFEBEE;border:1px solid #FFCDD2;border-radius:4px;padding:10px 14px;font-family:'DM Sans',sans-serif;font-size:.72rem;color:#B71C1C;margin-bottom:10px;}

/* ── Streamlit form overrides ────────────────────────────── */
.stTextInput>div>div>input{border:1.5px solid #E8D5A3!important;border-radius:4px!important;background:#FFFDF9!important;color:#1A1008!important;font-family:'DM Sans',sans-serif!important;font-size:.82rem!important;}
.stTextInput>div>div>input:focus{border-color:#B8860B!important;box-shadow:none!important;}
.stTextInput label,.stSelectbox label,.stTextArea label{font-family:'DM Sans',sans-serif!important;font-size:.66rem!important;letter-spacing:.1em!important;text-transform:uppercase!important;color:#8B6914!important;font-weight:400!important;}
.stSelectbox>div>div{border:1.5px solid #E8D5A3!important;border-radius:4px!important;background:#FFFDF9!important;font-family:'DM Sans',sans-serif!important;font-size:.82rem!important;}
.stButton>button{background:#1A1008!important;color:#FFFDF9!important;border:none!important;border-radius:4px!important;padding:12px 22px!important;font-family:'DM Sans',sans-serif!important;font-size:.72rem!important;letter-spacing:.13em!important;text-transform:uppercase!important;transition:background .2s!important;width:100%!important;}
.stButton>button:hover{background:#B8860B!important;}
[data-testid="stDownloadButton"]>button{background:#1A1008!important;color:#FFFDF9!important;border:none!important;border-radius:4px!important;padding:14px 22px!important;font-family:'DM Sans',sans-serif!important;font-size:.72rem!important;letter-spacing:.13em!important;text-transform:uppercase!important;width:100%!important;}
[data-testid="stDownloadButton"]>button:hover{background:#B8860B!important;}
[data-testid="stForm"]{border:none!important;padding:0!important;background:transparent!important;}

/* ── CONFIRMATION ────────────────────────────────────────── */
.conf-hero{background:#1A1008;padding:40px 5%;text-align:center;}
.conf-ring{width:72px;height:72px;border-radius:50%;border:2px solid #D4A843;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;}
.conf-inner{width:54px;height:54px;border-radius:50%;background:#B8860B;display:flex;align-items:center;justify-content:center;}
.conf-tick{width:22px;height:13px;border-left:3px solid #fff;border-bottom:3px solid #fff;transform:rotate(-45deg);margin-top:-5px;}
.conf-title{font-family:'Cormorant Garamond',serif;font-size:2rem;font-weight:600;color:#D4A843;letter-spacing:.04em;margin-bottom:8px;}
.conf-sub{font-family:'DM Sans',sans-serif;font-size:.7rem;color:rgba(255,253,249,.45);letter-spacing:.1em;margin-bottom:14px;}
.conf-order-no{font-family:'DM Sans',sans-serif;font-size:.62rem;color:#D4A843;background:rgba(184,134,11,.15);border:1px solid rgba(184,134,11,.3);padding:6px 18px;border-radius:2px;display:inline-block;letter-spacing:.14em;}
.conf-body{padding:24px 5%;}
.conf-info-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:20px;}
@media(max-width:700px){.conf-info-grid{grid-template-columns:1fr;}}
.conf-card{background:#fff;border:1px solid #EDD9A3;border-radius:6px;padding:16px 18px;}
.conf-card-lbl{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#B8860B;letter-spacing:.16em;text-transform:uppercase;margin-bottom:7px;font-weight:600;}
.conf-card-val{font-family:'DM Sans',sans-serif;font-size:.76rem;color:#1A1008;line-height:1.65;}
.conf-card-val span{color:#2E7D32;font-weight:600;}
.conf-items{background:#fff;border:1px solid #EDD9A3;border-radius:6px;margin-bottom:18px;overflow:hidden;}
.conf-items-hdr{padding:12px 18px;background:#FFF8EE;border-bottom:1px solid #EDD9A3;font-family:'DM Sans',sans-serif;font-size:.66rem;color:#1A1008;letter-spacing:.14em;text-transform:uppercase;font-weight:600;}
.conf-item-row{display:flex;align-items:center;gap:14px;padding:14px 18px;border-bottom:1px dashed #EDD9A3;}
.conf-item-row:last-child{border-bottom:none;}
.conf-item-img{width:50px;height:50px;border-radius:5px;overflow:hidden;background:#F5E6C8;flex-shrink:0;}
.conf-item-img img{width:100%;height:100%;object-fit:cover;}
.conf-item-name{font-family:'DM Sans',sans-serif;font-size:.74rem;color:#1A1008;font-weight:600;}
.conf-item-sub{font-family:'DM Sans',sans-serif;font-size:.64rem;color:#8B6914;margin-top:3px;}
.conf-item-price{margin-left:auto;font-family:'DM Sans',sans-serif;font-size:.78rem;font-weight:700;color:#B8860B;white-space:nowrap;}
.conf-total{background:#FFF8EE;border:1px solid #EDD9A3;border-radius:6px;padding:16px 20px;display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;}
.conf-total-lbl{font-family:'DM Sans',sans-serif;font-size:.7rem;color:#8B6914;letter-spacing:.12em;text-transform:uppercase;}
.conf-total-val{font-family:'DM Sans',sans-serif;font-size:1.5rem;font-weight:700;color:#B8860B;}
.conf-actions{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px;}
@media(max-width:600px){.conf-actions{grid-template-columns:1fr;}}
.conf-btn-dl{background:#1A1008;color:#FFFDF9!important;text-align:center;padding:14px;border-radius:4px;font-family:'DM Sans',sans-serif;font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;display:flex;align-items:center;justify-content:center;gap:8px;transition:background .2s;}
.conf-btn-dl:hover{background:#B8860B;}
.conf-btn-shop{border:1.5px solid #B8860B;color:#B8860B!important;text-align:center;padding:14px;border-radius:4px;font-family:'DM Sans',sans-serif;font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;transition:all .2s;}
.conf-btn-shop:hover{background:#B8860B;color:#fff!important;}
.conf-email{background:#E8F5E9;border:1px solid #A5D6A7;border-radius:6px;padding:14px 18px;display:flex;align-items:flex-start;gap:12px;}
.conf-email-icon{width:22px;height:22px;border-radius:50%;background:#2E7D32;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;}
.conf-email-tick{width:8px;height:5px;border-left:2px solid #fff;border-bottom:2px solid #fff;transform:rotate(-45deg);margin-top:-2px;}
.conf-email-txt{font-family:'DM Sans',sans-serif;font-size:.72rem;color:#1B5E20;line-height:1.7;}

/* ── FOOTER ──────────────────────────────────────────────── */
.aj-footer{background:#3D1F0E;border-top:3px solid #5C3420;padding:44px 5% 22px;}
.aj-fg{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:40px;margin-bottom:34px;}
.aj-fl-main{font-family:'Cormorant Garamond',serif;font-size:1rem;font-weight:600;color:#D4A843;letter-spacing:.22em;display:flex;align-items:center;gap:5px;margin-bottom:3px;}
.aj-fl-d{width:4px;height:4px;background:#D4A843;transform:rotate(45deg);display:inline-block;opacity:.7;}
.aj-fl-rule{width:100%;height:.6px;background:linear-gradient(to right,transparent,#B8860B,transparent);margin:4px 0;}
.aj-fl-sub{font-family:'DM Sans',sans-serif;font-size:.43rem;color:rgba(212,168,67,.45);letter-spacing:.28em;text-transform:uppercase;}
.aj-fl-tag{font-family:'DM Sans',sans-serif;font-size:.78rem;color:rgba(255,253,249,.34);line-height:1.7;margin:10px 0;}
.aj-fl-gstin{font-family:'DM Sans',sans-serif;font-size:.56rem;color:rgba(212,168,67,.38);background:rgba(184,134,11,.1);padding:3px 9px;border-radius:2px;display:inline-block;}
.aj-fc-title{font-family:'DM Sans',sans-serif;font-size:.56rem;color:rgba(212,168,67,.5);letter-spacing:.18em;text-transform:uppercase;margin-bottom:12px;font-weight:600;}
.aj-fc-links{list-style:none;padding:0;margin:0;}
.aj-fc-links li{margin-bottom:8px;}
.aj-fc-links a{font-family:'DM Sans',sans-serif;font-size:.74rem;color:rgba(255,253,249,.35);transition:color .2s;}
.aj-fc-links a:hover{color:#D4A843;}
.aj-fb{border-top:1px solid rgba(255,255,255,.07);padding-top:16px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:7px;}
.aj-fb-txt{font-family:'DM Sans',sans-serif;font-size:.58rem;color:rgba(255,253,249,.2);}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# NAVBAR
# ════════════════════════════════════════════════════════════
badge  = '<span class="aj-badge">' + str(cart_count) + '</span>' if cart_count > 0 else ""
wbadge = '<span class="aj-badge">' + str(wish_count) + '</span>' if wish_count > 0 else ""
auth   = (
    '<a href="?_nav=Profile" target="_self" class="aj-btn-ac">My Account</a>'
    if True else
    '<a href="?_nav=Login" target="_self" class="aj-btn-si">Sign In</a>'
)
if role == "admin":
    auth += '<a href="?_nav=Admin" target="_self" class="aj-btn-ac">Admin</a>'

st.markdown(
    '<nav class="aj-nav">'
    '<a href="?_nav=Home" target="_self" class="aj-logo">'
    '<div class="aj-logo-main">AURUS<span class="aj-logo-d"></span>JEWELS</div>'
    '<div class="aj-logo-sub">Fine Gold &amp; Silver &middot; BIS Hallmarked</div>'
    '</a>'
    '<ul class="aj-nav-links">'
    '<li><a href="?_nav=Catalogue" target="_self">Catalogue</a></li>'
    '<li><a href="?_nav=Catalogue&cat=pendants" target="_self">Pendants</a></li>'
    '<li><a href="?_nav=Catalogue&cat=rings" target="_self">Rings</a></li>'
    '<li><a href="?_nav=Catalogue&cat=earrings" target="_self">Earrings</a></li>'
    '<li><a href="?_nav=Catalogue&cat=bracelets" target="_self">Bracelets</a></li>'
    '<li><a href="?_nav=Catalogue&cat=chains" target="_self">Chains</a></li>'
    '</ul>'
    '<div class="aj-nav-right">'
    '<a href="?_nav=Wishlist" target="_self" class="aj-icon">&#9825;' + wbadge + '</a>'
    '<a href="?_nav=Cart" target="_self" class="aj-icon">&#128722;' + badge + '</a>'
    '<a href="?_nav=Profile" target="_self" class="aj-icon">&#128100;</a>'
    + auth +
    '</div></nav>',
    unsafe_allow_html=True
)

# ── Ticker ────────────────────────────────────────────────────
st.markdown(
    '<div class="aj-ticker"><div class="aj-ticker-items">'
    '<div class="aj-ti"><span class="aj-ti-l">Gold 22K</span>'
    '<span class="aj-ti-v">' + format_inr(r22k) + '</span><span class="aj-ti-u">/g</span></div>'
    '<div class="aj-ti"><span class="aj-ti-l">Gold 18K</span>'
    '<span class="aj-ti-v">' + format_inr(r18k) + '</span><span class="aj-ti-u">/g</span></div>'
    '<div class="aj-ti"><span class="aj-ti-l">Silver 925</span>'
    '<span class="aj-ti-v">' + format_inr(r925) + '</span><span class="aj-ti-u">/g</span></div>'
    '</div><div class="aj-tr"><div class="aj-ld"></div>'
    '<span class="aj-lt">Live IBJA &middot; Updates 9 AM daily</span>'
    '<span class="aj-bis-pill">BIS Hallmarked</span></div></div>',
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════
# CONFIRMATION SCREEN
# ════════════════════════════════════════════════════════════
if st.session_state["checkout_step"] == "confirmed":
    order_id   = st.session_state.get("placed_order_id")
    inv_path   = st.session_state.get("invoice_path")
    conf_order = execute_one(
        "SELECT * FROM fact_orders WHERE order_id=%s", (order_id,)
    ) if order_id else None
    conf_items = execute_query(
        "SELECT oi.*, p.image_main FROM fact_order_items oi "
        "JOIN dim_products p ON oi.product_id=p.product_id "
        "WHERE oi.order_id=%s", (order_id,)
    ) if order_id else []
    conf_addr  = execute_one(
        "SELECT * FROM dim_addresses WHERE address_id=%s",
        (conf_order["shipping_address_id"],)
    ) if conf_order else None

    inv_no = conf_order["invoice_number"] if conf_order else ("AJ-" + str(order_id))

    # Stepper — confirmation active
    st.markdown(
        '<div class="co-steps">'
        '<div class="co-step"><div class="co-step-num done">&#10003;</div>'
        '<span class="co-step-lbl done">Cart</span></div>'
        '<div class="co-step-line done"></div>'
        '<div class="co-step"><div class="co-step-num done">&#10003;</div>'
        '<span class="co-step-lbl done">Checkout</span></div>'
        '<div class="co-step-line done"></div>'
        '<div class="co-step"><div class="co-step-num active">3</div>'
        '<span class="co-step-lbl active">Confirmation</span></div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Hero
    st.markdown(
        '<div class="conf-hero">'
        '<div class="conf-ring"><div class="conf-inner"><div class="conf-tick"></div></div></div>'
        '<div class="conf-title">Order Confirmed!</div>'
        '<div class="conf-sub">Thank you for shopping with Aurus Jewels</div>'
        '<div class="conf-order-no">Order #' + str(inv_no) + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="conf-body">', unsafe_allow_html=True)

    # Info grid
    pay_method = conf_order.get("notes", "Cash on Delivery") if conf_order else "Cash on Delivery"
    addr_txt   = ""
    if conf_addr:
        addr_txt = (
            str(conf_addr.get("full_name","")) + "<br>" +
            str(conf_addr.get("address_line1","")) +
            ("<br>" + str(conf_addr["address_line2"]) if conf_addr.get("address_line2") else "") +
            "<br>" + str(conf_addr.get("city","")) + " – " + str(conf_addr.get("pincode",""))
        )

    r22k_snap = float(conf_order["gold_rate_22k"]) if conf_order and conf_order.get("gold_rate_22k") else r22k
    r18k_snap = float(conf_order["gold_rate_18k"]) if conf_order and conf_order.get("gold_rate_18k") else r18k

    st.markdown(
        '<div class="conf-info-grid">'
        '<div class="conf-card"><div class="conf-card-lbl">Delivering To</div>'
        '<div class="conf-card-val">' + addr_txt + '</div></div>'
        '<div class="conf-card"><div class="conf-card-lbl">Payment</div>'
        '<div class="conf-card-val">' + str(pay_method) + '<br>'
        '<span>Pay on arrival</span></div></div>'
        '<div class="conf-card"><div class="conf-card-lbl">Estimated Delivery</div>'
        '<div class="conf-card-val">3–5 business days<br>Fully insured &amp; tracked</div></div>'
        '<div class="conf-card"><div class="conf-card-lbl">Gold Rate at Order</div>'
        '<div class="conf-card-val">22K: ' + format_inr(r22k_snap) + '/g<br>'
        '18K: ' + format_inr(r18k_snap) + '/g</div></div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Items
    if conf_items:
        rows = ""
        for it in conf_items:
            img_html = (
                '<img src="' + img_url(it.get("image_main","")) + '" style="width:100%;height:100%;object-fit:cover;">'
                if it.get("image_main") else ""
            )
            rows += (
                '<div class="conf-item-row">'
                '<div class="conf-item-img">' + img_html + '</div>'
                '<div><div class="conf-item-name">' + str(it["product_name"]) + '</div>'
                '<div class="conf-item-sub">' + str(it["karat"]) + ' ' + str(it["metal_type"]).title()
                + ' &middot; ' + str(round(float(it["weight_g"]),1)) + 'g</div></div>'
                '<div class="conf-item-price">' + format_inr(float(it["line_total"])) + '</div>'
                '</div>'
            )
        st.markdown(
            '<div class="conf-items">'
            '<div class="conf-items-hdr">Items Ordered</div>'
            + rows + '</div>',
            unsafe_allow_html=True
        )

    # Total
    total_amt = float(conf_order["total_amount"]) if conf_order else final_total
    st.markdown(
        '<div class="conf-total">'
        '<span class="conf-total-lbl">Total Paid</span>'
        '<span class="conf-total-val">' + format_inr(total_amt) + '</span>'
        '</div>',
        unsafe_allow_html=True
    )

    # Action buttons — check actual file on disk
    actual_inv_path = st.session_state.get("invoice_path")
    if actual_inv_path and not os.path.exists(actual_inv_path):
        actual_inv_path = None

    if actual_inv_path:
        st.markdown('<div class="conf-actions">', unsafe_allow_html=True)
        with open(actual_inv_path, "rb") as f:
            st.download_button(
                label="⬇  Download GST Invoice",
                data=f.read(),
                file_name="AurusJewels_Invoice_" + str(inv_no) + ".pdf",
                mime="application/pdf",
                use_container_width=True
            )
        st.markdown(
            '<a href="?_nav=Catalogue" class="conf-btn-shop" style="display:block;text-align:center;margin-top:10px;">Continue Shopping</a></div>',
            unsafe_allow_html=True
        )
    else:
        # Invoice not ready — show both buttons side by side without empty column
        st.markdown(
            '<div class="conf-actions">'
            '<div style="background:#FFF8EE;border:1px solid #EDD9A3;border-radius:2px;'
            'padding:14px;text-align:center;font-family:\'DM Sans\',sans-serif;'
            'font-size:.6rem;color:#8B6914;letter-spacing:.12em;text-transform:uppercase;'
            'display:flex;align-items:center;justify-content:center;gap:8px;">'
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8B6914" stroke-width="2">'
            '<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/>'
            '</svg>'
            'Invoice generating &mdash; check your email shortly'
            '</div>'
            '<a href="?_nav=Catalogue" class="conf-btn-shop">Continue Shopping</a>'
            '</div>',
            unsafe_allow_html=True
        )

    # Email confirmation note
    st.markdown(
        '<div class="conf-email" style="margin-top:14px;">'
        '<div class="conf-email-icon"><div class="conf-email-tick"></div></div>'
        '<div class="conf-email-txt">A GST-compliant invoice with CGST + SGST breakdown has been '
        'emailed to <strong>' + str(email) + '</strong>. '
        'Check your inbox — it may take a few minutes to arrive.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# CHECKOUT SCREEN
# ════════════════════════════════════════════════════════════
else:
    # Stepper
    st.markdown(
        '<div class="co-steps">'
        '<div class="co-step"><div class="co-step-num done">&#10003;</div>'
        '<span class="co-step-lbl done">Cart</span></div>'
        '<div class="co-step-line done"></div>'
        '<div class="co-step"><div class="co-step-num active">2</div>'
        '<span class="co-step-lbl active">Checkout</span></div>'
        '<div class="co-step-line todo"></div>'
        '<div class="co-step"><div class="co-step-num todo">3</div>'
        '<span class="co-step-lbl todo">Confirmation</span></div>'
        '</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns([55, 45])
    with left:
        # ── DELIVERY ADDRESS ──────────────────────────────────
        st.markdown(
            '<div class="co-section">'
            '<div class="co-sec-hdr">'
            '<span class="co-sec-title">Delivery Address</span>'
            '<a href="?action=show_add_addr" target="_self" class="co-sec-link">+ Add New Address</a>'
            '</div>',
            unsafe_allow_html=True
        )

        # Address cards grid
        if addresses:
            addr_html = '<div class="co-addr-grid">'
            for addr in addresses:
                sel   = str(addr["address_id"]) == str(st.session_state["selected_address_id"])
                sel_c = " sel" if sel else ""
                addr_html += (
                    '<div class="co-addr-card' + sel_c + '">'
                    '<a href="?action=select_address&id=' + str(addr["address_id"]) + '" '
                    'style="display:block;text-decoration:none!important;" target="_self">'
                    '<div class="co-addr-radio' + sel_c + '"></div>'
                    '<div class="co-addr-lbl">' + str(addr.get("label","Home")) + '</div>'
                    '<div class="co-addr-name">' + str(addr.get("full_name","")) + '</div>'
                    '<div class="co-addr-txt">'
                    + str(addr.get("address_line1",""))
                    + (", " + str(addr["address_line2"]) if addr.get("address_line2") else "")
                    + "<br>" + str(addr.get("city","")) + ", " + str(addr.get("state",""))
                    + " – " + str(addr.get("pincode",""))
                    + "<br>" + str(addr.get("phone","")) +
                    '</div>'
                    '</a>'
                    '<a href="?action=delete_address&id=' + str(addr["address_id"]) + '" '
                    'class="co-addr-del" target="_self">Remove</a>'
                    '</div>'
                )
            addr_html += (
                '<a href="?action=show_add_addr" target="_self" class="co-addr-add">'
                '<div class="co-addr-add-icon">+</div>'
                '<span class="co-addr-add-txt">Add New Address</span>'
                '</a>'
                '</div>'
            )
            st.markdown(addr_html, unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="padding:16px 18px;">'
                '<div style="font-family:\'DM Sans\',sans-serif;font-size:.66rem;'
                'color:#8B6914;margin-bottom:12px;">No saved addresses. Add one to continue.</div>'
                '</div>',
                unsafe_allow_html=True
            )

  # close co-section

        # ── ADD NEW ADDRESS FORM ──────────────────────────────
        if st.session_state["show_add_addr"]:
            st.markdown(
                '<div class="co-section">'
                '<div class="co-sec-hdr"><span class="co-sec-title">New Delivery Address</span></div>',
                unsafe_allow_html=True
            )
            with st.form("add_address_form"):
                c1, c2 = st.columns(2)
                with c1:
                    a_name  = st.text_input("Full Name", placeholder="Recipient's full name")
                    a_line1 = st.text_input("Address Line 1", placeholder="House / Flat / Street")
                    a_city  = st.text_input("City", placeholder="City")
                with c2:
                    a_phone = st.text_input("Phone", placeholder="10-digit mobile number")
                    a_line2 = st.text_input("Address Line 2 (optional)", placeholder="Area / Landmark")
                    a_state = st.text_input("State", placeholder="State")
                c3, c4 = st.columns(2)
                with c3:
                    a_pin   = st.text_input("Pincode", placeholder="6-digit pincode")
                with c4:
                    a_label = st.selectbox("Label", ["Home", "Work", "Other"])
                a_default = st.checkbox("Set as default address")
                save_addr = st.form_submit_button("Save Address", use_container_width=True)

                if save_addr:
                    if not a_name or not a_line1 or not a_city or not a_state or not a_pin or not a_phone:
                        st.error("Please fill all required fields.")
                    else:
                        if a_default:
                            execute_write(
                                "UPDATE dim_addresses SET is_default=0 WHERE customer_id=%s", (cid,)
                            )
                        new_addr_id = execute_write(
                            """INSERT INTO dim_addresses
                               (customer_id, label, full_name, phone,
                                address_line1, address_line2, city, state, pincode, is_default)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (cid, a_label, a_name.strip(), a_phone.strip(),
                             a_line1.strip(), a_line2.strip() or None,
                             a_city.strip(), a_state.strip(), a_pin.strip(),
                             1 if a_default else 0)
                        )
                        if new_addr_id:
                            st.session_state["selected_address_id"] = new_addr_id
                            st.session_state["show_add_addr"] = False
                            st.success("Address saved!")
                            st.rerun()

    

        # ── PAYMENT METHOD ────────────────────────────────────
        selected_pay = st.session_state["payment_method"]
        cod_sel      = " sel" if selected_pay == "cod" else ""
        upi_sel      = " sel" if selected_pay == "upi" else ""

        st.markdown(
            '<div class="co-section">'
            '<div class="co-sec-hdr"><span class="co-sec-title">Payment Method</span></div>'
            '<div class="co-pay-opts">'
            '<a href="?action=select_payment&method=cod" target="_self" style="text-decoration:none!important;">'
            '<div class="co-pay-opt' + cod_sel + '">'
            '<div class="co-pay-radio' + cod_sel + '"></div>'
            '<div class="co-pay-info">'
            '<div class="co-pay-title">Cash on Delivery</div>'
            '<div class="co-pay-sub">Pay in cash when your order arrives at the door</div>'
            '</div><span class="co-pay-badge">COD</span>'
            '</div></a>'
            '<a href="?action=select_payment&method=upi" target="_self" style="text-decoration:none!important;">'
            '<div class="co-pay-opt' + upi_sel + '">'
            '<div class="co-pay-radio' + upi_sel + '"></div>'
            '<div class="co-pay-info">'
            '<div class="co-pay-title">UPI Payment</div>'
            '<div class="co-pay-sub">Pay instantly via GPay, PhonePe, Paytm or any UPI app</div>'
            '</div><span class="co-pay-badge">UPI</span>'
            '</div></a>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

        # UPI ID input shown only when UPI selected
        if selected_pay == "upi":
            st.markdown(
                '<div class="co-upi-area">'
                '<div class="co-upi-inner">',
                unsafe_allow_html=True
            )
            col_upi, col_or, col_qr = st.columns([4, 1, 1])
            with col_upi:
                st.markdown('<div class="co-upi-label">Your UPI ID</div>', unsafe_allow_html=True)
                upi_val = st.text_input(
                    "UPI ID", label_visibility="collapsed",
                    placeholder="yourname@upi",
                    value=st.session_state.get("upi_id",""),
                    key="upi_input"
                )
                st.session_state["upi_id"] = upi_val
            with col_or:
                st.markdown('<div class="co-upi-or">or</div>', unsafe_allow_html=True)
            with col_qr:
                st.markdown(
                    '<div style="margin-top:8px;">'
                    '<div style="font-family:\'DM Sans\',sans-serif;font-size:.5rem;color:#8B6914;'
                    'text-align:center;margin-bottom:4px;">Scan QR</div>'
                    '<div class="co-qr-stub">'
                    '<div class="co-qr-cell" style="background:#1A1008;"></div>'
                    '<div class="co-qr-cell" style="background:#EDD9A3;"></div>'
                    '<div class="co-qr-cell" style="background:#1A1008;"></div>'
                    '<div class="co-qr-cell" style="background:#EDD9A3;"></div>'
                    '<div class="co-qr-cell" style="background:#B8860B;"></div>'
                    '<div class="co-qr-cell" style="background:#EDD9A3;"></div>'
                    '<div class="co-qr-cell" style="background:#1A1008;"></div>'
                    '<div class="co-qr-cell" style="background:#EDD9A3;"></div>'
                    '<div class="co-qr-cell" style="background:#1A1008;"></div>'
                    '<div class="co-qr-cell" style="background:#EDD9A3;"></div>'
                    '<div class="co-qr-cell" style="background:#B8860B;"></div>'
                    '<div class="co-qr-cell" style="background:#1A1008;"></div>'
                    '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div></div>', unsafe_allow_html=True)

    with right:
        # Build items HTML
        items_html = '<div class="co-sum-items">'
        for item in cart_items:
            img_tag = (
                '<img src="' + img_url(item.get("image_main","")) + '" '
                'style="width:100%;height:100%;object-fit:cover;">'
                if item.get("image_main") else ""
            )
            items_html += (
                '<div class="co-sum-item">'
                '<div class="co-sum-img">' + img_tag + '</div>'
                '<div class="co-sum-info">'
                '<div class="co-sum-item-name">' + str(item["name"]) + '</div>'
                '<div class="co-sum-item-sub">'
                + str(item["karat"]) + ' ' + str(item["metal_type"]).title()
                + ' &middot; ' + str(round(float(item["weight_g"]),1)) + 'g'
                + ' &middot; Qty ' + str(item["quantity"]) +
                '</div>'
                '</div>'
                '<div class="co-sum-item-price">' + format_inr(item["line_total"]) + '</div>'
                '</div>'
            )
        items_html += '</div>'

        # Rows
        rows_html = (
            '<div class="co-sum-rows">'
            '<div class="co-sum-row">'
            '<span class="co-sum-row-lbl">Subtotal (' + str(item_count) + ' item' + ('s' if item_count != 1 else '') + ')</span>'
            '<span class="co-sum-row-val">' + format_inr(subtotal) + '</span>'
            '</div>'
        )
        if loyalty_disc > 0:
            tier_label = tier.title() + " Tier (" + str(int(loyalty_pct*100)) + "% off)"
            rows_html += (
                '<div class="co-sum-row disc">'
                '<span class="co-sum-row-lbl">Loyalty Discount · ' + tier_label + '</span>'
                '<span class="co-sum-row-val">&minus;' + format_inr(loyalty_disc) + '</span>'
                '</div>'
            )
        rows_html += (
            '<div class="co-sum-row">'
            '<span class="co-sum-row-lbl">Shipping</span>'
            '<span class="co-sum-row-val" style="color:#2E7D32;">Free</span>'
            '</div>'
            '<div class="co-sum-row total">'
            '<span class="co-sum-row-lbl">Total Payable</span>'
            '<span class="co-sum-row-val">' + format_inr(final_total) + '</span>'
            '</div>'
            '</div>'
        )

        st.markdown(
            '<div class="co-summary" style="border:none;border-radius:0;background:transparent;">'
            '<div class="co-sum-hdr"><div class="co-sum-title">Order Summary</div></div>'
            + items_html + rows_html +
            '<div class="co-rate-note">'
            '<div class="co-rate-dot"></div>'
            '<span class="co-rate-txt">Prices locked at today\'s IBJA rate.<br>'
            'Final amount won\'t change after placing order.</span>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

        # Place Order button + validation
        st.markdown('<div style="margin-top:4px;">', unsafe_allow_html=True)
        if st.button("Place Order →", use_container_width=True):
            if not st.session_state["selected_address_id"]:
                st.error("Please select a delivery address before placing your order.")
            elif st.session_state["payment_method"] == "upi" and not st.session_state.get("upi_id","").strip():
                st.error("Please enter your UPI ID to proceed.")
            else:
                # Store payment method note in order notes field
                pay_note = (
                    "Cash on Delivery" if st.session_state["payment_method"] == "cod"
                    else "UPI: " + st.session_state.get("upi_id","")
                )
                with st.spinner("Placing your order..."):
                    oid, err = place_order()
                if err:
                    st.error(err)
                else:
                    # Update notes column with payment method
                    execute_write(
                        "UPDATE fact_orders SET notes=%s WHERE order_id=%s",
                        (pay_note, oid)
                    )
                    # Fetch invoice path to enable download on confirmation screen
                    inv_row = execute_one(
                        "SELECT invoice_path FROM fact_orders WHERE order_id=%s", (oid,)
                    )
                    fetched_path = inv_row["invoice_path"] if inv_row and inv_row.get("invoice_path") else None
                    # Verify file actually exists on disk
                    if fetched_path and not os.path.exists(fetched_path):
                        fetched_path = None
                    st.session_state["checkout_step"]   = "confirmed"
                    st.session_state["placed_order_id"] = oid
                    st.session_state["invoice_path"]    = fetched_path
                    st.rerun()



        st.markdown(
            '<div class="co-secure-note">'
            '<svg width="10" height="12" viewBox="0 0 10 12" fill="none">'
            '<rect x="1" y="5" width="8" height="7" rx="1" fill="#C8A96A"/>'
            '<path d="M3 5V3.5a2 2 0 0 1 4 0V5" stroke="#C8A96A" stroke-width="1.2"/>'
            '</svg>'
            'Secure checkout &middot; BIS Hallmarked &middot; GST Invoice included'
            '</div>',
            unsafe_allow_html=True
        )



# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════
st.markdown(
    '<div class="aj-footer">'
    '<div class="aj-fg">'
    '<div>'
    '<div class="aj-fl-main">AURUS<span class="aj-fl-d"></span>JEWELS</div>'
    '<div class="aj-fl-rule"></div>'
    '<div class="aj-fl-sub">Fine Gold &amp; Silver &middot; BIS Hallmarked</div>'
    '<p class="aj-fl-tag">Fine hallmarked jewellery priced live from the official IBJA gold rate.</p>'
    '<span class="aj-fl-gstin">GSTIN: 07AABCS1429B1Z6</span>'
    '</div>'
    '<div><div class="aj-fc-title">Shop</div><ul class="aj-fc-links">'
    '<li><a href="?_nav=Catalogue&cat=pendants" target="_self">Pendants</a></li>'
    '<li><a href="?_nav=Catalogue&cat=rings" target="_self">Rings</a></li>'
    '<li><a href="?_nav=Catalogue&cat=earrings" target="_self">Earrings</a></li>'
    '<li><a href="?_nav=Catalogue&cat=bracelets" target="_self">Bracelets</a></li>'
    '<li><a href="?_nav=Catalogue&cat=chains" target="_self">Chains</a></li>'
    '</ul></div>'
    '<div><div class="aj-fc-title">Account</div><ul class="aj-fc-links">'
    '<li><a href="?_nav=Login" target="_self">Sign In</a></li>'
    '<li><a href="?_nav=Profile" target="_self">My Orders</a></li>'
    '<li><a href="?_nav=Wishlist" target="_self">Wishlist</a></li>'
    '<li><a href="?_nav=Cart" target="_self">Cart</a></li>'
    '</ul></div>'
    '<div><div class="aj-fc-title">Support</div><ul class="aj-fc-links">'
    '<li><a href="#" target="_self">About Us</a></li>'
    '<li><a href="#" target="_self">BIS Hallmarking</a></li>'
    '<li><a href="#" target="_self">Pricing Policy</a></li>'
    '<li><a href="#" target="_self">Contact Us</a></li>'
    '</ul></div>'
    '</div>'
    '<div class="aj-fb">'
    '<span class="aj-fb-txt">&copy; 2026 Aurus Jewels. All rights reserved. All products BIS hallmarked.</span>'
    '<span class="aj-fb-txt">Prices update daily from IBJA official gold rates.</span>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)