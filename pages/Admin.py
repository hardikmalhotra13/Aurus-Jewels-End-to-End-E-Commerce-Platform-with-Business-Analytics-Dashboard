"""
pages/Admin.py — Aurus Jewels Admin Panel
Sections: Dashboard · Products · Orders · Gold Rates · Analytics
"""
import streamlit as st
import sys, os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.session        import init_session, require_admin
from core.pricing_engine import get_all_rates, format_inr, invalidate_rate_cache
from database.db         import execute_query, execute_write, execute_one

st.set_page_config(
    page_title            = "Admin — Aurus Jewels",
    page_icon             = "⚙",
    layout                = "wide",
    initial_sidebar_state = "collapsed",
)

init_session()
require_admin()

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

# ── Section state (replaces st.tabs — gives us full control) ──
SECTIONS = ["Dashboard", "Products", "Orders", "Gold Rates", "Analytics"]
if "admin_section" not in st.session_state:
    st.session_state["admin_section"] = "Dashboard"

# Read section from query param (set by HTML tab bar clicks)
_sec = st.query_params.get("section", "")
if _sec and _sec in SECTIONS:
    st.session_state["admin_section"] = _sec
    st.query_params.clear()
    st.rerun()

section = st.session_state["admin_section"]

# ── Session state defaults ────────────────────────────────────
for k, v in [
    ("edit_pid",         None),
    ("show_add_product", False),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Query-param CRUD action handlers ─────────────────────────
action  = st.query_params.get("action", "")
act_id  = st.query_params.get("id",     "")
act_sec = st.query_params.get("section","")

if action == "deactivate_product" and act_id:
    execute_write(
        "UPDATE dim_products SET is_active=0 WHERE product_id=%s", (act_id,)
    )
    st.session_state["admin_section"] = "Products"
    st.query_params.clear(); st.rerun()

if action == "activate_product" and act_id:
    execute_write(
        "UPDATE dim_products SET is_active=1 WHERE product_id=%s", (act_id,)
    )
    st.session_state["admin_section"] = "Products"
    st.query_params.clear(); st.rerun()

if action == "edit_product" and act_id:
    st.session_state["edit_pid"]       = int(act_id)
    st.session_state["admin_section"]  = "Products"
    st.query_params.clear(); st.rerun()

if action == "cancel_edit":
    st.session_state["edit_pid"]       = None
    st.session_state["admin_section"]  = "Products"
    st.query_params.clear(); st.rerun()

if action == "update_order_status" and act_id:
    new_status = st.query_params.get("status", "")
    if new_status in ("pending","confirmed","shipped","delivered","cancelled"):
        execute_write(
            "UPDATE fact_orders SET order_status=%s WHERE order_id=%s",
            (new_status, act_id)
        )
    st.session_state["admin_section"] = "Orders"
    st.query_params.clear(); st.rerun()

# ── Live rates ────────────────────────────────────────────────
rates = get_all_rates()
r22k  = rates.get(("gold",   "22K"),  6850.0)
r18k  = rates.get(("gold",   "18K"),  5600.0)
r925  = rates.get(("silver", "925"),    85.0)

# ── Categories for dropdowns ──────────────────────────────────
categories = execute_query(
    "SELECT * FROM dim_categories ORDER BY display_order"
) or []
cat_map = {c["category_id"]: c["name"] for c in categories}

today_str = date.today().strftime("%d %b %Y")

# ── Plotly theme ──────────────────────────────────────────────
GOLD    = "#B8860B"
GOLD_LT = "#D4A843"
ESP     = "#1A1008"
CREAM   = "#FFF8EE"
MOCHA   = "#8B6914"
BORDER  = "#EDD9A3"
PALETTE = [GOLD, GOLD_LT, ESP, "#EDD9A3", MOCHA, "#F5E6C8", "#5C3420", "#4CAF50"]

def style_fig(fig, height=340, title=""):
    fig.update_layout(
        height=height,
        title_text=title,
        title_font=dict(family="Cormorant Garamond,serif", size=15, color=ESP),
        title_x=0,
        paper_bgcolor="white",
        plot_bgcolor=CREAM,
        font=dict(family="DM Sans,sans-serif", color=ESP, size=11),
        margin=dict(l=16, r=16, t=44 if title else 16, b=16),
        colorway=PALETTE,
        legend=dict(
            bgcolor="rgba(255,253,249,0.9)",
            bordercolor=BORDER, borderwidth=1,
            font=dict(size=10),
        ),
    )
    fig.update_xaxes(
        gridcolor=BORDER, linecolor=BORDER,
        tickfont=dict(size=10, color=MOCHA)
    )
    fig.update_yaxes(
        gridcolor=BORDER, linecolor=BORDER,
        tickfont=dict(size=10, color=MOCHA)
    )
    return fig

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

/* ── Admin Navbar ─────────────────────────────────────────── */
.adm-nav{
  background:#1A1008;padding:0 5%;height:56px;
  display:flex;align-items:center;justify-content:space-between;
}
.adm-logo{
  font-family:'Cormorant Garamond',serif;
  font-size:1.3rem;font-weight:600;color:#D4A843;
  letter-spacing:.2em;display:flex;align-items:center;gap:7px;
}
.adm-logo-d{width:6px;height:6px;background:#D4A843;transform:rotate(45deg);display:inline-block;}
.adm-badge{
  font-family:'DM Sans',sans-serif;
  font-size:.48rem;background:rgba(184,134,11,.22);color:#E8C547;
  border:1px solid rgba(184,134,11,.35);
  padding:3px 10px;border-radius:2px;letter-spacing:.1em;text-transform:uppercase;
  margin-left:10px;
}
.adm-nav-right{display:flex;align-items:center;gap:14px;}
.adm-user{font-family:'DM Sans',sans-serif;font-size:.58rem;color:rgba(255,253,249,.4);}
.adm-store-link{
  font-family:'DM Sans',sans-serif;
  font-size:.54rem;letter-spacing:.1em;text-transform:uppercase;
  border:1px solid rgba(184,134,11,.35);color:#D4A843!important;
  padding:5px 13px;border-radius:2px;transition:all .2s;
}
.adm-store-link:hover{background:rgba(184,134,11,.15);}
.adm-logout{
  font-family:'DM Sans',sans-serif;
  font-size:.54rem;letter-spacing:.1em;text-transform:uppercase;
  color:rgba(255,253,249,.35)!important;padding:5px 13px;
  border:1px solid rgba(255,255,255,.1);border-radius:2px;
}
.adm-logout:hover{color:rgba(255,253,249,.7)!important;}

/* ── Custom tab bar ───────────────────────────────────────── */
.adm-tabs{
  background:#FFF8EE;border-bottom:1.5px solid #EDD9A3;
  display:flex;padding:0 5%;gap:0;
}
.adm-tab{
  font-family:'DM Sans',sans-serif;
  font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;
  color:#8B6914!important;padding:14px 22px;
  border-bottom:2px solid transparent;margin-bottom:-1.5px;
  cursor:pointer;font-weight:500;transition:color .2s;
  text-decoration:none!important;white-space:nowrap;
}
.adm-tab:hover{color:#B8860B!important;}
.adm-tab.on{color:#B8860B!important;border-bottom-color:#B8860B;}

/* ── Page header ──────────────────────────────────────────── */
.adm-page-hdr{
  padding:24px 5% 20px;border-bottom:1px solid #EDD9A3;
  background:#FFFDF9;display:flex;align-items:flex-end;
  justify-content:space-between;
}
.adm-page-over{
  font-family:'DM Sans',sans-serif;font-size:.58rem;color:#B8860B;
  letter-spacing:.22em;text-transform:uppercase;margin-bottom:5px;
  display:flex;align-items:center;gap:8px;
}
.adm-page-over::before{content:'';display:block;width:16px;height:1px;background:#B8860B;}
.adm-page-title{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(1.6rem,2.5vw,2.2rem);font-weight:600;
  color:#1A1008;letter-spacing:.03em;line-height:1.1;
}
.adm-page-sub{font-family:'DM Sans',sans-serif;font-size:.62rem;color:#8B6914;margin-top:3px;}
.btn-primary{
  font-family:'DM Sans',sans-serif;font-size:.58rem;letter-spacing:.12em;
  text-transform:uppercase;background:#B8860B;color:#fff!important;
  padding:8px 18px;border-radius:2px;cursor:pointer;transition:background .2s;
  text-decoration:none!important;
}
.btn-primary:hover{background:#9B7209;}

/* ── KPI cards ────────────────────────────────────────────── */
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:22px 5%;}
.kpi-card{
  background:#fff;border:1px solid #EDD9A3;border-radius:6px;
  padding:20px 22px;border-left:3px solid #B8860B;
}
.kpi-card.warn{border-left-color:#E65100;}
.kpi-card.green{border-left-color:#2E7D32;}
.kpi-lbl{
  font-family:'DM Sans',sans-serif;font-size:.62rem;color:#8B6914;
  letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px;font-weight:500;
}
.kpi-val{
  font-family:'Cormorant Garamond',serif;
  font-size:2.2rem;font-weight:600;color:#1A1008;line-height:1;
}
.kpi-card.warn .kpi-val{color:#E65100;}
.kpi-card.green .kpi-val{color:#2E7D32;}
.kpi-note{font-family:'DM Sans',sans-serif;font-size:.54rem;color:#B8860B;margin-top:6px;}
.kpi-card.warn .kpi-note{color:#E65100;}

/* ── Rate card ────────────────────────────────────────────── */
.rate-ov-card{
  margin:0 5% 20px;background:#fff;border:1px solid #EDD9A3;
  border-radius:6px;padding:18px 22px;
}
.rate-ov-hdr{
  display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;
}
.rate-ov-title{
  font-family:'DM Sans',sans-serif;font-size:.6rem;color:#1A1008;
  letter-spacing:.14em;text-transform:uppercase;font-weight:600;
}
.rate-ov-badge{
  font-family:'DM Sans',sans-serif;font-size:.5rem;
  background:#E8F5E9;color:#2E7D32;padding:3px 9px;border-radius:2px;
}
.rate-ov-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
.rate-ov-item{
  background:#FFF8EE;border:1px solid #EDD9A3;border-radius:4px;padding:13px 15px;
}
.rate-ov-item-lbl{
  font-family:'DM Sans',sans-serif;font-size:.52rem;color:#8B6914;
  letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px;
}
.rate-ov-item-val{
  font-family:'Cormorant Garamond',serif;
  font-size:1.3rem;font-weight:600;color:#B8860B;
}

/* ── Tables ───────────────────────────────────────────────── */
.tbl-wrap{
  margin:0 5% 24px;background:#fff;border:1px solid #EDD9A3;
  border-radius:6px;overflow:hidden;
}
.tbl-toolbar{
  padding:12px 16px;background:#FFF8EE;border-bottom:1px solid #EDD9A3;
  display:flex;align-items:center;justify-content:space-between;gap:12px;
}
.tbl-toolbar-title{
  font-family:'DM Sans',sans-serif;font-size:.68rem;color:#1A1008;
  letter-spacing:.12em;text-transform:uppercase;font-weight:600;
}
table.aj-tbl{width:100%;border-collapse:collapse;}
table.aj-tbl th{
  background:#FFF8EE;color:#8B6914;letter-spacing:.1em;text-transform:uppercase;
  padding:10px 16px;text-align:left;font-family:'DM Sans',sans-serif;
  font-size:.64rem;font-weight:500;border-bottom:1px solid #EDD9A3;
}
table.aj-tbl td{
  padding:10px 16px;color:#1A1008;border-bottom:1px dashed #EDD9A3;
  font-family:'DM Sans',sans-serif;font-size:.78rem;
}
table.aj-tbl tr:last-child td{border-bottom:none;}
table.aj-tbl tr:hover td{background:#FFFDF9;}
.tbl-act{color:#B8860B!important;font-size:.66rem;border-bottom:1px solid rgba(184,134,11,.3);margin-right:10px;}
.tbl-del{color:#9B2335!important;font-size:.66rem;border-bottom:1px solid rgba(155,35,53,.3);}
.tbl-on{color:#2E7D32!important;font-size:.66rem;border-bottom:1px solid rgba(46,125,50,.3);}
.stock-low{color:#E65100;font-weight:600;}
.stock-ok{color:#2E7D32;}

/* ── Status badges ────────────────────────────────────────── */
.st-pending   {background:#FFF3E0;color:#E65100;padding:3px 10px;border-radius:2px;font-size:.62rem;font-family:'DM Sans';}
.st-confirmed {background:#E3F2FD;color:#1565C0;padding:3px 10px;border-radius:2px;font-size:.62rem;font-family:'DM Sans';}
.st-processing{background:#F3E5F5;color:#6A1B9A;padding:3px 10px;border-radius:2px;font-size:.62rem;font-family:'DM Sans';}
.st-shipped   {background:#F3E5F5;color:#6A1B9A;padding:3px 10px;border-radius:2px;font-size:.62rem;font-family:'DM Sans';}
.st-delivered {background:#E8F5E9;color:#1B5E20;padding:3px 10px;border-radius:2px;font-size:.62rem;font-family:'DM Sans';font-weight:600;}
.st-cancelled {background:#FFEBEE;color:#B71C1C;padding:3px 10px;border-radius:2px;font-size:.62rem;font-family:'DM Sans';}
.st-active    {background:#E8F5E9;color:#2E7D32;padding:3px 9px;border-radius:2px;font-size:.52rem;font-family:'DM Sans';}
.st-inactive  {background:#FFEBEE;color:#B71C1C;padding:3px 9px;border-radius:2px;font-size:.52rem;font-family:'DM Sans';}

/* ── Analytics ────────────────────────────────────────────── */
.analytics-pad{padding:22px 5%;}
.chart-sec-title{
  font-family:'DM Sans',sans-serif;font-size:.62rem;color:#B8860B;
  letter-spacing:.2em;text-transform:uppercase;margin-bottom:18px;
  display:flex;align-items:center;gap:8px;margin-top:8px;
}
.chart-sec-title::before{content:'';display:block;width:16px;height:1px;background:#B8860B;}
.insight-box{
  background:#FFF8EE;border:1px solid #EDD9A3;border-radius:6px;
  padding:14px 18px;margin-bottom:22px;
  font-family:'DM Sans',sans-serif;font-size:.78rem;color:#4A3728;line-height:1.75;
}
.insight-box strong{color:#B8860B;}

/* ── Low stock alert ──────────────────────────────────────── */
.alert-box{
  margin:0 5% 20px;background:#FFF3E0;border:1px solid #FFCC80;
  border-left:3px solid #E65100;border-radius:4px;
  padding:12px 18px;font-family:'DM Sans',sans-serif;
  font-size:.66rem;color:#BF360C;line-height:1.65;
}

/* ── Edit banner ──────────────────────────────────────────── */
.edit-banner{
  margin:0 5% 16px;padding:14px 20px;background:#FFF8EE;
  border:1.5px solid #EDD9A3;border-left:3px solid #B8860B;
  border-radius:4px;font-family:'DM Sans',sans-serif;
  font-size:.66rem;color:#8B6914;
}
.edit-banner strong{color:#1A1008;font-size:.76rem;}

/* ── Streamlit overrides ──────────────────────────────────── */
[data-testid="stForm"]{border:none!important;padding:0!important;background:transparent!important;}
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stTextArea textarea{
  border:1.5px solid #E8D5A3!important;border-radius:2px!important;
  background:#FFFDF9!important;color:#1A1008!important;
  font-family:'DM Sans',sans-serif!important;font-size:.82rem!important;
}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus{
  border-color:#B8860B!important;box-shadow:none!important;
}
.stTextInput label,.stNumberInput label,.stSelectbox label,.stTextArea label{
  font-family:'DM Sans',sans-serif!important;font-size:.6rem!important;
  letter-spacing:.12em!important;text-transform:uppercase!important;
  color:#8B6914!important;font-weight:400!important;
}
.stSelectbox>div>div{
  border:1.5px solid #E8D5A3!important;border-radius:2px!important;
  background:#FFFDF9!important;color:#1A1008!important;
  font-family:'DM Sans',sans-serif!important;font-size:.82rem!important;
}
.stButton>button{
  background:#1A1008!important;color:#FFFDF9!important;
  border:none!important;border-radius:2px!important;padding:11px 22px!important;
  font-family:'DM Sans',sans-serif!important;font-size:.64rem!important;
  letter-spacing:.13em!important;text-transform:uppercase!important;
  transition:background .2s!important;
}
.stButton>button:hover{background:#B8860B!important;}
.stCheckbox label{font-family:'DM Sans',sans-serif!important;font-size:.76rem!important;color:#4A3728!important;}
.stExpander{border:1px solid #EDD9A3!important;border-radius:6px!important;background:#FFF8EE!important;}
.stExpander summary{font-family:'DM Sans',sans-serif!important;font-size:.66rem!important;letter-spacing:.1em!important;text-transform:uppercase!important;color:#8B6914!important;}
.stTextInput>div>div>input::placeholder{color:#C8A96A!important;}

@media(max-width:1100px){.kpi-grid{grid-template-columns:repeat(2,1fr);}}
@media(max-width:700px){.kpi-grid{grid-template-columns:1fr;}.rate-ov-grid{grid-template-columns:1fr;}}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# NAVBAR
# ════════════════════════════════════════════════════════════
admin_email = st.session_state.get("email", "admin")
st.markdown(
    '<nav class="adm-nav">'
    '<div style="display:flex;align-items:center;">'
    '<div class="adm-logo">AURUS<span class="adm-logo-d"></span>JEWELS</div>'
    '<span class="adm-badge">Admin Panel</span>'
    '</div>'
    '<div class="adm-nav-right">'
    '<span class="adm-user">Signed in as ' + admin_email + '</span>'
    '<a href="?_nav=Home" class="adm-store-link">View Store</a>'
    '<a href="?_nav=Login" class="adm-logout">Logout</a>'
    '</div>'
    '</nav>',
    unsafe_allow_html=True
)

# ── Custom Tab Bar ────────────────────────────────────────────
tabs_html = '<div class="adm-tabs">'
for s in SECTIONS:
    on = " on" if s == section else ""
    tabs_html += (
        '<a href="?section=' + s + '" target="_self" class="adm-tab' + on + '">' + s + '</a>'
    )
tabs_html += '</div>'
st.markdown(tabs_html, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SECTION: DASHBOARD
# ════════════════════════════════════════════════════════════
if section == "Dashboard":

    st.markdown(
        '<div class="adm-page-hdr">'
        '<div>'
        '<div class="adm-page-over">Overview</div>'
        '<div class="adm-page-title">Dashboard</div>'
        '<div class="adm-page-sub">' + today_str + ' · Live data</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # KPIs
    rev_today_row  = execute_one(
        "SELECT COALESCE(SUM(total_amount),0) AS v FROM fact_orders "
        "WHERE DATE(created_at)=CURDATE() AND order_status!='cancelled'"
    )
    ord_today_row  = execute_one(
        "SELECT COUNT(*) AS v FROM fact_orders WHERE DATE(created_at)=CURDATE()"
    )
    pending_row    = execute_one(
        "SELECT COUNT(*) AS v FROM fact_orders WHERE order_status='pending'"
    )
    low_stock_row  = execute_query(
        "SELECT COUNT(*) AS v FROM dim_products WHERE stock_qty<=3 AND is_active=1"
    )
    new_cust_row   = execute_one(
        "SELECT COUNT(*) AS v FROM dim_customers "
        "WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) AND role='customer'"
    )
    rev_month_row  = execute_one(
        "SELECT COALESCE(SUM(total_amount),0) AS v FROM fact_orders "
        "WHERE MONTH(created_at)=MONTH(CURDATE()) "
        "AND YEAR(created_at)=YEAR(CURDATE()) AND order_status!='cancelled'"
    )

    rev_today  = float(rev_today_row["v"])  if rev_today_row  else 0.0
    ord_today  = int(ord_today_row["v"])    if ord_today_row  else 0
    pend_cnt   = int(pending_row["v"])      if pending_row    else 0
    low_cnt    = int(low_stock_row[0]["v"]) if low_stock_row  else 0
    new_cust   = int(new_cust_row["v"])     if new_cust_row   else 0
    rev_month  = float(rev_month_row["v"])  if rev_month_row  else 0.0

    st.markdown(
        '<div class="kpi-grid">'
        '<div class="kpi-card">'
        '<div class="kpi-lbl">Revenue Today</div>'
        '<div class="kpi-val">' + format_inr(rev_today) + '</div>'
        '<div class="kpi-note">Month: ' + format_inr(rev_month) + '</div>'
        '</div>'
        '<div class="kpi-card">'
        '<div class="kpi-lbl">Orders Today</div>'
        '<div class="kpi-val">' + str(ord_today) + '</div>'
        '<div class="kpi-note">' + str(pend_cnt) + ' pending confirmation</div>'
        '</div>'
        '<div class="kpi-card warn">'
        '<div class="kpi-lbl">Low Stock Alerts</div>'
        '<div class="kpi-val">' + str(low_cnt) + '</div>'
        '<div class="kpi-note">Products at or below 3 units</div>'
        '</div>'
        '<div class="kpi-card green">'
        '<div class="kpi-lbl">New Customers</div>'
        '<div class="kpi-val">' + str(new_cust) + '</div>'
        '<div class="kpi-note">Last 7 days</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Low stock list
    low_prods = execute_query(
        "SELECT sku, name, stock_qty FROM dim_products "
        "WHERE stock_qty<=3 AND is_active=1 ORDER BY stock_qty ASC LIMIT 5"
    ) or []
    if low_prods:
        txt = " &nbsp;|&nbsp; ".join(
            p["sku"] + " — " + p["name"] + " (" + str(p["stock_qty"]) + " left)"
            for p in low_prods
        )
        st.markdown(
            '<div class="alert-box"><strong>Low Stock:</strong> ' + txt + '</div>',
            unsafe_allow_html=True
        )

    # Rate card
    st.markdown(
        '<div class="rate-ov-card">'
        '<div class="rate-ov-hdr">'
        '<span class="rate-ov-title">Today\'s Gold &amp; Silver Rates</span>'
        '<span class="rate-ov-badge">&#9679; Live from IBJA</span>'
        '</div>'
        '<div class="rate-ov-grid">'
        '<div class="rate-ov-item">'
        '<div class="rate-ov-item-lbl">Gold 22K / gram</div>'
        '<div class="rate-ov-item-val">' + format_inr(r22k) + '</div>'
        '</div>'
        '<div class="rate-ov-item">'
        '<div class="rate-ov-item-lbl">Gold 18K / gram</div>'
        '<div class="rate-ov-item-val">' + format_inr(r18k) + '</div>'
        '</div>'
        '<div class="rate-ov-item">'
        '<div class="rate-ov-item-lbl">Silver 925 / gram</div>'
        '<div class="rate-ov-item-val">' + format_inr(r925) + '</div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Recent orders
    recent = execute_query(
        "SELECT o.order_id, c.full_name, o.total_amount, "
        "o.created_at, o.order_status "
        "FROM fact_orders o "
        "JOIN dim_customers c ON o.customer_id=c.customer_id "
        "ORDER BY o.created_at DESC LIMIT 8"
    ) or []

    if recent:
        rows = ""
        for o in recent:
            s     = o["order_status"]
            badge = '<span class="st-' + s + '">' + s.title() + '</span>'
            rows += (
                "<tr>"
                "<td>#" + str(o["order_id"]) + "</td>"
                "<td>" + str(o["full_name"]) + "</td>"
                "<td>" + format_inr(float(o["total_amount"])) + "</td>"
                "<td>" + str(o["created_at"])[:10] + "</td>"
                "<td>" + badge + "</td>"
                "</tr>"
            )
        st.markdown(
            '<div class="tbl-wrap">'
            '<div class="tbl-toolbar">'
            '<span class="tbl-toolbar-title">Recent Orders</span>'
            '</div>'
            '<table class="aj-tbl">'
            '<tr><th>Order</th><th>Customer</th>'
            '<th>Total</th><th>Date</th><th>Status</th></tr>'
            + rows + '</table></div>',
            unsafe_allow_html=True
        )


# ════════════════════════════════════════════════════════════
# SECTION: PRODUCTS
# ════════════════════════════════════════════════════════════
elif section == "Products":

    st.markdown(
        '<div class="adm-page-hdr">'
        '<div>'
        '<div class="adm-page-over">Inventory</div>'
        '<div class="adm-page-title">Products</div>'
        '<div class="adm-page-sub">Full CRUD · 48 products across 5 categories</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Edit form — shown above table when edit_pid is set
    if st.session_state["edit_pid"]:
        ep = execute_one(
            "SELECT * FROM dim_products WHERE product_id=%s",
            (st.session_state["edit_pid"],)
        )
        if ep:
            st.markdown(
                '<div class="edit-banner">'
                'Editing: <strong>' + str(ep["name"]) + '</strong>'
                '</div>',
                unsafe_allow_html=True
            )
            with st.form("edit_product_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    e_name   = st.text_input("Product Name",  value=ep["name"])
                    e_cat    = st.selectbox(
                        "Category",
                        options=list(cat_map.keys()),
                        index=list(cat_map.keys()).index(ep["category_id"])
                        if ep["category_id"] in cat_map else 0,
                        format_func=lambda x: cat_map[x]
                    )
                    e_metal  = st.selectbox(
                        "Metal", ["gold","silver"],
                        index=0 if ep["metal_type"]=="gold" else 1
                    )
                with c2:
                    e_karat  = st.selectbox(
                        "Karat", ["22K","18K","925"],
                        index=["22K","18K","925"].index(ep["karat"])
                        if ep["karat"] in ["22K","18K","925"] else 0
                    )
                    e_weight = st.number_input(
                        "Weight (g)", min_value=0.1, step=0.1,
                        value=float(ep["weight_g"])
                    )
                    e_making = st.number_input(
                        "Making %", min_value=1, max_value=50,
                        value=int(float(ep["making_pct"]) * 100)
                    )
                with c3:
                    e_stock  = st.number_input(
                        "Stock Qty", min_value=0,
                        value=int(ep["stock_qty"])
                    )
                    e_bis    = st.text_input(
                        "BIS Hallmark No",
                        value=ep.get("bis_hallmark_no","") or ""
                    )
                    e_feat   = st.checkbox(
                        "Featured", value=bool(ep.get("is_featured",0))
                    )
                e_desc = st.text_area(
                    "Description",
                    value=ep.get("description","") or "", height=80
                )
                sc1, sc2 = st.columns(2)
                with sc1:
                    save = st.form_submit_button("Save Changes", use_container_width=True)
                with sc2:
                    cancel = st.form_submit_button("Cancel", use_container_width=True)

                if save:
                    execute_write(
                        """UPDATE dim_products SET
                           name=%s, description=%s, category_id=%s,
                           metal_type=%s, karat=%s, weight_g=%s,
                           making_pct=%s, stock_qty=%s,
                           is_featured=%s, bis_hallmark_no=%s
                           WHERE product_id=%s""",
                        (
                            e_name.strip(), e_desc.strip(), e_cat,
                            e_metal, e_karat, e_weight,
                            round(e_making/100, 4), e_stock,
                            1 if e_feat else 0,
                            e_bis.strip(), st.session_state["edit_pid"]
                        )
                    )
                    st.session_state["edit_pid"] = None
                    st.success("Product updated successfully!")
                    st.rerun()
                if cancel:
                    st.session_state["edit_pid"] = None
                    st.rerun()

    # Add product expander
    with st.expander("+ Add New Product"):
        with st.form("add_product_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_sku    = st.text_input("SKU", placeholder="P049")
                new_name   = st.text_input("Product Name")
                new_cat    = st.selectbox(
                    "Category",
                    options=list(cat_map.keys()),
                    format_func=lambda x: cat_map[x]
                )
            with c2:
                new_metal  = st.selectbox("Metal", ["gold","silver"])
                new_karat  = st.selectbox("Karat", ["22K","18K","925"])
                new_weight = st.number_input("Weight (g)", min_value=0.1, step=0.1, value=3.0)
                new_making = st.number_input("Making %", min_value=1, max_value=50, value=12)
            with c3:
                new_stock  = st.number_input("Stock Qty", min_value=0, value=10)
                new_img    = st.text_input("Image Main Path")
                new_img2   = st.text_input("Image 2 Path")
                new_bis    = st.text_input("BIS Hallmark No")
            new_desc = st.text_area("Description", height=80)
            new_feat = st.checkbox("Mark as Featured")
            add_sub  = st.form_submit_button("Add Product", use_container_width=True)

            if add_sub:
                if not new_sku or not new_name:
                    st.error("SKU and product name are required.")
                else:
                    nid = execute_write(
                        """INSERT INTO dim_products
                           (sku, name, description, category_id, metal_type,
                            karat, weight_g, making_pct, stock_qty,
                            image_main, image_2, is_featured, is_active, bis_hallmark_no)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s)""",
                        (
                            new_sku.strip().upper(), new_name.strip(),
                            new_desc.strip(), new_cat, new_metal,
                            new_karat, new_weight, round(new_making/100, 4),
                            new_stock, new_img.strip(), new_img2.strip(),
                            1 if new_feat else 0, new_bis.strip()
                        )
                    )
                    if nid:
                        st.success("Product added!")
                        st.rerun()

    # Search
    search_q = st.text_input(
        "", placeholder="Search by product name or SKU…",
        label_visibility="collapsed"
    )

    products = execute_query(
        "SELECT p.*, c.name AS category_name "
        "FROM dim_products p "
        "JOIN dim_categories c ON p.category_id=c.category_id "
        + ("WHERE p.name LIKE %s OR p.sku LIKE %s " if search_q else "")
        + "ORDER BY p.product_id",
        ("%" + search_q + "%", "%" + search_q + "%") if search_q else ()
    ) or []

    rows = ""
    for p in products:
        stock   = int(p["stock_qty"])
        s_cls   = "stock-low" if stock <= 3 else "stock-ok"
        s_badge = (
            '<span class="st-active">Active</span>'
            if p["is_active"]
            else '<span class="st-inactive">Inactive</span>'
        )
        toggle  = (
            '<a href="?action=deactivate_product&id=' + str(p["product_id"]) + '" class="tbl-del">Deactivate</a>'
            if p["is_active"]
            else '<a href="?action=activate_product&id=' + str(p["product_id"]) + '" class="tbl-on">Activate</a>'
        )
        rows += (
            "<tr>"
            "<td>" + str(p["sku"]) + "</td>"
            "<td>" + str(p["name"]) + "</td>"
            "<td>" + str(p["category_name"]) + "</td>"
            "<td>" + str(p["metal_type"].title()) + " " + str(p["karat"]) + "</td>"
            "<td>" + str(round(float(p["weight_g"]),1)) + "g</td>"
            "<td>" + str(int(float(p["making_pct"])*100)) + "%</td>"
            "<td class='" + s_cls + "'>" + str(stock) + "</td>"
            "<td>" + s_badge + "</td>"
            "<td>"
            "<a href='?action=edit_product&id=" + str(p["product_id"]) + "' class='tbl-act'>Edit</a>"
            + toggle +
            "</td>"
            "</tr>"
        )

    st.markdown(
        '<div class="tbl-wrap">'
        '<div class="tbl-toolbar">'
        '<span class="tbl-toolbar-title">' + str(len(products)) + ' Products</span>'
        '</div>'
        '<table class="aj-tbl">'
        '<tr><th>SKU</th><th>Name</th><th>Category</th>'
        '<th>Metal</th><th>Weight</th><th>Making</th>'
        '<th>Stock</th><th>Status</th><th>Actions</th></tr>'
        + rows + '</table></div>',
        unsafe_allow_html=True
    )


# ════════════════════════════════════════════════════════════
# SECTION: ORDERS
# ════════════════════════════════════════════════════════════
elif section == "Orders":

    st.markdown(
        '<div class="adm-page-hdr">'
        '<div>'
        '<div class="adm-page-over">Operations</div>'
        '<div class="adm-page-title">Orders</div>'
        '<div class="adm-page-sub">Filter · Update status · Track deliveries</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    STATUS_FLOW = {
        "pending":   "confirmed",
        "confirmed": "shipped",
        "shipped":   "delivered",
    }
    STATUS_LABEL = {
        "pending":   "Confirm",
        "confirmed": "Mark Shipped",
        "shipped":   "Mark Delivered",
        "delivered": "—",
        "cancelled": "—",
    }

    filter_opt = st.selectbox(
        "Status",
        ["all","pending","confirmed","shipped","delivered","cancelled"],
        label_visibility="collapsed"
    )

    if filter_opt == "all":
        orders = execute_query(
            "SELECT o.*, c.full_name FROM fact_orders o "
            "JOIN dim_customers c ON o.customer_id=c.customer_id "
            "ORDER BY o.created_at DESC"
        ) or []
    else:
        orders = execute_query(
            "SELECT o.*, c.full_name FROM fact_orders o "
            "JOIN dim_customers c ON o.customer_id=c.customer_id "
            "WHERE o.order_status=%s ORDER BY o.created_at DESC",
            (filter_opt,)
        ) or []

    rows = ""
    for o in orders:
        s     = o["order_status"]
        badge = '<span class="st-' + s + '">' + s.title() + '</span>'
        nxt   = STATUS_FLOW.get(s, "")
        lbl   = STATUS_LABEL.get(s, "—")
        act   = (
            '<a href="?action=update_order_status&id='
            + str(o["order_id"]) + '&status=' + nxt
            + '" class="tbl-act">' + lbl + '</a>'
            if nxt else
            '<span style="color:#C8A96A;font-size:.56rem;">' + lbl + '</span>'
        )
        rows += (
            "<tr>"
            "<td>#" + str(o["order_id"]) + "</td>"
            "<td>" + str(o["full_name"]) + "</td>"
            "<td>" + format_inr(float(o["total_amount"])) + "</td>"
            "<td>" + str(o["created_at"])[:10] + "</td>"
            "<td>" + badge + "</td>"
            "<td>" + act + "</td>"
            "</tr>"
        )

    st.markdown(
        '<div class="tbl-wrap">'
        '<div class="tbl-toolbar">'
        '<span class="tbl-toolbar-title">' + str(len(orders)) + ' Orders</span>'
        '</div>'
        '<table class="aj-tbl">'
        '<tr><th>Order</th><th>Customer</th><th>Total</th>'
        '<th>Date</th><th>Status</th><th>Action</th></tr>'
        + rows + '</table></div>',
        unsafe_allow_html=True
    )


# ════════════════════════════════════════════════════════════
# SECTION: GOLD RATES
# ════════════════════════════════════════════════════════════
elif section == "Gold Rates":

    st.markdown(
        '<div class="adm-page-hdr">'
        '<div>'
        '<div class="adm-page-over">Rate Management</div>'
        '<div class="adm-page-title">Gold &amp; Silver Rates</div>'
        '<div class="adm-page-sub">Manual override · Rate history · IBJA source</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="rate-ov-card" style="margin-top:20px;">'
        '<div class="rate-ov-hdr">'
        '<span class="rate-ov-title">Current Rates — ' + today_str + '</span>'
        '<span class="rate-ov-badge">&#9679; Auto-fetched from IBJA at 9:00 AM</span>'
        '</div>'
        '<div class="rate-ov-grid">'
        '<div class="rate-ov-item"><div class="rate-ov-item-lbl">Gold 22K per gram</div>'
        '<div class="rate-ov-item-val">' + format_inr(r22k) + '</div></div>'
        '<div class="rate-ov-item"><div class="rate-ov-item-lbl">Gold 18K per gram</div>'
        '<div class="rate-ov-item-val">' + format_inr(r18k) + '</div></div>'
        '<div class="rate-ov-item"><div class="rate-ov-item-lbl">Silver 925 per gram</div>'
        '<div class="rate-ov-item-val">' + format_inr(r925) + '</div></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div style="padding:4px 5% 10px;">'
        '<div style="font-family:\'DM Sans\',sans-serif;font-size:.6rem;'
        'color:#1A1008;letter-spacing:.14em;text-transform:uppercase;'
        'font-weight:600;margin-bottom:14px;">Manual Rate Override</div>'
        '</div>',
        unsafe_allow_html=True
    )

    with st.form("rate_override_form"):
        c1, c2, c3, c4 = st.columns([2,2,2,1])
        with c1:
            ov_22k = st.number_input("Gold 22K (₹/g)", min_value=1000.0,
                                     step=10.0, value=float(r22k), format="%.2f")
        with c2:
            ov_18k = st.number_input("Gold 18K (₹/g)", min_value=1000.0,
                                     step=10.0, value=float(r18k), format="%.2f")
        with c3:
            ov_925 = st.number_input("Silver 925 (₹/g)", min_value=10.0,
                                     step=1.0, value=float(r925), format="%.2f")
        with c4:
            st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
            ov_sub = st.form_submit_button("Save Rates", use_container_width=True)

        if ov_sub:
            for metal, karat, rate in [
                ("gold","22K",ov_22k),("gold","18K",ov_18k),("silver","925",ov_925)
            ]:
                execute_write(
                    """INSERT INTO dim_gold_rates
                       (metal_type, karat, rate_per_gram, effective_date, source)
                       VALUES (%s,%s,%s,CURDATE(),'Manual')
                       ON DUPLICATE KEY UPDATE rate_per_gram=%s, source='Manual'""",
                    (metal, karat, rate, rate)
                )
            invalidate_rate_cache()
            st.success("Rates updated! All product prices now reflect new rates.")
            st.rerun()

    hist = execute_query(
        "SELECT effective_date, metal_type, karat, rate_per_gram, source "
        "FROM dim_gold_rates ORDER BY effective_date DESC LIMIT 45"
    ) or []

    if hist:
        rows = ""
        for h in hist:
            rows += (
                "<tr>"
                "<td>" + str(h["effective_date"]) + "</td>"
                "<td>" + str(h["metal_type"]).title() + "</td>"
                "<td>" + str(h["karat"]) + "</td>"
                "<td>" + format_inr(float(h["rate_per_gram"])) + "</td>"
                "<td>" + str(h["source"]) + "</td>"
                "</tr>"
            )
        st.markdown(
            '<div class="tbl-wrap" style="margin-top:8px;">'
            '<div class="tbl-toolbar">'
            '<span class="tbl-toolbar-title">Rate History — Last 45 Records</span>'
            '</div>'
            '<table class="aj-tbl">'
            '<tr><th>Date</th><th>Metal</th><th>Karat</th>'
            '<th>Rate / gram</th><th>Source</th></tr>'
            + rows + '</table></div>',
            unsafe_allow_html=True
        )


# ════════════════════════════════════════════════════════════
# SECTION: ANALYTICS
# ════════════════════════════════════════════════════════════
elif section == "Analytics":

    st.markdown(
        '<div class="adm-page-hdr">'
        '<div>'
        '<div class="adm-page-over">Data Analysis</div>'
        '<div class="adm-page-title">Analytics &amp; Trends</div>'
        '<div class="adm-page-sub">'
        'Sales patterns · Seasonal demand · Gold rate correlation'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="analytics-pad">', unsafe_allow_html=True)

    # ── FIX: Use CONCAT instead of DATE_FORMAT to avoid %% connector issues ──
    rev_monthly_raw = execute_query(
        "SELECT CONCAT(YEAR(created_at),'-',LPAD(MONTH(created_at),2,'0')) AS month, "
        "SUM(total_amount) AS revenue, COUNT(*) AS order_count "
        "FROM fact_orders WHERE order_status!='cancelled' "
        "GROUP BY CONCAT(YEAR(created_at),'-',LPAD(MONTH(created_at),2,'0')) "
        "ORDER BY month"
    ) or []

    rate_hist_raw = execute_query(
        "SELECT effective_date, karat, rate_per_gram "
        "FROM dim_gold_rates ORDER BY effective_date"
    ) or []

    cat_rev_raw = execute_query(
        "SELECT c.name AS category, "
        "SUM(oi.unit_price * oi.quantity) AS revenue "
        "FROM fact_order_items oi "
        "JOIN dim_products p ON oi.product_id=p.product_id "
        "JOIN dim_categories c ON p.category_id=c.category_id "
        "JOIN fact_orders o ON oi.order_id=o.order_id "
        "WHERE o.order_status!='cancelled' "
        "GROUP BY c.name ORDER BY revenue DESC"
    ) or []

    dow_raw = execute_query(
        "SELECT DAYOFWEEK(created_at) AS dow, COUNT(*) AS cnt "
        "FROM fact_orders WHERE order_status!='cancelled' "
        "GROUP BY DAYOFWEEK(created_at) ORDER BY DAYOFWEEK(created_at)"
    ) or []

    qtr_raw = execute_query(
        "SELECT YEAR(created_at) AS yr, QUARTER(created_at) AS qtr, "
        "SUM(total_amount) AS revenue "
        "FROM fact_orders WHERE order_status!='cancelled' "
        "GROUP BY YEAR(created_at), QUARTER(created_at) "
        "ORDER BY YEAR(created_at), QUARTER(created_at)"
    ) or []

    tier_raw = execute_query(
        "SELECT loyalty_tier, COUNT(*) AS cnt "
        "FROM dim_customers WHERE role='customer' "
        "GROUP BY loyalty_tier"
    ) or []

    top_prod_raw = execute_query(
        "SELECT p.name, SUM(oi.unit_price*oi.quantity) AS revenue "
        "FROM fact_order_items oi "
        "JOIN dim_products p ON oi.product_id=p.product_id "
        "JOIN fact_orders o ON oi.order_id=o.order_id "
        "WHERE o.order_status!='cancelled' "
        "GROUP BY p.name ORDER BY revenue DESC LIMIT 8"
    ) or []

    making_raw = execute_query(
        "SELECT c.name AS category, AVG(p.making_pct)*100 AS avg_making "
        "FROM dim_products p "
        "JOIN dim_categories c ON p.category_id=c.category_id "
        "WHERE p.is_active=1 GROUP BY c.name"
    ) or []

    # ── safe month label helper ───────────────────────────────
    def month_label(m):
        """Convert '2025-03' → 'Mar 25' safely."""
        try:
            return datetime(int(m[:4]), int(m[5:7]), 1).strftime("%b %y")
        except Exception:
            return m

    # ── Row 1: Monthly Revenue + Gold Rate Trend ──────────────
    st.markdown('<div class="chart-sec-title">Sales Performance</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if rev_monthly_raw:
            df_rev = pd.DataFrame(rev_monthly_raw)
            df_rev["revenue"]   = df_rev["revenue"].astype(float)
            df_rev["month_lbl"] = df_rev["month"].apply(month_label)

            fig = go.Figure(go.Bar(
                x=df_rev["month_lbl"].tolist(),
                y=df_rev["revenue"].tolist(),
                marker_color=GOLD,
                marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
            ))

            months = df_rev["month"].tolist()
            for ann_m, ann_txt in [
                ("2025-04","Akshaya Tritiya"),
                ("2025-10","Dhanteras"),
                ("2025-11","Diwali + Weddings"),
                ("2025-12","Wedding Season"),
            ]:
                if ann_m in months:
                    idx  = months.index(ann_m)
                    yval = float(df_rev.iloc[idx]["revenue"])
                    fig.add_annotation(
                        x=df_rev.iloc[idx]["month_lbl"],
                        y=yval * 1.05,
                        text=ann_txt,
                        showarrow=True, arrowhead=2,
                        arrowsize=0.8, arrowcolor=MOCHA,
                        font=dict(size=9, color=MOCHA),
                        bgcolor="rgba(255,248,238,0.9)",
                        bordercolor=BORDER, borderwidth=1,
                        ax=0, ay=-28,
                    )

            style_fig(fig, height=340, title="Monthly Revenue (₹)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No order data. Run the SQL UPDATE for created_at dates first.")

    with col2:
        if rate_hist_raw:
            df_rates = pd.DataFrame(rate_hist_raw)
            df_rates["rate_per_gram"] = df_rates["rate_per_gram"].astype(float)
            df_rates["effective_date"] = pd.to_datetime(df_rates["effective_date"])

            fig2 = px.line(
                df_rates, x="effective_date", y="rate_per_gram", color="karat",
                color_discrete_map={"22K":GOLD,"18K":GOLD_LT,"925":MOCHA},
                markers=True,
                labels={"effective_date":"Date","rate_per_gram":"₹/gram","karat":"Karat"},
            )
            fig2.update_traces(marker_size=5)
            style_fig(fig2, height=340, title="Gold & Silver Rate Trend")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No rate history data.")

    st.markdown(
        '<div class="insight-box">'
        '<strong>Key Insight:</strong> Revenue peaks sharply during '
        '<strong>Dhanteras (Oct)</strong> and <strong>the wedding season (Nov–Jan)</strong> '
        'even as gold rates rise — confirming that jewellery demand in India is '
        '<strong>event-driven, not price-sensitive</strong>. '
        'Monsoon months (Jun–Aug) show the lowest sales despite lower gold rates.'
        '</div>',
        unsafe_allow_html=True
    )

    # ── Row 2: Revenue vs Rate + Category ────────────────────
    st.markdown('<div class="chart-sec-title">Correlation &amp; Distribution</div>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        if rev_monthly_raw and rate_hist_raw:
            df_rev2 = pd.DataFrame(rev_monthly_raw)
            df_rev2["revenue"] = df_rev2["revenue"].astype(float)
            df_rev2["date"] = df_rev2["month"].apply(
                lambda m: datetime(int(m[:4]), int(m[5:7]), 1)
            )

            df_22k = pd.DataFrame(rate_hist_raw)
            df_22k = df_22k[df_22k["karat"]=="22K"].copy()
            df_22k["rate_per_gram"] = df_22k["rate_per_gram"].astype(float)
            df_22k["date"] = pd.to_datetime(df_22k["effective_date"])
            df_22k["month_dt"] = df_22k["date"].apply(
                lambda d: datetime(d.year, d.month, 1)
            )

            merged = pd.merge(df_rev2, df_22k[["month_dt","rate_per_gram"]],
                              left_on="date", right_on="month_dt", how="inner")

            if not merged.empty:
                lbl = merged["month"].apply(month_label).tolist()
                fig3 = go.Figure()
                fig3.add_trace(go.Bar(
                    x=lbl, y=merged["revenue"].tolist(),
                    name="Revenue (₹)", marker_color=GOLD,
                    marker_line_width=0, yaxis="y",
                    hovertemplate="Revenue: ₹%{y:,.0f}<extra></extra>",
                ))
                fig3.add_trace(go.Scatter(
                    x=lbl, y=merged["rate_per_gram"].tolist(),
                    name="Gold 22K (₹/g)",
                    line=dict(color=ESP, width=2.5),
                    yaxis="y2",
                    hovertemplate="Rate: ₹%{y:.0f}/g<extra></extra>",
                ))
                fig3.update_layout(
                    yaxis2=dict(
                        overlaying="y", side="right",
                        tickfont=dict(size=9, color=MOCHA),
                        gridcolor=BORDER,
                    )
                )
                style_fig(fig3, height=340, title="Revenue vs Gold Rate")
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Not enough data for correlation chart.")
        else:
            st.info("No data.")

    with col4:
        if cat_rev_raw:
            df_cat = pd.DataFrame(cat_rev_raw)
            df_cat["revenue"] = df_cat["revenue"].astype(float)
            fig4 = px.pie(
                df_cat, values="revenue", names="category", hole=0.45,
                color_discrete_sequence=[GOLD,GOLD_LT,MOCHA,"#EDD9A3","#F5E6C8"],
            )
            fig4.update_traces(
                textfont_size=11,
                hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<extra></extra>",
            )
            style_fig(fig4, height=340, title="Revenue by Category")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No order data.")

    # ── Row 3: Quarterly + Day of Week ───────────────────────
    st.markdown('<div class="chart-sec-title">Seasonal &amp; Timing Patterns</div>', unsafe_allow_html=True)

    col5, col6 = st.columns(2)

    with col5:
        if qtr_raw:
            df_qtr = pd.DataFrame(qtr_raw)
            df_qtr["revenue"] = df_qtr["revenue"].astype(float)
            df_qtr["label"]   = "Q" + df_qtr["qtr"].astype(str) + " " + df_qtr["yr"].astype(str)
            fig5 = go.Figure(go.Bar(
                x=df_qtr["label"].tolist(),
                y=df_qtr["revenue"].tolist(),
                marker_color=[
                    ESP if ("Q4" in l or "Q1" in l) else GOLD
                    for l in df_qtr["label"].tolist()
                ],
                marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
            ))
            style_fig(fig5, height=320, title="Quarterly Revenue")
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No data.")

    with col6:
        DAY_NAMES = {1:"Sun",2:"Mon",3:"Tue",4:"Wed",5:"Thu",6:"Fri",7:"Sat"}
        if dow_raw:
            df_dow = pd.DataFrame(dow_raw)
            df_dow["day_name"] = df_dow["dow"].map(DAY_NAMES)
            df_dow["cnt"]      = df_dow["cnt"].astype(int)
            day_order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            df_dow = (
                df_dow.set_index("day_name").reindex(day_order)
                .fillna(0).reset_index()
            )
            df_dow.columns = ["day_name","dow","cnt"]

            fig6 = go.Figure(go.Bar(
                x=df_dow["day_name"].tolist(),
                y=df_dow["cnt"].tolist(),
                marker_color=[
                    ESP if d in ("Sat","Sun") else GOLD
                    for d in df_dow["day_name"].tolist()
                ],
                marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>%{y} orders<extra></extra>",
            ))
            style_fig(fig6, height=320, title="Orders by Day of Week")
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("No data.")

    # ── Row 4: Top Products + Loyalty Tiers ──────────────────
    st.markdown('<div class="chart-sec-title">Products &amp; Customers</div>', unsafe_allow_html=True)

    col7, col8 = st.columns(2)

    with col7:
        if top_prod_raw:
            df_top = pd.DataFrame(top_prod_raw)
            df_top["revenue"] = df_top["revenue"].astype(float)
            df_top = df_top.sort_values("revenue")
            fig7 = go.Figure(go.Bar(
                x=df_top["revenue"].tolist(),
                y=df_top["name"].tolist(),
                orientation="h",
                marker_color=GOLD, marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>",
            ))
            style_fig(fig7, height=340, title="Top Products by Revenue")
            st.plotly_chart(fig7, use_container_width=True)
        else:
            st.info("No data.")

    with col8:
        if tier_raw:
            df_tier = pd.DataFrame(tier_raw)
            df_tier["cnt"] = df_tier["cnt"].astype(int)
            TIER_COLORS = {
                "member":"#D3D1C7","silver":"#BDBDBD",
                "gold":GOLD,"platinum":"#546E7A"
            }
            df_tier["color"] = df_tier["loyalty_tier"].map(TIER_COLORS).fillna(GOLD_LT)
            fig8 = go.Figure(go.Pie(
                labels=df_tier["loyalty_tier"].str.title().tolist(),
                values=df_tier["cnt"].tolist(),
                hole=0.45,
                marker_colors=df_tier["color"].tolist(),
                hovertemplate="<b>%{label}</b><br>%{value} customers<extra></extra>",
            ))
            style_fig(fig8, height=340, title="Customer Loyalty Tiers")
            st.plotly_chart(fig8, use_container_width=True)
        else:
            st.info("No customer data.")

    # Making charge
    if making_raw:
        df_mkg = pd.DataFrame(making_raw)
        df_mkg["avg_making"] = df_mkg["avg_making"].astype(float).round(1)
        df_mkg = df_mkg.sort_values("avg_making")
        fig9 = go.Figure(go.Bar(
            x=df_mkg["avg_making"].tolist(),
            y=df_mkg["category"].tolist(),
            orientation="h",
            marker_color=GOLD_LT, marker_line_width=0,
            text=[str(v)+"%" for v in df_mkg["avg_making"].tolist()],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Avg making: %{x:.1f}%<extra></extra>",
        ))
        style_fig(fig9, height=260, title="Avg Making Charge by Category (%)")
        st.plotly_chart(fig9, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)