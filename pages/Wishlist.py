"""
pages/Wishlist.py — Aurus Jewels Wishlist Page
"""
import streamlit as st
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.session        import init_session, require_login
from core.pricing_engine import get_all_rates, format_inr
from database.db         import execute_query, execute_write, execute_one

st.set_page_config(
    page_title            = "My Wishlist — Aurus Jewels",
    page_icon             = "♡",
    layout                = "wide",
    initial_sidebar_state = "collapsed",
)

init_session()
require_login()

cid = st.session_state.get("customer_id")

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

# ── Action handlers ───────────────────────────────────────────
action     = st.query_params.get("action",   "")
item_id    = st.query_params.get("item",     "")
product_id = st.query_params.get("product",  "")
sort_key   = st.query_params.get("sort",     "recent")

if action == "remove_wish" and item_id:
    execute_write(
        "DELETE FROM customer_wishlist WHERE wishlist_id=%s AND customer_id=%s",
        (item_id, cid)
    )
    st.query_params.clear()
    st.rerun()

if action == "move_to_cart" and item_id and product_id:
    existing = execute_one(
        "SELECT cart_id, quantity FROM customer_cart "
        "WHERE customer_id=%s AND product_id=%s",
        (cid, product_id)
    )
    if existing:
        execute_write(
            "UPDATE customer_cart SET quantity=quantity+1 WHERE cart_id=%s",
            (existing["cart_id"],)
        )
    else:
        execute_write(
            "INSERT INTO customer_cart (customer_id, product_id, quantity) VALUES (%s,%s,1)",
            (cid, product_id)
        )
    execute_write(
        "DELETE FROM customer_wishlist WHERE wishlist_id=%s AND customer_id=%s",
        (item_id, cid)
    )
    st.query_params.clear()
    st.rerun()

if action == "add_all":
    all_items = execute_query(
        "SELECT w.wishlist_id, w.product_id "
        "FROM customer_wishlist w "
        "WHERE w.customer_id=%s",
        (cid,)
    ) or []
    for wi in all_items:
        existing = execute_one(
            "SELECT cart_id FROM customer_cart "
            "WHERE customer_id=%s AND product_id=%s",
            (cid, wi["product_id"])
        )
        if existing:
            execute_write(
                "UPDATE customer_cart SET quantity=quantity+1 WHERE cart_id=%s",
                (existing["cart_id"],)
            )
        else:
            execute_write(
                "INSERT INTO customer_cart (customer_id, product_id, quantity) VALUES (%s,%s,1)",
                (cid, wi["product_id"])
            )
    execute_write(
        "DELETE FROM customer_wishlist WHERE customer_id=%s", (cid,)
    )
    st.query_params.clear()
    st.rerun()

if action == "clear_wishlist":
    execute_write(
        "DELETE FROM customer_wishlist WHERE customer_id=%s", (cid,)
    )
    st.query_params.clear()
    st.rerun()

# ── Sort handler (set via query param, persist in session) ────
if sort_key in ("recent", "price_asc", "price_desc"):
    st.session_state["wish_sort"] = sort_key

sort = st.session_state.get("wish_sort", "recent")

# ── Live rates ────────────────────────────────────────────────
rates = get_all_rates()

def get_rate(metal_type, karat):
    return float(rates.get((metal_type, karat), 6850.0))

def calc_price(weight_g, making_pct, metal_type, karat):
    rate         = get_rate(metal_type, karat)
    metal_val    = float(weight_g) * rate
    making       = metal_val * float(making_pct)
    pre_gst      = metal_val + making
    gst          = pre_gst * 0.05
    return round(pre_gst + gst, 2)

# ── Yesterday's rates for price-change indicator ──────────────
def get_yesterday_rate(metal_type, karat):
    row = execute_one(
        "SELECT rate_per_gram FROM dim_gold_rates "
        "WHERE metal_type=%s AND karat=%s "
        "AND effective_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY)",
        (metal_type, karat)
    )
    return float(row["rate_per_gram"]) if row else None

# ── Fetch wishlist ────────────────────────────────────────────
wishlist_raw = execute_query(
    "SELECT w.wishlist_id, p.product_id, p.sku, p.name, "
    "p.category_id, p.metal_type, p.karat, p.weight_g, p.making_pct, "
    "p.image_main, c.name AS category_name "
    "FROM customer_wishlist w "
    "JOIN dim_products p ON w.product_id=p.product_id "
    "JOIN dim_categories c ON p.category_id=c.category_id "
    "WHERE w.customer_id=%s AND p.is_active=1 "
    "ORDER BY w.wishlist_id DESC",
    (cid,)
) or []

# ── Calculate live prices & apply sort ───────────────────────
for item in wishlist_raw:
    item["final_price"]  = calc_price(
        item["weight_g"], item["making_pct"],
        item["metal_type"], item["karat"]
    )
    yrate = get_yesterday_rate(item["metal_type"], item["karat"])
    if yrate:
        yp = calc_price(item["weight_g"], item["making_pct"], item["metal_type"], item["karat"])
        item["price_dropped"] = get_rate(item["metal_type"], item["karat"]) < yrate
    else:
        item["price_dropped"] = False

if sort == "price_asc":
    wishlist_raw.sort(key=lambda x: x["final_price"])
elif sort == "price_desc":
    wishlist_raw.sort(key=lambda x: x["final_price"], reverse=True)
# default: recent (already ordered by added_at DESC from query)

wishlist_total = sum(i["final_price"] for i in wishlist_raw)
wish_count     = len(wishlist_raw)

# ── Cart count for navbar ─────────────────────────────────────
cart_row   = execute_one("SELECT COUNT(*) AS c FROM customer_cart WHERE customer_id=%s", (cid,))
cart_count = int(cart_row["c"]) if cart_row else 0

# ── Navbar auth ───────────────────────────────────────────────
logged_in = st.session_state.get("logged_in", False)
role      = st.session_state.get("role", "customer")
full_name = st.session_state.get("full_name", "")

# auth built inline in navbar render below

# ── Image url helper ──────────────────────────────────────────
def img_url(path):
    if not path:
        return ""
    return path.replace("\\", "/").replace("static/", "/app/static/")

# ── Sort label helper ─────────────────────────────────────────
SORT_LABELS = {
    "recent":     "Recently Added",
    "price_asc":  "Price: Low to High",
    "price_desc": "Price: High to Low",
}

# ════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════
st.markdown('<base target="_parent">', unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

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

/* ── NAVBAR — exact match to Product.py ─────────────── */
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
.aj-btn-si{font-family:'DM Sans',sans-serif;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;background:#1A1008;color:#FFFDF9!important;padding:7px 16px;border-radius:2px;transition:background .2s;}
.aj-btn-si:hover{background:#B8860B;}
.aj-btn-ac{font-family:'DM Sans',sans-serif;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;border:1.5px solid #B8860B;color:#B8860B!important;padding:6px 12px;border-radius:2px;transition:all .2s;}
.aj-btn-ac:hover{background:#B8860B;color:#fff!important;}

/* ── TICKER — exact match to Product.py ─────────────── */
.aj-ticker{background:#1A1008;padding:7px 5%;display:flex;align-items:center;justify-content:space-between;}
.aj-ticker-items{display:flex;align-items:center;}
.aj-ti{padding:0 16px;border-right:1px solid rgba(184,134,11,.28);display:flex;align-items:center;gap:6px;}
.aj-ti:first-child{padding-left:0;}
.aj-ti:last-child{border:none;}
.aj-ti-l{font-family:'DM Sans',sans-serif;font-size:.54rem;color:rgba(255,253,249,.45);letter-spacing:.12em;text-transform:uppercase;}
.aj-ti-v{font-family:'DM Sans',sans-serif;font-size:.9rem;font-weight:600;color:#D4A843;}
.aj-ti-u{font-size:.5rem;color:rgba(212,168,67,.5);}
.aj-tr{display:flex;align-items:center;gap:7px;}
.aj-ld{width:5px;height:5px;border-radius:50%;background:#4CAF50;}
.aj-lt{font-family:'DM Sans',sans-serif;font-size:.52rem;color:rgba(255,253,249,.36);}
.aj-bis-pill{font-family:'DM Sans',sans-serif;font-size:.52rem;background:rgba(184,134,11,.16);color:#D4A843;border:1px solid rgba(184,134,11,.28);padding:2px 9px;border-radius:2px;}

/* ── PAGE HEADER — centred, elegant ───────────────────── */
.wl-hdr{
  padding:36px 5% 28px;border-bottom:1px solid #EDD9A3;
  text-align:center;position:relative;background:#FFFDF9;
}
.wl-hdr-over{
  font-family:'DM Sans',sans-serif;font-size:.58rem;color:#B8860B;
  letter-spacing:.26em;text-transform:uppercase;margin-bottom:10px;
  display:flex;align-items:center;justify-content:center;gap:12px;
}
.wl-hdr-over::before,.wl-hdr-over::after{
  content:'';display:block;width:32px;height:1px;background:#EDD9A3;
}
.wl-hdr-title{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(2rem,3.5vw,2.8rem);font-weight:600;
  color:#1A1008;letter-spacing:.04em;line-height:1.1;margin-bottom:10px;
  font-style:italic;
}
.wl-hdr-count{
  font-family:'DM Sans',sans-serif;font-size:.62rem;
  color:#8B6914;
}
.wl-shop-link{
  position:absolute;right:5%;top:50%;transform:translateY(-50%);
  font-family:'DM Sans',sans-serif;font-size:.58rem;
  color:#8B6914!important;border-bottom:1px solid #EDD9A3;
  padding-bottom:2px;transition:color .2s;white-space:nowrap;
}
.wl-shop-link:hover{color:#B8860B!important;border-bottom-color:#B8860B;}

/* ── SORT BAR ──────────────────────────────────────────── */
.wl-sortbar{
  padding:11px 5%;background:#FFF8EE;border-bottom:1px solid #EDD9A3;
  display:flex;align-items:center;gap:16px;
}
.wl-sort-lbl{
  font-family:'DM Sans',sans-serif;font-size:.56rem;
  color:#8B6914;letter-spacing:.12em;text-transform:uppercase;
  white-space:nowrap;
}
.wl-sort-pills{display:flex;gap:8px;}
.wl-sort-pill{
  font-family:'DM Sans',sans-serif;font-size:.54rem;letter-spacing:.08em;
  text-transform:uppercase;padding:5px 14px;border-radius:2px;
  border:1.5px solid #EDD9A3;color:#8B6914!important;
  background:#FFFDF9;transition:all .2s;white-space:nowrap;
}
.wl-sort-pill:hover{border-color:#B8860B;color:#B8860B!important;}
.wl-sort-pill.on{background:#B8860B;color:#fff!important;border-color:#B8860B;}
.wl-spacer{flex:1;}
.wl-clear{
  font-family:'DM Sans',sans-serif;font-size:.54rem;letter-spacing:.08em;
  text-transform:uppercase;color:#9B2335!important;
  border-bottom:1px solid rgba(155,35,53,.3);padding-bottom:1px;
  white-space:nowrap;transition:color .2s;
}
.wl-clear:hover{color:#C62828!important;}

/* ── PRODUCT GRID ──────────────────────────────────────── */
.wl-grid{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:20px;padding:24px 5%;
}
@media(max-width:1200px){.wl-grid{grid-template-columns:repeat(3,minmax(0,1fr));}}
@media(max-width:860px) {.wl-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
@media(max-width:540px) {.wl-grid{grid-template-columns:1fr;}}

/* ── PRODUCT CARD ──────────────────────────────────────── */
.wl-card{
  background:#fff;border:1px solid #EDD9A3;border-radius:8px;
  overflow:hidden;display:flex;flex-direction:column;
  transition:border-color .2s;
}
.wl-card:hover{border-color:#D4A843;}

.wl-card-img-wrap{position:relative;aspect-ratio:1;overflow:hidden;background:#F5E6C8;}
.wl-card-img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .4s;}
.wl-card:hover .wl-card-img{transform:scale(1.04);}
.wl-card-img-placeholder{
  width:100%;height:100%;background:linear-gradient(160deg,#D4A843 0%,#EDD9A3 55%,#F5E6C8 100%);
  display:flex;align-items:center;justify-content:center;
}
.wl-card-img-placeholder svg{opacity:.22;}

.wl-karat{
  position:absolute;top:10px;left:10px;
  font-family:'DM Sans',sans-serif;
  font-size:.5rem;background:#1A1008;color:#E8C547;
  padding:3px 7px;border-radius:2px;letter-spacing:.08em;z-index:2;
}
.wl-remove-x{
  position:absolute;top:10px;right:10px;
  width:26px;height:26px;border-radius:50%;
  background:rgba(255,253,249,.92);border:1px solid #EDD9A3;
  display:flex;align-items:center;justify-content:center;
  font-size:.7rem;color:#9B2335;z-index:2;
  transition:background .2s;cursor:pointer;
}
.wl-remove-x:hover{background:#fff;}
.wl-price-drop-badge{
  position:absolute;bottom:10px;left:10px;
  font-family:'DM Sans',sans-serif;
  font-size:.48rem;background:#E8F5E9;color:#2E7D32;
  border:1px solid #A5D6A7;padding:2px 7px;border-radius:2px;
  letter-spacing:.06em;z-index:2;font-weight:600;
}

.wl-card-body{padding:14px 15px 16px;display:flex;flex-direction:column;flex:1;}
.wl-cat{
  font-family:'DM Sans',sans-serif;font-size:.52rem;color:#B8860B;
  letter-spacing:.16em;text-transform:uppercase;margin-bottom:4px;font-weight:500;
}
.wl-name{
  font-family:'Cormorant Garamond',serif;
  font-size:1rem;font-weight:500;color:#1A1008;
  line-height:1.3;margin-bottom:8px;flex:1;
}
.wl-pills{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;}
.wl-pill{
  font-family:'DM Sans',sans-serif;
  font-size:.5rem;background:#F5E6C8;color:#8B6914;
  padding:2px 7px;border-radius:2px;
}
.wl-divider{height:1px;background:#F0E4C4;margin-bottom:11px;}

.wl-price-row{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:12px;}
.wl-price{
  font-family:'DM Sans',sans-serif;
  font-size:1.05rem;font-weight:600;color:#B8860B;line-height:1;
}
.wl-price.dropped{color:#2E7D32;}
.wl-price-sub{
  font-family:'DM Sans',sans-serif;font-size:.5rem;color:#8B6914;
}

.wl-actions{display:flex;gap:8px;align-items:center;}
.wl-move-btn{
  flex:1;background:#1A1008;color:#FFFDF9!important;
  border-radius:2px;padding:9px 12px;
  font-family:'DM Sans',sans-serif;font-size:.54rem;
  letter-spacing:.12em;text-transform:uppercase;
  text-align:center;transition:background .2s;display:block;
}
.wl-move-btn:hover{background:#B8860B;}
.wl-heart-btn{
  width:34px;height:34px;flex-shrink:0;border-radius:2px;
  border:1.5px solid #E57373;background:#FFF0F0;
  display:flex;align-items:center;justify-content:center;
  font-size:.9rem;color:#C62828;transition:all .2s;cursor:pointer;
}
.wl-heart-btn:hover{background:#FFEBEE;}

/* ── SUMMARY BAR ───────────────────────────────────────── */
.wl-sumbar{
  padding:14px 5%;background:#FFF8EE;
  border-top:1.5px solid #EDD9A3;
  display:flex;align-items:center;justify-content:space-between;
  flex-wrap:wrap;gap:12px;
}
.wl-sum-left{}
.wl-sum-lbl{font-family:'DM Sans',sans-serif;font-size:.56rem;color:#8B6914;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px;}
.wl-sum-val{font-family:'Cormorant Garamond',serif;font-size:1.5rem;font-weight:600;color:#B8860B;line-height:1;}
.wl-sum-note{font-family:'DM Sans',sans-serif;font-size:.5rem;color:#8B6914;margin-top:3px;}
.wl-add-all{
  font-family:'DM Sans',sans-serif;font-size:.58rem;letter-spacing:.12em;
  text-transform:uppercase;background:#B8860B;color:#fff!important;
  padding:10px 22px;border-radius:2px;
  transition:background .2s;white-space:nowrap;
}
.wl-add-all:hover{background:#9B7209;}

/* ── EMPTY STATE ───────────────────────────────────────── */
.wl-empty{
  text-align:center;padding:72px 5% 80px;
}
.wl-empty-icon{
  width:64px;height:64px;margin:0 auto 20px;
  border:2px solid #EDD9A3;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
}
.wl-empty-icon svg{color:#EDD9A3;}
.wl-empty-title{
  font-family:'Cormorant Garamond',serif;
  font-size:1.6rem;font-weight:600;color:#1A1008;
  margin-bottom:8px;
}
.wl-empty-sub{
  font-family:'DM Sans',sans-serif;font-size:.72rem;
  color:#8B6914;line-height:1.75;margin-bottom:28px;
  max-width:380px;margin-left:auto;margin-right:auto;
}
.wl-empty-cta{
  font-family:'DM Sans',sans-serif;font-size:.58rem;
  letter-spacing:.12em;text-transform:uppercase;
  background:#1A1008;color:#FFFDF9!important;
  padding:11px 28px;border-radius:2px;
  display:inline-block;transition:background .2s;
}
.wl-empty-cta:hover{background:#B8860B;}

/* ── FOOTER — exact Product.py ─────────────────────────── */
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
r22k = get_rate("gold",   "22K")
r18k = get_rate("gold",   "18K")
r925 = get_rate("silver", "925")

badge  = '<span class="aj-badge">' + str(cart_count) + '</span>' if cart_count > 0 else ""
wbadge = '<span class="aj-badge">' + str(wish_count) + '</span>' if wish_count > 0 else ""
auth   = (
    '<a href="?_nav=Profile" target="_self" class="aj-btn-ac">My Account</a>'
    if logged_in else
    '<a href="?_nav=Login" target="_self" class="aj-btn-si">Sign In</a>'
)
if role == "admin" and logged_in:
    auth = auth + '<a href="?_nav=Admin" target="_self" class="aj-btn-ac">Admin</a>'
plink = "?_nav=Profile" if logged_in else "?_nav=Login"

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
    '<a href="' + plink + '" target="_self" class="aj-icon">&#128100;</a>'
    + auth +
    '</div></nav>',
    unsafe_allow_html=True
)

# ── Ticker — exact Product.py format ─────────────────────────
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
# EMPTY STATE
# ════════════════════════════════════════════════════════════
if wish_count == 0:
    st.markdown(
        '<div class="wl-hdr">'
        '<div class="wl-hdr-left">'
        '<div class="wl-hdr-over">Saved Items</div>'
        '<div class="wl-hdr-title">My Wishlist</div>'
        '<div class="wl-hdr-count">Your wishlist is empty</div>'
        '</div>'
        '<a href="?_nav=Catalogue" class="wl-shop-link">← Browse Catalogue</a>'
        '</div>'
        '<div class="wl-empty">'
        '<div class="wl-empty-icon">'
        '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">'
        '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>'
        '</svg>'
        '</div>'
        '<div class="wl-empty-title">Nothing saved yet</div>'
        '<div class="wl-empty-sub">'
        'Browse our catalogue and tap the heart icon on any piece to save it here.'
        '<br>Your wishlist stays saved across visits.'
        '</div>'
        '<a href="?_nav=Catalogue" class="wl-empty-cta">Explore Catalogue</a>'
        '</div>',
        unsafe_allow_html=True
    )

# ════════════════════════════════════════════════════════════
# WISHLIST WITH ITEMS
# ════════════════════════════════════════════════════════════
else:
    # ── Page header ───────────────────────────────────────────
    item_word = "piece" if wish_count == 1 else "pieces"
    st.markdown(
        '<div class="wl-hdr">'
        '<div class="wl-hdr-left">'
        '<div class="wl-hdr-over">Saved Items</div>'
        '<div class="wl-hdr-title">My Wishlist</div>'
        '<div class="wl-hdr-count">'
        + str(wish_count) + ' ' + item_word +
        ' &nbsp;&middot;&nbsp; All prices live from today\'s IBJA rate'
        '</div>'
        '</div>'
        '<a href="?_nav=Catalogue" class="wl-shop-link">← Continue Shopping</a>'
        '</div>',
        unsafe_allow_html=True
    )

    # ── Sort bar ──────────────────────────────────────────────
    def sort_pill(key, label):
        on = " on" if sort == key else ""
        return (
            '<a href="?sort=' + key + '" target="_self" '
            'class="wl-sort-pill' + on + '">' + label + '</a>'
        )

    st.markdown(
        '<div class="wl-sortbar">'
        '<span class="wl-sort-lbl">Sort by</span>'
        '<div class="wl-sort-pills">'
        + sort_pill("recent",     "Recently Added")
        + sort_pill("price_asc",  "Price: Low to High")
        + sort_pill("price_desc", "Price: High to Low") +
        '</div>'
        '<span class="wl-spacer"></span>'
        '<a href="?action=clear_wishlist" class="wl-clear">✕ Clear Wishlist</a>'
        '</div>',
        unsafe_allow_html=True
    )

    # ── Product grid ──────────────────────────────────────────
    cards_html = '<div class="wl-grid">'

    for item in wishlist_raw:
        wid    = str(item["wishlist_id"])
        pid    = str(item["product_id"])
        price  = item["final_price"]
        karat  = str(item["karat"])
        name   = str(item["name"])
        cat    = str(item["category_name"])
        metal  = str(item["metal_type"]).title()
        weight = str(round(float(item["weight_g"]), 1))
        making = str(int(float(item["making_pct"]) * 100))
        dropped = item["price_dropped"]

        # Image
        img_path = item.get("image_main", "")
        if img_path:
            img_html = (
                '<img src="' + img_url(img_path) + '" '
                'class="wl-card-img" alt="' + name + '" loading="lazy">'
            )
        else:
            img_html = (
                '<div class="wl-card-img-placeholder">'
                '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#B8860B" stroke-width="1">'
                '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>'
                '</svg>'
                '</div>'
            )

        # Price drop badge
        drop_badge = (
            '<span class="wl-price-drop-badge">↓ Price dropped</span>'
            if dropped else ""
        )

        # Price class
        price_cls = "wl-price dropped" if dropped else "wl-price"

        cards_html += (
            '<div class="wl-card">'
            '<div class="wl-card-img-wrap">'
            + img_html +
            '<span class="wl-karat">' + karat + '</span>'
            '<a href="?action=remove_wish&item=' + wid + '" class="wl-remove-x" title="Remove from wishlist">✕</a>'
            + drop_badge +
            '</div>'
            '<div class="wl-card-body">'
            '<div class="wl-cat">' + cat + '</div>'
            '<a href="?_nav=Product&id=' + pid + '" style="color:#1A1008!important;">'
            '<div class="wl-name">' + name + '</div>'
            '</a>'
            '<div class="wl-pills">'
            '<span class="wl-pill">' + metal + ' ' + karat + '</span>'
            '<span class="wl-pill">' + weight + 'g</span>'
            '<span class="wl-pill">Making ' + making + '%</span>'
            '</div>'
            '<div class="wl-divider"></div>'
            '<div class="wl-price-row">'
            '<div>'
            '<div class="' + price_cls + '">' + format_inr(price) + '</div>'
            '<div class="wl-price-sub">'
            + ('Price dropped today' if dropped else 'Live IBJA rate') +
            '</div>'
            '</div>'
            '</div>'
            '<div class="wl-actions">'
            '<a href="?action=move_to_cart&item=' + wid + '&product=' + pid + '" '
            'class="wl-move-btn">Move to Cart</a>'
            '<a href="?action=remove_wish&item=' + wid + '" class="wl-heart-btn" title="Remove">♥</a>'
            '</div>'
            '</div>'
            '</div>'
        )

    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)

    # ── Summary bar ───────────────────────────────────────────
    st.markdown(
        '<div class="wl-sumbar">'
        '<div class="wl-sum-left">'
        '<div class="wl-sum-lbl">Combined wishlist value</div>'
        '<div class="wl-sum-val">' + format_inr(wishlist_total) + '</div>'
        '<div class="wl-sum-note">All prices live &middot; Updated this morning from IBJA</div>'
        '</div>'
        '<a href="?action=add_all" class="wl-add-all">Add All to Cart</a>'
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
    '<li><a href="?_nav=Login" target="_self">Register</a></li>'
    '<li><a href="?_nav=Profile" target="_self">My Orders</a></li>'
    '<li><a href="?_nav=Wishlist" target="_self">Wishlist</a></li>'
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