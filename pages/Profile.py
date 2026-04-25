"""
pages/Profile.py — Aurus Jewels Customer Profile
4 tabs: My Orders | Addresses | Loyalty & Rewards | Account Settings
"""
import streamlit as st
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.session        import init_session, require_login
from core.pricing_engine import format_inr, get_all_rates
from database.db         import execute_query, execute_write, execute_one

try:
    import bcrypt
except ImportError:
    bcrypt = None

st.set_page_config(
    page_title            = "My Account — Aurus Jewels",
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

# ── Navigation ────────────────────────────────────────────────
PAGE_MAP = {
    "Home":"Home.py","Catalogue":"pages/Catalogue.py","Product":"pages/Product.py",
    "Cart":"pages/Cart.py","Checkout":"pages/Checkout.py","Profile":"pages/Profile.py",
    "Login":"pages/Login.py","Admin":"pages/Admin.py","Wishlist":"pages/Wishlist.py",
}
_nav = st.query_params.get("_nav","")
if _nav and _nav in PAGE_MAP:
    st.query_params.clear()
    st.switch_page(PAGE_MAP[_nav])

# ── Tab state ─────────────────────────────────────────────────
TABS = ["My Orders", "Addresses", "Loyalty & Rewards", "Account Settings"]
if "profile_tab" not in st.session_state:
    st.session_state["profile_tab"] = "My Orders"

_tab = st.query_params.get("tab","")
if _tab and _tab in TABS:
    st.session_state["profile_tab"] = _tab
    st.query_params.clear(); st.rerun()

tab = st.session_state["profile_tab"]

# ── Action handlers ───────────────────────────────────────────
action = st.query_params.get("action","")
act_id = st.query_params.get("id","")

if action == "logout":
    for k in ["logged_in","customer_id","email","full_name","role","loyalty_tier"]:
        st.session_state.pop(k, None)
    # Clear cookie
    try:
        from streamlit_extras.stoggle import stoggle
    except Exception:
        pass
    try:
        import extra_streamlit_components as stx
        cm = stx.CookieManager()
        cm.delete("aurus_token")
    except Exception:
        pass
    st.query_params.clear()
    st.switch_page("Home.py")

if action == "delete_address" and act_id:
    execute_write("DELETE FROM dim_addresses WHERE address_id=%s AND customer_id=%s",(act_id,cid))
    st.session_state["profile_tab"] = "Addresses"
    st.query_params.clear(); st.rerun()

if action == "set_default_address" and act_id:
    execute_write("UPDATE dim_addresses SET is_default=0 WHERE customer_id=%s",(cid,))
    execute_write("UPDATE dim_addresses SET is_default=1 WHERE address_id=%s AND customer_id=%s",(act_id,cid))
    st.session_state["profile_tab"] = "Addresses"
    st.query_params.clear(); st.rerun()

# ── Order filter ──────────────────────────────────────────────
if "order_filter" not in st.session_state:
    st.session_state["order_filter"] = "All"
_of = st.query_params.get("filter","")
if _of:
    st.session_state["order_filter"] = _of
    st.session_state["profile_tab"]  = "My Orders"
    st.query_params.clear(); st.rerun()

# ── Address edit state ────────────────────────────────────────
if "edit_addr_id" not in st.session_state:
    st.session_state["edit_addr_id"] = None
if "show_add_addr" not in st.session_state:
    st.session_state["show_add_addr"] = False
_ea = st.query_params.get("edit_addr","")
if _ea:
    st.session_state["edit_addr_id"]  = int(_ea)
    st.session_state["profile_tab"]   = "Addresses"
    st.query_params.clear(); st.rerun()
_aa = st.query_params.get("add_addr","")
if _aa == "1":
    st.session_state["show_add_addr"] = True
    st.session_state["profile_tab"]   = "Addresses"
    st.query_params.clear(); st.rerun()

# ── DB helpers ────────────────────────────────────────────────
def img_url(p):
    if not p: return ""
    return p.replace("\\","/").replace("static/","/app/static/")

customer = execute_one(
    "SELECT full_name, email, phone, loyalty_tier, total_spend FROM dim_customers WHERE customer_id=%s",(cid,)
)
if not customer:
    st.switch_page("pages/Login.py")

db_name  = str(customer.get("full_name",""))
db_email = str(customer.get("email",""))
db_phone = str(customer.get("phone","") or "")
db_tier  = str(customer.get("loyalty_tier","member"))
db_spend = float(customer.get("total_spend") or 0)

# Navbar counts
cart_row = execute_one("SELECT COUNT(*) AS c FROM customer_cart WHERE customer_id=%s",(cid,))
cart_count = int(cart_row["c"]) if cart_row else 0
wish_row = execute_one("SELECT COUNT(*) AS c FROM customer_wishlist WHERE customer_id=%s",(cid,))
wish_count = int(wish_row["c"]) if wish_row else 0
order_row = execute_one("SELECT COUNT(*) AS c FROM fact_orders WHERE customer_id=%s",(cid,))
order_count = int(order_row["c"]) if order_row else 0

# Avatar initials
def initials(name):
    parts = name.strip().split()
    if len(parts) >= 2: return (parts[0][0]+parts[-1][0]).upper()
    return name[:2].upper() if name else "HM"

# Tier display
TIER_INFO = {
    "member":   {"label":"Member",   "disc":"0%",  "color":"#8B6914",  "next":"Silver",   "next_at":50000},
    "silver":   {"label":"Silver",   "disc":"3%",  "color":"#888780",  "next":"Gold",     "next_at":150000},
    "gold":     {"label":"Gold",     "disc":"5%",  "color":"#B8860B",  "next":"Platinum", "next_at":500000},
    "platinum": {"label":"Platinum", "disc":"5% + Free shipping", "color":"#B0BEC5", "next":None, "next_at":None},
}
ti = TIER_INFO.get(db_tier, TIER_INFO["member"])

# Live rates
rates = get_all_rates()
r22k = rates.get(("gold","22K"),6850.0)
r18k = rates.get(("gold","18K"),5600.0)
r925 = rates.get(("silver","925"),85.0)

badge_count = cart_count + wish_count

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
.aj-btn-logout{font-family:'DM Sans',sans-serif;font-size:.58rem;letter-spacing:.12em;text-transform:uppercase;border:1.5px solid #9B2335;color:#9B2335!important;padding:6px 13px;border-radius:2px;transition:all .2s;}
.aj-btn-logout:hover{background:#9B2335;color:#fff!important;}

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

/* ── PROFILE HERO ────────────────────────────────────────── */
.pf-hero{background:#1A1008;padding:28px 5%;display:flex;align-items:center;gap:22px;}
.pf-avatar{width:60px;height:60px;border-radius:50%;background:#B8860B;display:flex;align-items:center;justify-content:center;font-family:'Cormorant Garamond',serif;font-size:1.4rem;font-weight:600;color:#FFFDF9;border:2.5px solid #D4A843;flex-shrink:0;}
.pf-hero-info{flex:1;}
.pf-hero-name{font-family:'Cormorant Garamond',serif;font-size:1.4rem;font-weight:600;color:#D4A843;letter-spacing:.04em;margin-bottom:4px;}
.pf-hero-email{font-family:'DM Sans',sans-serif;font-size:.64rem;color:rgba(255,253,249,.4);margin-bottom:8px;}
.pf-hero-badges{display:flex;gap:8px;align-items:center;}
.pf-tier-badge{font-family:'DM Sans',sans-serif;font-size:.56rem;font-weight:600;letter-spacing:.1em;padding:3px 12px;border-radius:2px;background:rgba(184,134,11,.22);color:#E8C547;border:1px solid rgba(184,134,11,.4);}
.pf-orders-badge{font-family:'DM Sans',sans-serif;font-size:.56rem;color:rgba(255,253,249,.35);background:rgba(255,253,249,.07);padding:3px 12px;border-radius:2px;}
.pf-hero-right{text-align:right;}
.pf-spend-lbl{font-family:'DM Sans',sans-serif;font-size:.52rem;color:rgba(255,253,249,.3);letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px;}
.pf-spend-val{font-family:'DM Sans',sans-serif;font-size:1.1rem;font-weight:700;color:#D4A843;}

/* ── TAB BAR ─────────────────────────────────────────────── */
.pf-tabs{background:#FFF8EE;border-bottom:1px solid #EDD9A3;display:flex;padding:0 5%;}
.pf-tab{font-family:'DM Sans',sans-serif;font-size:.64rem;letter-spacing:.1em;text-transform:uppercase;padding:14px 18px;color:#8B6914!important;border-bottom:2.5px solid transparent;white-space:nowrap;transition:all .2s;}
.pf-tab:hover{color:#B8860B!important;}
.pf-tab.on{color:#1A1008!important;border-bottom-color:#B8860B;font-weight:600;}

/* ── CONTENT WRAPPER ─────────────────────────────────────── */
.pf-content{padding:28px 5% 40px;}

/* ── ORDER FILTER PILLS ──────────────────────────────────── */
.ord-filters{display:flex;gap:8px;margin-bottom:22px;flex-wrap:wrap;}
.ord-pill{font-family:'DM Sans',sans-serif;font-size:.58rem;letter-spacing:.08em;text-transform:uppercase;padding:6px 16px;border-radius:2px;border:1px solid #EDD9A3;color:#8B6914!important;transition:all .2s;}
.ord-pill:hover{border-color:#B8860B;color:#B8860B!important;}
.ord-pill.on{background:#1A1008;color:#FFFDF9!important;border-color:#1A1008;}

/* ── ORDER CARD ──────────────────────────────────────────── */
.ord-card{background:#fff;border:1px solid #EDD9A3;border-radius:8px;padding:18px 20px;margin-bottom:14px;transition:border-color .2s;}
.ord-card:hover{border-color:#D4A843;}
.ord-card-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px;}
.ord-id{font-family:'DM Sans',sans-serif;font-size:.72rem;font-weight:600;color:#1A1008;margin-bottom:3px;}
.ord-date{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;}
.ord-status{font-family:'DM Sans',sans-serif;font-size:.56rem;padding:3px 10px;border-radius:2px;font-weight:600;white-space:nowrap;}
.ord-delivered{background:#E8F5E9;color:#1B5E20;}
.ord-shipped{background:#E3F2FD;color:#0D47A1;}
.ord-confirmed{background:#FFF8EE;color:#B8860B;border:1px solid #EDD9A3;}
.ord-pending{background:#FFF3E0;color:#E65100;}
.ord-cancelled{background:#FFEBEE;color:#B71C1C;}

.ord-items-list{border-top:1px dashed #EDD9A3;border-bottom:1px dashed #EDD9A3;padding:12px 0;margin-bottom:14px;display:flex;flex-direction:column;gap:10px;}
.ord-item{display:flex;align-items:center;gap:12px;}
.ord-img{width:44px;height:44px;border-radius:5px;overflow:hidden;background:#F5E6C8;flex-shrink:0;border:1px solid #EDD9A3;}
.ord-img img{width:100%;height:100%;object-fit:cover;}
.ord-item-name{font-family:'DM Sans',sans-serif;font-size:.68rem;color:#1A1008;font-weight:500;margin-bottom:2px;}
.ord-item-sub{font-family:'DM Sans',sans-serif;font-size:.58rem;color:#8B6914;}

.ord-bottom{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;}
.ord-total-lbl{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;margin-bottom:3px;}
.ord-total-val{font-family:'DM Sans',sans-serif;font-size:.9rem;font-weight:700;color:#B8860B;}
.ord-actions{display:flex;gap:8px;}
.ord-btn{font-family:'DM Sans',sans-serif;font-size:.58rem;letter-spacing:.08em;text-transform:uppercase;padding:7px 14px;border-radius:2px;white-space:nowrap;}
.ord-btn-outline{border:1px solid #EDD9A3;color:#4A3728!important;}
.ord-btn-outline:hover{border-color:#B8860B;color:#B8860B!important;}
.ord-btn-dark{background:#1A1008;color:#FFFDF9!important;border:none;transition:background .2s;}
.ord-btn-dark:hover{background:#B8860B;}

.ord-empty{text-align:center;padding:56px 0;}
.ord-empty-icon{font-size:2.4rem;margin-bottom:14px;}
.ord-empty-title{font-family:'Cormorant Garamond',serif;font-size:1.4rem;color:#1A1008;margin-bottom:6px;}
.ord-empty-sub{font-family:'DM Sans',sans-serif;font-size:.7rem;color:#8B6914;margin-bottom:20px;}
.ord-empty-cta{font-family:'DM Sans',sans-serif;font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;background:#1A1008;color:#FFFDF9!important;padding:11px 24px;border-radius:2px;display:inline-block;}
.ord-empty-cta:hover{background:#B8860B;}

/* ── ADDRESS GRID ────────────────────────────────────────── */
.addr-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-bottom:20px;}
@media(max-width:900px){.addr-grid{grid-template-columns:1fr 1fr;}}
.addr-card{background:#fff;border:1.5px solid #EDD9A3;border-radius:8px;padding:16px 18px;position:relative;transition:border-color .2s;}
.addr-card:hover{border-color:#D4A843;}
.addr-card.default{border-color:#B8860B;}
.addr-default-badge{position:absolute;top:12px;right:12px;font-family:'DM Sans',sans-serif;font-size:.52rem;background:#FFF8EE;color:#B8860B;border:1px solid #EDD9A3;padding:2px 8px;border-radius:2px;font-weight:600;letter-spacing:.08em;}
.addr-lbl{font-family:'DM Sans',sans-serif;font-size:.58rem;letter-spacing:.14em;text-transform:uppercase;color:#B8860B;margin-bottom:6px;font-weight:600;}
.addr-name{font-family:'DM Sans',sans-serif;font-size:.78rem;color:#1A1008;font-weight:600;margin-bottom:5px;}
.addr-txt{font-family:'DM Sans',sans-serif;font-size:.68rem;color:#8B6914;line-height:1.65;margin-bottom:12px;}
.addr-btn-row{display:flex;gap:8px;flex-wrap:wrap;}
.addr-btn{font-family:'DM Sans',sans-serif;font-size:.54rem;letter-spacing:.08em;text-transform:uppercase;padding:5px 12px;border-radius:2px;}
.addr-btn-edit{border:1px solid #EDD9A3;color:#4A3728!important;}
.addr-btn-edit:hover{border-color:#B8860B;color:#B8860B!important;}
.addr-btn-default{border:1px solid #EDD9A3;color:#8B6914!important;}
.addr-btn-default:hover{border-color:#B8860B;color:#B8860B!important;}
.addr-btn-del{border:1px solid rgba(155,35,53,.25);color:#9B2335!important;}
.addr-btn-del:hover{background:#FFEBEE;}
.addr-add{border:1.5px dashed #EDD9A3;border-radius:8px;padding:28px 18px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;cursor:pointer;transition:border-color .2s;background:#FFFDF9;}
.addr-add:hover{border-color:#B8860B;}
.addr-add-icon{width:26px;height:26px;border-radius:50%;border:1.5px solid #B8860B;display:flex;align-items:center;justify-content:center;font-size:1rem;color:#B8860B;}
.addr-add-txt{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#B8860B;letter-spacing:.1em;text-transform:uppercase;}

/* ── LOYALTY ─────────────────────────────────────────────── */
.loy-hero{background:#1A1008;border-radius:8px;padding:20px 24px;margin-bottom:18px;display:flex;align-items:center;justify-content:space-between;}
.loy-left{}
.loy-tier-lbl{font-family:'DM Sans',sans-serif;font-size:.58rem;color:rgba(255,253,249,.35);letter-spacing:.14em;text-transform:uppercase;margin-bottom:5px;}
.loy-tier-name{font-family:'Cormorant Garamond',serif;font-size:1.5rem;font-weight:600;color:#D4A843;margin-bottom:5px;}
.loy-tier-disc{font-family:'DM Sans',sans-serif;font-size:.64rem;color:rgba(255,253,249,.5);}
.loy-right{text-align:right;}
.loy-spend-lbl{font-family:'DM Sans',sans-serif;font-size:.52rem;color:rgba(255,253,249,.3);letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px;}
.loy-spend-val{font-family:'DM Sans',sans-serif;font-size:1.1rem;font-weight:700;color:#D4A843;}

.loy-progress{margin-bottom:18px;}
.loy-prog-hdr{display:flex;justify-content:space-between;margin-bottom:8px;}
.loy-prog-lbl{font-family:'DM Sans',sans-serif;font-size:.64rem;color:#8B6914;}
.loy-prog-val{font-family:'DM Sans',sans-serif;font-size:.64rem;color:#B8860B;font-weight:600;}
.loy-prog-track{height:7px;background:#EDD9A3;border-radius:4px;overflow:hidden;margin-bottom:6px;}
.loy-prog-note{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;}

.loy-tiers-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:18px;}
.loy-tier-card{border:1px solid #EDD9A3;border-radius:6px;padding:12px 14px;text-align:center;}
.loy-tier-card.active{border-color:#B8860B;background:#FFF8EE;}
.loy-tier-dot{width:10px;height:10px;border-radius:50%;margin:0 auto 6px;}
.loy-tier-name2{font-family:'DM Sans',sans-serif;font-size:.66rem;color:#1A1008;font-weight:600;margin-bottom:3px;}
.loy-tier-thresh{font-family:'DM Sans',sans-serif;font-size:.56rem;color:#8B6914;margin-bottom:4px;}
.loy-tier-disc2{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#B8860B;font-weight:600;}

.loy-benefits{background:#FFF8EE;border:1px solid #EDD9A3;border-radius:8px;padding:18px 20px;}
.loy-ben-title{font-family:'DM Sans',sans-serif;font-size:.68rem;color:#1A1008;font-weight:600;letter-spacing:.12em;text-transform:uppercase;margin-bottom:12px;}
.loy-ben-row{display:flex;align-items:center;gap:10px;margin-bottom:9px;}
.loy-ben-check{width:18px;height:18px;border-radius:50%;background:#2E7D32;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.loy-ben-tick{width:8px;height:5px;border-left:2px solid #fff;border-bottom:2px solid #fff;transform:rotate(-45deg);margin-top:-2px;}
.loy-ben-txt{font-family:'DM Sans',sans-serif;font-size:.7rem;color:#4A3728;}

/* ── SETTINGS ────────────────────────────────────────────── */
.set-section{background:#fff;border:1px solid #EDD9A3;border-radius:8px;padding:20px 22px;margin-bottom:16px;}
.set-sec-title{font-family:'DM Sans',sans-serif;font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:#1A1008;font-weight:600;margin-bottom:16px;padding-bottom:10px;border-bottom:2px solid #B8860B;}

/* Streamlit form overrides */
[data-testid="stForm"]{border:none!important;padding:0!important;background:transparent!important;}
.stTextInput>div>div>input{border:1.5px solid #E8D5A3!important;border-radius:3px!important;background:#FFFDF9!important;color:#1A1008!important;font-family:'DM Sans',sans-serif!important;font-size:.82rem!important;padding:10px 12px!important;}
.stTextInput>div>div>input:focus{border-color:#B8860B!important;box-shadow:none!important;}
.stTextInput label{font-family:'DM Sans',sans-serif!important;font-size:.62rem!important;letter-spacing:.1em!important;text-transform:uppercase!important;color:#8B6914!important;font-weight:400!important;}
.stSelectbox>div>div{border:1.5px solid #E8D5A3!important;border-radius:3px!important;background:#FFFDF9!important;font-family:'DM Sans',sans-serif!important;font-size:.82rem!important;}
.stSelectbox label{font-family:'DM Sans',sans-serif!important;font-size:.62rem!important;letter-spacing:.1em!important;text-transform:uppercase!important;color:#8B6914!important;font-weight:400!important;}
.stCheckbox label{font-family:'DM Sans',sans-serif!important;font-size:.7rem!important;color:#4A3728!important;}
.stButton>button{background:#1A1008!important;color:#FFFDF9!important;border:none!important;border-radius:2px!important;padding:11px 22px!important;font-family:'DM Sans',sans-serif!important;font-size:.66rem!important;letter-spacing:.14em!important;text-transform:uppercase!important;transition:background .2s!important;width:100%!important;}
.stButton>button:hover{background:#B8860B!important;}
.stSuccess{font-family:'DM Sans',sans-serif!important;font-size:.7rem!important;}

.set-danger{background:#FFF5F5;border:1.5px solid #FFCDD2;border-radius:8px;padding:18px 22px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;}
.set-danger-info{}
.set-danger-lbl{font-family:'DM Sans',sans-serif;font-size:.72rem;color:#9B2335;font-weight:600;margin-bottom:4px;}
.set-danger-sub{font-family:'DM Sans',sans-serif;font-size:.64rem;color:#C62828;opacity:.7;}
.set-danger-btn{font-family:'DM Sans',sans-serif;font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;padding:8px 18px;border-radius:2px;border:1.5px solid #9B2335;color:#9B2335!important;transition:all .2s;}
.set-danger-btn:hover{background:#9B2335;color:#fff!important;}

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
badge  = '<span class="aj-badge">'+str(cart_count)+'</span>' if cart_count > 0 else ""
wbadge = '<span class="aj-badge">'+str(wish_count)+'</span>' if wish_count > 0 else ""
admin_btn = '<a href="?_nav=Admin" target="_self" class="aj-btn-logout" style="border-color:#B8860B;color:#B8860B!important;margin-right:4px;">Admin</a>' if role=="admin" else ""

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
    '<a href="?_nav=Wishlist" target="_self" class="aj-icon">&#9825;'+wbadge+'</a>'
    '<a href="?_nav=Cart"     target="_self" class="aj-icon">&#128722;'+badge+'</a>'
    '<a href="?_nav=Profile"  target="_self" class="aj-icon">&#128100;</a>'
    + admin_btn +
    '<a href="?action=logout" target="_self" class="aj-btn-logout">Sign Out</a>'
    '</div></nav>',
    unsafe_allow_html=True
)

# ── Ticker ────────────────────────────────────────────────────
st.markdown(
    '<div class="aj-ticker"><div class="aj-ticker-items">'
    '<div class="aj-ti"><span class="aj-ti-l">Gold 22K</span>'
    '<span class="aj-ti-v">'+format_inr(r22k)+'</span><span class="aj-ti-u">/g</span></div>'
    '<div class="aj-ti"><span class="aj-ti-l">Gold 18K</span>'
    '<span class="aj-ti-v">'+format_inr(r18k)+'</span><span class="aj-ti-u">/g</span></div>'
    '<div class="aj-ti"><span class="aj-ti-l">Silver 925</span>'
    '<span class="aj-ti-v">'+format_inr(r925)+'</span><span class="aj-ti-u">/g</span></div>'
    '</div><div class="aj-tr"><div class="aj-ld"></div>'
    '<span class="aj-lt">Live IBJA &middot; Updates 9 AM daily</span>'
    '<span class="aj-bis-pill">BIS Hallmarked</span></div></div>',
    unsafe_allow_html=True
)

# ── Profile Hero ──────────────────────────────────────────────
st.markdown(
    '<div class="pf-hero">'
    '<div class="pf-avatar">'+initials(db_name)+'</div>'
    '<div class="pf-hero-info">'
    '<div class="pf-hero-name">'+db_name+'</div>'
    '<div class="pf-hero-email">'+db_email+'</div>'
    '<div class="pf-hero-badges">'
    '<span class="pf-tier-badge">&#9733; '+ti["label"]+' Member</span>'
    '<span class="pf-orders-badge">'+str(order_count)+' Order'+('' if order_count==1 else 's')+'</span>'
    '</div>'
    '</div>'
    '<div class="pf-hero-right">'
    '<div class="pf-spend-lbl">Lifetime Spend</div>'
    '<div class="pf-spend-val">'+format_inr(db_spend)+'</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ── Tab bar ───────────────────────────────────────────────────
tabs_html = '<div class="pf-tabs">'
for t in TABS:
    on = " on" if t == tab else ""
    tabs_html += '<a href="?tab='+t+'" target="_self" class="pf-tab'+on+'">'+t+'</a>'
tabs_html += '</div>'
st.markdown(tabs_html, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TAB 1 — MY ORDERS
# ════════════════════════════════════════════════════════════
if tab == "My Orders":
    st.markdown('<div class="pf-content">', unsafe_allow_html=True)

    STATUS_MAP = {
        "pending"  : ("Pending",   "ord-pending"),
        "confirmed": ("Confirmed", "ord-confirmed"),
        "processing":("Processing","ord-confirmed"),
        "shipped"  : ("Shipped",   "ord-shipped"),
        "delivered": ("Delivered", "ord-delivered"),
        "cancelled": ("Cancelled", "ord-cancelled"),
    }

    # Filter pills
    of = st.session_state["order_filter"]
    filters_html = '<div class="ord-filters">'
    for f in ["All","Confirmed","Shipped","Delivered","Cancelled"]:
        on = " on" if of == f else ""
        filters_html += '<a href="?filter='+f+'" target="_self" class="ord-pill'+on+'">'+f+'</a>'
    filters_html += '</div>'
    st.markdown(filters_html, unsafe_allow_html=True)

    # Fetch orders
    if of == "All":
        orders = execute_query(
            "SELECT * FROM fact_orders WHERE customer_id=%s ORDER BY created_at DESC",(cid,)
        ) or []
    else:
        orders = execute_query(
            "SELECT * FROM fact_orders WHERE customer_id=%s AND order_status=%s ORDER BY created_at DESC",
            (cid, of.lower())
        ) or []

    if not orders:
        st.markdown(
            '<div class="ord-empty">'
            '<div class="ord-empty-icon">&#128722;</div>'
            '<div class="ord-empty-title">No orders yet</div>'
            '<div class="ord-empty-sub">Your completed orders will appear here.</div>'
            '<a href="?_nav=Catalogue" target="_self" class="ord-empty-cta">Start Shopping</a>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        for order in orders:
            oid    = order["order_id"]
            inv_no = str(order.get("invoice_number") or ("AJ-"+str(oid)))
            status = str(order.get("order_status","confirmed")).lower()
            s_label, s_cls = STATUS_MAP.get(status, ("Confirmed","ord-confirmed"))
            total  = float(order.get("total_amount",0))
            created= order.get("created_at")
            date_s = created.strftime("%d %b %Y") if hasattr(created,"strftime") else str(created)[:10]

            # Order items
            items = execute_query(
                "SELECT oi.product_name, oi.karat, oi.metal_type, oi.quantity, "
                "p.image_main FROM fact_order_items oi "
                "LEFT JOIN dim_products p ON oi.product_id=p.product_id "
                "WHERE oi.order_id=%s LIMIT 3", (oid,)
            ) or []

            items_html = '<div class="ord-items-list">'
            for it in items:
                img_tag = ('<img src="'+img_url(it["image_main"])+'" style="width:100%;height:100%;object-fit:cover;">' if it.get("image_main") else "")
                items_html += (
                    '<div class="ord-item">'
                    '<div class="ord-img">'+img_tag+'</div>'
                    '<div><div class="ord-item-name">'+str(it["product_name"])+'</div>'
                    '<div class="ord-item-sub">'+str(it["karat"])+' '+str(it["metal_type"]).title()+' &middot; Qty '+str(it["quantity"])+'</div>'
                    '</div></div>'
                )
            items_html += '</div>'

            inv_path = order.get("invoice_path","")
            dl_btn = (
                '<a href="?tab=My+Orders" target="_self" class="ord-btn ord-btn-dark">&#8595; Invoice</a>'
                if inv_path else
                '<span class="ord-btn" style="background:#F5E6C8;color:#8B6914;font-family:\'DM Sans\',sans-serif;font-size:.54rem;letter-spacing:.08em;text-transform:uppercase;padding:7px 14px;border-radius:2px;">&#8595; Invoice</span>'
            )

            st.markdown(
                '<div class="ord-card">'
                '<div class="ord-card-top">'
                '<div><div class="ord-id">Order #'+inv_no+'</div>'
                '<div class="ord-date">'+date_s+'</div></div>'
                '<span class="ord-status '+s_cls+'">'+s_label+'</span>'
                '</div>'
                + items_html +
                '<div class="ord-bottom">'
                '<div><div class="ord-total-lbl">Order Total</div>'
                '<div class="ord-total-val">'+format_inr(total)+'</div></div>'
                '<div class="ord-actions">'
                '<a href="?tab=My+Orders" target="_self" class="ord-btn ord-btn-outline">View Details</a>'
                + dl_btn +
                '</div></div>'
                '</div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TAB 2 — ADDRESSES
# ════════════════════════════════════════════════════════════
elif tab == "Addresses":
    st.markdown('<div class="pf-content">', unsafe_allow_html=True)

    addresses = execute_query(
        "SELECT * FROM dim_addresses WHERE customer_id=%s ORDER BY is_default DESC, address_id DESC",(cid,)
    ) or []

    # Address cards
    cards_html = '<div class="addr-grid">'
    for addr in addresses:
        aid  = str(addr["address_id"])
        dflt = bool(addr.get("is_default"))
        dflt_badge = '<span class="addr-default-badge">Default</span>' if dflt else ""
        dflt_btn   = "" if dflt else '<a href="?action=set_default_address&id='+aid+'" target="_self" class="addr-btn addr-btn-default">Set Default</a>'
        line2 = (", "+str(addr["address_line2"])) if addr.get("address_line2") else ""

        cards_html += (
            '<div class="addr-card'+(" default" if dflt else "")+'">'
            + dflt_badge +
            '<div class="addr-lbl">'+str(addr.get("label","Home"))+'</div>'
            '<div class="addr-name">'+str(addr.get("full_name",""))+'</div>'
            '<div class="addr-txt">'
            +str(addr.get("address_line1",""))+line2
            +'<br>'+str(addr.get("city",""))+', '+str(addr.get("state",""))+' &ndash; '+str(addr.get("pincode",""))
            +'<br>'+str(addr.get("phone",""))
            +'</div>'
            '<div class="addr-btn-row">'
            '<a href="?edit_addr='+aid+'" target="_self" class="addr-btn addr-btn-edit">Edit</a>'
            + dflt_btn +
            '<a href="?action=delete_address&id='+aid+'" target="_self" class="addr-btn addr-btn-del">Remove</a>'
            '</div></div>'
        )
    cards_html += (
        '<a href="?add_addr=1" target="_self" class="addr-add">'
        '<div class="addr-add-icon">+</div>'
        '<div class="addr-add-txt">Add New Address</div>'
        '</a>'
        '</div>'
    )
    st.markdown(cards_html, unsafe_allow_html=True)

    # Edit/Add form
    edit_id = st.session_state.get("edit_addr_id")
    show_add = st.session_state.get("show_add_addr", False)

    if edit_id or show_add:
        edit_data = execute_one("SELECT * FROM dim_addresses WHERE address_id=%s AND customer_id=%s",(edit_id,cid)) if edit_id else None
        form_title = "Edit Address" if edit_id else "Add New Address"

        st.markdown(
            '<div style="background:#fff;border:1px solid #EDD9A3;border-radius:8px;padding:20px 22px;margin-top:4px;">'
            '<div style="font-family:\'DM Sans\',sans-serif;font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:#1A1008;font-weight:600;margin-bottom:16px;padding-bottom:10px;border-bottom:2px solid #B8860B;">'+form_title+'</div>',
            unsafe_allow_html=True
        )
        with st.form("addr_form"):
            c1, c2 = st.columns(2)
            with c1:
                a_name  = st.text_input("Full Name",       value=str(edit_data["full_name"]  if edit_data else ""))
                a_line1 = st.text_input("Address Line 1",  value=str(edit_data["address_line1"] if edit_data else ""))
                a_city  = st.text_input("City",            value=str(edit_data["city"]        if edit_data else ""))
            with c2:
                a_phone = st.text_input("Phone",           value=str(edit_data["phone"]       if edit_data else ""))
                a_line2 = st.text_input("Address Line 2 (optional)", value=str(edit_data.get("address_line2","") or "" if edit_data else ""))
                a_state = st.text_input("State",           value=str(edit_data["state"]       if edit_data else ""))
            c3, c4 = st.columns(2)
            with c3:
                a_pin   = st.text_input("Pincode", value=str(edit_data["pincode"] if edit_data else ""))
            with c4:
                a_label = st.selectbox("Label",["Home","Work","Other"],
                    index=["Home","Work","Other"].index(edit_data.get("label","Home")) if edit_data and edit_data.get("label") in ["Home","Work","Other"] else 0)
            a_default = st.checkbox("Set as default address", value=bool(edit_data.get("is_default")) if edit_data else False)
            save = st.form_submit_button("Save Address", use_container_width=True)
            cancel = st.form_submit_button("Cancel", use_container_width=False)

            if cancel:
                st.session_state["edit_addr_id"] = None
                st.session_state["show_add_addr"] = False
                st.rerun()

            if save:
                if not a_name or not a_line1 or not a_city or not a_state or not a_pin or not a_phone:
                    st.error("Please fill all required fields.")
                else:
                    if a_default:
                        execute_write("UPDATE dim_addresses SET is_default=0 WHERE customer_id=%s",(cid,))
                    if edit_id:
                        execute_write(
                            "UPDATE dim_addresses SET label=%s,full_name=%s,phone=%s,"
                            "address_line1=%s,address_line2=%s,city=%s,state=%s,pincode=%s,is_default=%s "
                            "WHERE address_id=%s AND customer_id=%s",
                            (a_label,a_name.strip(),a_phone.strip(),a_line1.strip(),
                             a_line2.strip() or None,a_city.strip(),a_state.strip(),a_pin.strip(),
                             1 if a_default else 0, edit_id, cid)
                        )
                    else:
                        execute_write(
                            "INSERT INTO dim_addresses (customer_id,label,full_name,phone,"
                            "address_line1,address_line2,city,state,pincode,is_default) "
                            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (cid,a_label,a_name.strip(),a_phone.strip(),a_line1.strip(),
                             a_line2.strip() or None,a_city.strip(),a_state.strip(),a_pin.strip(),
                             1 if a_default else 0)
                        )
                    st.session_state["edit_addr_id"]  = None
                    st.session_state["show_add_addr"] = False
                    st.success("Address saved!")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TAB 3 — LOYALTY & REWARDS
# ════════════════════════════════════════════════════════════
elif tab == "Loyalty & Rewards":
    st.markdown('<div class="pf-content">', unsafe_allow_html=True)

    # Tier hero card
    st.markdown(
        '<div class="loy-hero">'
        '<div class="loy-left">'
        '<div class="loy-tier-lbl">Current Tier</div>'
        '<div class="loy-tier-name">&#9733; '+ti["label"]+' Member</div>'
        '<div class="loy-tier-disc">'+ti["disc"]+' loyalty discount on every order</div>'
        '</div>'
        '<div class="loy-right">'
        '<div class="loy-spend-lbl">Total Spend</div>'
        '<div class="loy-spend-val">'+format_inr(db_spend)+'</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Progress bar
    if ti["next"]:
        next_at  = ti["next_at"]
        PREV = {"silver":50000,"gold":150000,"platinum":500000,"member":0}
        prev_at  = PREV.get(db_tier, 0)
        range_   = next_at - prev_at
        progress = min(100, int((db_spend - prev_at) / range_ * 100)) if range_ > 0 else 100
        remaining = max(0, next_at - db_spend)

        st.markdown(
            '<div class="loy-progress">'
            '<div class="loy-prog-hdr">'
            '<span class="loy-prog-lbl">Progress to '+ti["next"]+'</span>'
            '<span class="loy-prog-val">'+format_inr(db_spend)+' / '+format_inr(next_at)+'</span>'
            '</div>'
            '<div class="loy-prog-track">'
            '<div style="height:100%;background:#B8860B;border-radius:4px;width:'+str(progress)+'%;"></div>'
            '</div>'
            '<div class="loy-prog-note">'+format_inr(remaining)+' more to reach '+ti["next"]+'</div>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="loy-progress">'
            '<div class="loy-prog-hdr"><span class="loy-prog-lbl">You\'ve reached the highest tier!</span></div>'
            '<div class="loy-prog-track"><div style="height:100%;background:#B8860B;border-radius:4px;width:100%;"></div></div>'
            '</div>',
            unsafe_allow_html=True
        )

    # 4-tier grid
    TIER_GRID = [
        ("member",   "Member",   "Default", "0%",             "#8B6914"),
        ("silver",   "Silver",   "₹50K+",   "3% off",         "#9E9E9E"),
        ("gold",     "Gold",     "₹1.5L+",  "5% off",         "#B8860B"),
        ("platinum", "Platinum", "₹5L+",    "5% + Free ship",  "#B0BEC5"),
    ]
    grid = '<div class="loy-tiers-grid">'
    for key,name,thresh,disc,dot_col in TIER_GRID:
        active = " active" if key==db_tier else ""
        grid += (
            '<div class="loy-tier-card'+active+'">'
            '<div class="loy-tier-dot" style="background:'+dot_col+';"></div>'
            '<div class="loy-tier-name2">'+name+'</div>'
            '<div class="loy-tier-thresh">'+thresh+'</div>'
            '<div class="loy-tier-disc2">'+disc+'</div>'
            '</div>'
        )
    grid += '</div>'
    st.markdown(grid, unsafe_allow_html=True)

    # Benefits
    benefits = [
        ti["disc"]+" loyalty discount applied automatically at checkout",
        "GST-compliant invoice on every order",
        "BIS hallmarked jewellery guarantee",
        "Free delivery on all orders across India",
    ]
    if db_tier == "platinum":
        benefits.insert(0, "Free shipping on every order")
    if db_tier in ("gold","platinum"):
        benefits.append("Priority customer support")

    ben_html = '<div class="loy-benefits"><div class="loy-ben-title">Your '+ti["label"]+' Member Benefits</div>'
    for b in benefits:
        ben_html += (
            '<div class="loy-ben-row">'
            '<div class="loy-ben-check"><div class="loy-ben-tick"></div></div>'
            '<div class="loy-ben-txt">'+b+'</div>'
            '</div>'
        )
    ben_html += '</div>'
    st.markdown(ben_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TAB 4 — ACCOUNT SETTINGS
# ════════════════════════════════════════════════════════════
elif tab == "Account Settings":
    st.markdown('<div class="pf-content">', unsafe_allow_html=True)

    # ── Personal Info ─────────────────────────────────────────
    st.markdown(
        '<div class="set-section">'
        '<div class="set-sec-title">Personal Information</div>',
        unsafe_allow_html=True
    )
    with st.form("personal_form"):
        c1, c2 = st.columns(2)
        with c1:
            new_name  = st.text_input("Full Name", value=db_name)
        with c2:
            new_phone = st.text_input("Phone Number", value=db_phone)
        save_personal = st.form_submit_button("Save Changes", use_container_width=True)
        if save_personal:
            if not new_name.strip():
                st.error("Name cannot be empty.")
            else:
                execute_write(
                    "UPDATE dim_customers SET full_name=%s, phone=%s WHERE customer_id=%s",
                    (new_name.strip(), new_phone.strip(), cid)
                )
                st.session_state["full_name"] = new_name.strip()
                st.success("Profile updated successfully!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Change Password ───────────────────────────────────────
    st.markdown(
        '<div class="set-section">'
        '<div class="set-sec-title">Change Password</div>',
        unsafe_allow_html=True
    )
    with st.form("password_form"):
        c1, c2 = st.columns(2)
        with c1:
            old_pw  = st.text_input("Current Password", type="password")
        with c2:
            new_pw  = st.text_input("New Password", type="password", placeholder="Min 8 characters")
        conf_pw = st.text_input("Confirm New Password", type="password", placeholder="Re-enter new password")
        save_pw = st.form_submit_button("Update Password", use_container_width=True)
        if save_pw:
            if not old_pw or not new_pw or not conf_pw:
                st.error("Please fill all password fields.")
            elif new_pw != conf_pw:
                st.error("New passwords do not match.")
            elif len(new_pw) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                row = execute_one("SELECT password_hash FROM dim_customers WHERE customer_id=%s",(cid,))
                if row and bcrypt:
                    valid = bcrypt.checkpw(old_pw.encode(), row["password_hash"].encode() if isinstance(row["password_hash"],str) else row["password_hash"])
                    if valid:
                        new_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt(12)).decode()
                        execute_write("UPDATE dim_customers SET password_hash=%s WHERE customer_id=%s",(new_hash,cid))
                        st.success("Password updated successfully!")
                    else:
                        st.error("Current password is incorrect.")
                else:
                    st.error("Could not verify password. Please try again.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Danger Zone ───────────────────────────────────────────
    st.markdown(
        '<div class="set-danger">'
        '<div class="set-danger-info">'
        '<div class="set-danger-lbl">Delete Account</div>'
        '<div class="set-danger-sub">This will permanently remove your account and all order history.</div>'
        '</div>'
        '<a href="?action=logout" target="_self" class="set-danger-btn">Delete Account</a>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════
st.markdown(
    '<div class="aj-footer"><div class="aj-fg">'
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
    '<li><a href="?tab=My+Orders" target="_self">My Orders</a></li>'
    '<li><a href="?tab=Addresses" target="_self">Addresses</a></li>'
    '<li><a href="?_nav=Wishlist" target="_self">Wishlist</a></li>'
    '<li><a href="?action=logout" target="_self">Sign Out</a></li>'
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
    '</div></div>',
    unsafe_allow_html=True
)