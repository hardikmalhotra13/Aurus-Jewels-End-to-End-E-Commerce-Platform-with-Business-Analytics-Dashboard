"""
pages/Cart.py — Aurus Jewels Shopping Cart
"""
import streamlit as st
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.session        import init_session, is_logged_in, get_role, get_loyalty_tier
from core.pricing_engine import get_all_rates, format_inr, price_product
from database.db         import execute_query, execute_write

st.set_page_config(
    page_title            = "Cart — Aurus Jewels",
    page_icon             = "✦",
    layout                = "wide",
    initial_sidebar_state = "collapsed",
)

init_session()

PAGE_MAP = {
    "Home":"Home.py","Catalogue":"pages/Catalogue.py","Product":"pages/Product.py",
    "Cart":"pages/Cart.py","Checkout":"pages/Checkout.py","Profile":"pages/Profile.py",
    "Login":"pages/Login.py","Admin":"pages/Admin.py","Wishlist":"pages/Wishlist.py",
}
_nav = st.query_params.get("_nav","")
if _nav and _nav in PAGE_MAP:
    st.query_params.clear()
    st.switch_page(PAGE_MAP[_nav])

if not is_logged_in():
    st.switch_page("pages/Login.py")

cid  = st.session_state.get("customer_id")
role = get_role()
tier = get_loyalty_tier()

action  = st.query_params.get("action","")
item_id = st.query_params.get("item","")

if action == "qty_up" and item_id:
    # Check available stock before incrementing
    stock_check = execute_query(
        "SELECT cc.quantity, p.stock_qty FROM customer_cart cc "
        "JOIN dim_products p ON cc.product_id=p.product_id "
        "WHERE cc.cart_id=%s AND cc.customer_id=%s",
        (item_id, cid)
    )
    if stock_check:
        current_qty = int(stock_check[0]["quantity"])
        available   = int(stock_check[0]["stock_qty"])
        if current_qty < available:
            execute_write("UPDATE customer_cart SET quantity=quantity+1 WHERE cart_id=%s AND customer_id=%s",(item_id,cid))
        # else: silently cap at stock_qty — UI will show OUT OF STOCK indicator
    st.query_params.clear(); st.rerun()

if action == "qty_down" and item_id:
    row = execute_query("SELECT quantity FROM customer_cart WHERE cart_id=%s AND customer_id=%s",(item_id,cid))
    if row:
        if int(row[0]["quantity"]) > 1:
            execute_write("UPDATE customer_cart SET quantity=quantity-1 WHERE cart_id=%s AND customer_id=%s",(item_id,cid))
        else:
            execute_write("DELETE FROM customer_cart WHERE cart_id=%s AND customer_id=%s",(item_id,cid))
    st.query_params.clear(); st.rerun()

if action == "remove" and item_id:
    execute_write("DELETE FROM customer_cart WHERE cart_id=%s AND customer_id=%s",(item_id,cid))
    st.query_params.clear(); st.rerun()

for k,v in [("promo_applied",None),("promo_discount",0.0),("promo_msg",""),("promo_msg_type","")]:
    if k not in st.session_state: st.session_state[k]=v

PROMO_CODES = {
    "AURUS10" :{"type":"pct", "value":10, "label":"10% off"},
    "WELCOME5":{"type":"pct", "value":5,  "label":"5% off"},
    "FLAT500" :{"type":"flat","value":500,"label":"₹500 off"},
}

cart_items = execute_query(
    """SELECT cc.cart_id,cc.quantity,p.*,c.name AS category_name,c.slug
       FROM customer_cart cc
       JOIN dim_products p ON cc.product_id=p.product_id
       JOIN dim_categories c ON p.category_id=c.category_id
       WHERE cc.customer_id=%s AND p.is_active=1
       ORDER BY cc.cart_id DESC""",
    (cid,)
) or []

rates = get_all_rates()
r22k  = rates.get(("gold","22K"),6850.0)
r18k  = rates.get(("gold","18K"),5600.0)
r925  = rates.get(("silver","925"),85.0)

def img_url(p):
    return p.replace("\\","/").replace("static/","/app/static/")

items_priced=[]
grand_subtotal=0.0
for it in cart_items:
    pr=price_product(it); qty=int(it["quantity"])
    available=int(it.get("stock_qty",999))
    out_of_stock=(available==0)
    qty_exceeds=(qty>available and available>0)
    lt=round(pr["final_price"]*qty,2); grand_subtotal+=lt
    items_priced.append({**it,"pr":pr,"line_total":lt,"available":available,"out_of_stock":out_of_stock,"qty_exceeds":qty_exceeds})

TIER_DISC={"member":0,"silver":3,"gold":5,"platinum":5}
loyalty_pct=TIER_DISC.get(tier,0)
loyalty_disc=round(grand_subtotal*loyalty_pct/100,2)
promo_disc=float(st.session_state["promo_discount"])
total_payable=max(0.0,round(grand_subtotal-loyalty_disc-promo_disc,2))
total_items=sum(int(i["quantity"]) for i in cart_items)
cart_count=total_items
w=execute_query("SELECT COUNT(*) AS t FROM customer_wishlist WHERE customer_id=%s",(cid,))
wish_count=int(w[0]["t"]) if w else 0

# ════════════════════════════════════════════════════════════
# CSS — <base> MUST be separate from <style>
# ════════════════════════════════════════════════════════════
st.markdown('<base target="_parent">', unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

#MainMenu,footer,header{display:none!important;}
.stApp{background:#FFFDF9!important;}
[data-testid="stAppViewContainer"]>.main{padding:0!important;}
[data-testid="stHeader"]{display:none!important;}
section[data-testid="stSidebar"]{display:none!important;}
.block-container{padding:0!important;max-width:100%!important;}
.element-container{margin:0!important;width:100%!important;}
div[data-testid="stVerticalBlock"]>div{gap:0!important;}
*{box-sizing:border-box;}
a{text-decoration:none!important;}

[data-testid="stHorizontalBlock"]{gap:0!important;align-items:flex-start!important;}
[data-testid="stHorizontalBlock"]>div{padding:0!important;}
[data-testid="stHorizontalBlock"]>div:last-child{padding-left:2%!important;}
[data-testid="stHorizontalBlock"]>div:first-child{background:#FFFDF9;}

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
.aj-icon{font-size:1.05rem;color:#4A3728;display:flex;align-items:center;justify-content:center;width:26px;height:26px;position:relative;transition:color .2s;}
.aj-icon:hover{color:#B8860B;}
.aj-badge{position:absolute;top:-5px;right:-6px;background:#9B2335;color:#fff;font-size:.44rem;font-weight:700;border-radius:50%;width:13px;height:13px;display:flex;align-items:center;justify-content:center;}
.aj-btn-ac{font-family:'DM Sans',sans-serif;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;border:1.5px solid #B8860B;color:#B8860B!important;padding:6px 12px;border-radius:2px;transition:all .2s;}
.aj-btn-ac:hover{background:#B8860B;color:#fff!important;}

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

/* ── PAGE HEADER — centred ───────────────────────────────── */
.cart-hdr{padding:32px 5% 26px;border-bottom:1px solid #EDD9A3;text-align:center;position:relative;background:#FFFDF9;}
.cart-hdr-over{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#B8860B;letter-spacing:.26em;text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;justify-content:center;gap:12px;}
.cart-hdr-over::before,.cart-hdr-over::after{content:'';display:block;width:32px;height:1px;background:#EDD9A3;}
.cart-hdr-title{font-family:'Cormorant Garamond',serif;font-style:italic;font-size:clamp(1.8rem,3vw,2.6rem);font-weight:600;color:#1A1008;letter-spacing:.04em;line-height:1.1;margin-bottom:10px;}
.cart-hdr-sub{font-family:'DM Sans',sans-serif;font-size:.66rem;color:#8B6914;}
.cart-continue{position:absolute;right:5%;top:50%;transform:translateY(-50%);font-family:'DM Sans',sans-serif;font-size:.62rem;color:#8B6914!important;border-bottom:1px solid #EDD9A3;padding-bottom:2px;transition:color .2s;white-space:nowrap;}
.cart-continue:hover{color:#B8860B!important;border-bottom-color:#B8860B;}

/* ── EMPTY STATE ─────────────────────────────────────────── */
.empty-cart{text-align:center;padding:72px 5% 80px;}
.empty-icon{font-size:2.8rem;margin-bottom:16px;}
.empty-title{font-family:'Cormorant Garamond',serif;font-size:1.7rem;font-weight:500;color:#1A1008;margin-bottom:8px;}
.empty-sub{font-family:'DM Sans',sans-serif;font-size:.76rem;color:#8B6914;line-height:1.75;margin-bottom:26px;max-width:420px;margin-left:auto;margin-right:auto;}
.empty-cta{font-family:'DM Sans',sans-serif;font-size:.66rem;letter-spacing:.15em;text-transform:uppercase;background:#1A1008;color:#FFFDF9!important;padding:13px 30px;border-radius:2px;display:inline-block;transition:background .2s;}
.empty-cta:hover{background:#B8860B;}

/* ── ITEMS COLUMN ────────────────────────────────────────── */
.cart-items-col{padding:28px 32px 40px;}
.live-rate-note{display:flex;align-items:flex-start;gap:8px;background:#FFF8EE;border:1px solid #EDD9A3;border-radius:4px;padding:11px 15px;margin-bottom:18px;max-width:580px;}
.lrn-dot{width:6px;height:6px;border-radius:50%;background:#4CAF50;flex-shrink:0;margin-top:3px;}
.lrn-txt{font-family:'DM Sans',sans-serif;font-size:.68rem;color:#8B6914;line-height:1.65;}

/* ── ITEM CARD ───────────────────────────────────────────── */
.cart-item{background:#fff;border:1px solid #EDD9A3;border-radius:8px;padding:16px;display:flex;gap:14px;margin-bottom:12px;max-width:580px;}
.cart-item:last-child{margin-bottom:0;}
.ci-img{width:86px;height:86px;border-radius:6px;overflow:hidden;position:relative;flex-shrink:0;background:linear-gradient(135deg,#F5E6C8,#EDD9A3);}
.ci-img img{width:100%;height:100%;object-fit:cover;display:block;}
.ci-karat{position:absolute;top:6px;left:6px;font-family:'DM Sans',sans-serif;font-size:.5rem;letter-spacing:.08em;background:#1A1008;color:#E8C547;padding:2px 7px;border-radius:2px;font-weight:500;}
.ci-info{flex:1;min-width:0;}
.ci-cat{font-family:'DM Sans',sans-serif;font-size:.58rem;color:#B8860B;letter-spacing:.16em;text-transform:uppercase;font-weight:500;margin-bottom:3px;}
.ci-name{font-family:'Cormorant Garamond',serif;font-size:1.1rem;font-weight:500;color:#1A1008;line-height:1.25;margin-bottom:8px;}
.ci-pills{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:10px;}
.ci-pill{font-family:'DM Sans',sans-serif;font-size:.56rem;background:#F5E6C8;color:#8B6914;padding:3px 8px;border-radius:2px;font-weight:500;}
.ci-bis{font-family:'DM Sans',sans-serif;font-size:.56rem;background:#E8F5E9;color:#2E7D32;padding:3px 8px;border-radius:2px;font-weight:500;}
.ci-divider{height:1px;background:#F0E4C4;margin-bottom:10px;}
.ci-breakdown{display:flex;flex-direction:column;gap:4px;margin-bottom:12px;}
.ci-br-row{display:flex;justify-content:space-between;align-items:center;}
.ci-br-lbl{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;}
.ci-br-val{font-family:'DM Sans',sans-serif;font-size:.62rem;color:#4A3728;font-weight:500;}
.ci-footer{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;}
.qty-wrap{display:flex;align-items:center;border:1px solid #EDD9A3;border-radius:2px;overflow:hidden;flex-shrink:0;}
.qty-btn{width:32px;height:32px;background:#FFFDF9;display:inline-flex;align-items:center;justify-content:center;font-size:1rem;color:#4A3728!important;text-decoration:none!important;transition:background .2s;font-weight:500;line-height:1;}
.qty-btn:hover{background:#F5E6C8;color:#B8860B!important;}
.qty-val{width:36px;height:32px;background:#fff;border-left:1px solid #EDD9A3;border-right:1px solid #EDD9A3;display:inline-flex;align-items:center;justify-content:center;font-family:'DM Sans',sans-serif;font-size:.74rem;font-weight:600;color:#1A1008;}
.ci-total{font-family:'DM Sans',sans-serif;font-size:1.1rem;font-weight:700;color:#B8860B;white-space:nowrap;}
.ci-multi{font-family:'DM Sans',sans-serif;font-size:.58rem;color:#8B6914;font-weight:400;}
.ci-remove{font-family:'DM Sans',sans-serif;font-size:.58rem;color:#9B2335;border-bottom:1px solid rgba(155,35,53,.3);padding-bottom:1px;text-decoration:none!important;transition:color .2s;white-space:nowrap;}
.ci-remove:hover{color:#7A1828!important;}
.ci-oos-badge{font-family:'DM Sans',sans-serif;font-size:.52rem;background:#FFEBEE;color:#B71C1C;border:1px solid #FFCDD2;padding:3px 9px;border-radius:2px;font-weight:600;letter-spacing:.06em;display:inline-block;margin-bottom:8px;}
.ci-qty-warn{font-family:'DM Sans',sans-serif;font-size:.54rem;color:#E65100;margin-top:4px;display:flex;align-items:center;gap:4px;}
.qty-btn.disabled{opacity:.35;pointer-events:none;cursor:not-allowed;}

/* ── ORDER SUMMARY ───────────────────────────────────────── */
.sum-wrap{padding:22px 24px 28px 28px;background:transparent;}
.sum-title{font-family:'Cormorant Garamond',serif;font-size:1.45rem;font-weight:600;color:#1A1008;padding-bottom:14px;border-bottom:2px solid #B8860B;margin-bottom:18px;letter-spacing:.04em;font-style:italic;}
.sum-rows{display:flex;flex-direction:column;margin-bottom:18px;}
.sum-row{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px dashed #EDD9A3;}
.sum-row:last-child{border-bottom:none;}
.sum-lbl{font-family:'DM Sans',sans-serif;font-size:.72rem;color:#8B6914;}
.sum-val{font-family:'DM Sans',sans-serif;font-size:.72rem;color:#1A1008;font-weight:500;}
.sum-val.disc{color:#2E7D32;}
.sum-val.free{color:#2E7D32;font-weight:600;}
.tier-badge{font-family:'DM Sans',sans-serif;font-size:.5rem;background:#F5E6C8;color:#B8860B;padding:1px 6px;border-radius:2px;font-weight:700;margin-left:5px;letter-spacing:.06em;}
.promo-tag{font-family:'DM Sans',sans-serif;font-size:.5rem;background:#E8F5E9;color:#2E7D32;border:1px solid #A5D6A7;padding:1px 6px;border-radius:2px;font-weight:600;margin-left:5px;}
.promo-hdr{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;letter-spacing:.14em;text-transform:uppercase;margin-bottom:8px;font-weight:600;padding:12px 0 0;border-top:1px solid #EDD9A3;}
.promo-ok{font-family:'DM Sans',sans-serif;font-size:.66rem;background:#E8F5E9;border:1px solid #A5D6A7;border-radius:3px;padding:9px 13px;color:#2E7D32;margin-top:10px;}
.promo-err{font-family:'DM Sans',sans-serif;font-size:.66rem;background:#FDF0F0;border:1px solid #F5C6C6;border-radius:3px;padding:9px 13px;color:#9B2335;margin-top:10px;}
.loyalty-band{background:linear-gradient(135deg,#FFF8EE,#FFF3DC);border:1px solid #EDD9A3;border-radius:6px;padding:11px 14px;margin-top:14px;margin-bottom:14px;display:flex;align-items:flex-start;gap:9px;}
.loyalty-band-txt{font-family:'DM Sans',sans-serif;font-size:.64rem;color:#8B6914;line-height:1.65;}
.loyalty-band-txt strong{color:#B8860B;font-weight:600;}

/* ── TOTAL BOX — DM Sans (standard, not Cormorant) ──────── */
.total-box{background:#1A1008;border-radius:6px;padding:15px 18px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;}
.total-lbl{font-family:'DM Sans',sans-serif;font-size:.7rem;color:rgba(255,253,249,.5);letter-spacing:.14em;text-transform:uppercase;}
.total-val{font-family:'DM Sans',sans-serif;font-size:1.3rem;font-weight:700;color:#D4A843;}

.btn-checkout{display:block;width:100%;background:#B8860B;color:#fff!important;border-radius:2px;padding:16px;font-family:'DM Sans',sans-serif;font-size:.76rem;letter-spacing:.18em;text-transform:uppercase;font-weight:600;text-align:center;text-decoration:none!important;transition:background .25s;margin-bottom:8px;}
.btn-checkout:hover{background:#9B7209;}
.checkout-sub{text-align:center;font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;margin-bottom:14px;}
.safe-strip{background:#F5E6C8;border-radius:4px;padding:10px 13px;display:flex;align-items:flex-start;gap:8px;margin-bottom:13px;}
.safe-strip-txt{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;line-height:1.65;}
.rate-note{display:flex;align-items:flex-start;gap:6px;padding-top:11px;border-top:1px solid #EDD9A3;}
.rate-note-dot{width:5px;height:5px;border-radius:50%;background:#4CAF50;flex-shrink:0;margin-top:3px;}
.rate-note-txt{font-family:'DM Sans',sans-serif;font-size:.58rem;color:#8B6914;line-height:1.65;}

/* ── Streamlit overrides ──────────────────────────────────── */
[data-testid="stForm"]{border:none!important;padding:0!important;background:transparent!important;}
.stTextInput>div>div>input{border:2px solid #EDD9A3!important;border-radius:2px!important;background:#FFFDF9!important;color:#1A1008!important;padding:10px 14px!important;font-family:'DM Sans',sans-serif!important;font-size:.82rem!important;letter-spacing:.04em!important;}
.stTextInput>div>div>input:focus{border-color:#B8860B!important;box-shadow:none!important;}
.stTextInput>div>div>input::placeholder{color:#C8A96A!important;opacity:1!important;}
.stTextInput label{display:none!important;}
.stButton>button{background:linear-gradient(135deg,#B8860B,#9B7209)!important;color:#FFFDF9!important;border:none!important;border-radius:2px!important;padding:11px!important;font-family:'DM Sans',sans-serif!important;font-size:.66rem!important;letter-spacing:.15em!important;text-transform:uppercase!important;width:100%!important;transition:all .2s!important;box-shadow:0 2px 8px rgba(184,134,11,.3)!important;}
.stButton>button:hover{background:linear-gradient(135deg,#9B7209,#7A5A07)!important;box-shadow:0 4px 16px rgba(184,134,11,.4)!important;}

/* ── FOOTER ──────────────────────────────────────────────── */
.aj-footer{background:#3D1F0E;border-top:3px solid #5C3420;padding:44px 5% 22px;display:block;width:100%;}
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

@media(max-width:1100px){.aj-fg{grid-template-columns:1fr 1fr;gap:24px;}}
@media(max-width:768px){
  [data-testid="stHorizontalBlock"]{flex-direction:column!important;}
  [data-testid="stHorizontalBlock"]>div:first-child{border-right:none;border-bottom:1px solid #EDD9A3;}
  .aj-nav-links{display:none;}
  .aj-fg{grid-template-columns:1fr;}
  .cart-continue{position:static;transform:none;display:block;text-align:center;margin-top:10px;}
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# NAVBAR
# ════════════════════════════════════════════════════════════
badge  = '<span class="aj-badge">' + str(cart_count) + '</span>' if cart_count > 0 else ""
wbadge = '<span class="aj-badge">' + str(wish_count) + '</span>' if wish_count > 0 else ""

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
    '<a href="?_nav=Cart"     target="_self" class="aj-icon">&#128722;' + badge + '</a>'
    '<a href="?_nav=Profile"  target="_self" class="aj-icon">&#128100;</a>'
    '<a href="?_nav=Profile"  target="_self" class="aj-btn-ac">My Account</a>'
    '</div></nav>',
    unsafe_allow_html=True
)

# ── TICKER ────────────────────────────────────────────────────
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

# ── PAGE HEADER ───────────────────────────────────────────────
item_str = str(total_items) + (" item" if total_items == 1 else " items")
st.markdown(
    '<div class="cart-hdr">'
    '<div class="cart-hdr-over">Your Selection</div>'
    '<div class="cart-hdr-title">Shopping Cart</div>'
    '<div class="cart-hdr-sub">'
    + item_str + ' &middot; All prices live from today\'s IBJA rate'
    '</div>'
    '<a href="?_nav=Catalogue" target="_self" class="cart-continue">&#8592; Continue Shopping</a>'
    '</div>',
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════
# EMPTY CART
# ════════════════════════════════════════════════════════════
if not items_priced:
    st.markdown(
        '<div class="empty-cart">'
        '<div class="empty-icon">&#128722;</div>'
        '<div class="empty-title">Your cart is empty</div>'
        '<div class="empty-sub">Looks like you haven\'t added any pieces yet. '
        'Browse our collection to find your perfect jewellery.</div>'
        '<a href="?_nav=Catalogue" target="_self" class="empty-cta">Explore Collection</a>'
        '</div>',
        unsafe_allow_html=True
    )

# ════════════════════════════════════════════════════════════
# FILLED CART
# ════════════════════════════════════════════════════════════
else:
    left_col, right_col = st.columns([6, 4])

    with left_col:
        out = (
            '<div class="cart-items-col">'
            '<div class="live-rate-note"><div class="lrn-dot"></div>'
            '<span class="lrn-txt">Prices below reflect <strong>today\'s IBJA gold rate</strong>'
            ' and will update tomorrow morning at 9 AM.</span></div>'
        )
        for it in items_priced:
            cart_id  = str(it["cart_id"])
            qty      = int(it["quantity"])
            pr       = it["pr"]
            wt       = float(it["weight_g"])
            making_p = str(int(float(it["making_pct"])*100))
            img_src  = img_url(it["image_main"])
            qty_multi= ' <span class="ci-multi">&times; '+str(qty)+'</span>' if qty>1 else ''

            oos        = it.get("out_of_stock", False)
            qty_exc    = it.get("qty_exceeds", False)
            available  = it.get("available", 999)
            oos_badge  = '<div class="ci-oos-badge">&#9888; Out of Stock</div>' if oos else ""
            qty_warn   = ('<div class="ci-qty-warn">&#9888; Only '+str(available)+' in stock — reduce quantity</div>' if qty_exc else "")
            plus_cls   = "qty-btn disabled" if (oos or qty_exc) else "qty-btn"
            plus_href  = ("#" if (oos or qty_exc) else "?action=qty_up&item="+cart_id)

            out += (
                '<div class="cart-item">'
                '<div class="ci-img"><img src="'+img_src+'" alt="'+it["name"]+'">'
                '<span class="ci-karat">'+it["karat"]+'</span></div>'
                '<div class="ci-info">'
                + oos_badge +
                '<div class="ci-cat">'+it["category_name"]+'</div>'
                '<div class="ci-name">'+it["name"]+'</div>'
                '<div class="ci-pills">'
                '<span class="ci-pill">'+it["karat"]+'</span>'
                '<span class="ci-pill">'+str(round(wt,1))+'g</span>'
                '<span class="ci-pill">Making '+making_p+'%</span>'
                '<span class="ci-bis">&#10003; BIS Hallmarked</span>'
                '</div>'
                '<div class="ci-divider"></div>'
                '<div class="ci-breakdown">'
                '<div class="ci-br-row">'
                '<span class="ci-br-lbl">Metal value ('+str(round(wt,1))+'g &times; '+format_inr(round(pr["rate_per_gram"],2))+'/g)</span>'
                '<span class="ci-br-val">'+format_inr(pr["metal_value"])+'</span></div>'
                '<div class="ci-br-row">'
                '<span class="ci-br-lbl">Making ('+making_p+'%)</span>'
                '<span class="ci-br-val">'+format_inr(pr["making_charge"])+'</span></div>'
                '<div class="ci-br-row">'
                '<span class="ci-br-lbl">GST (3%)</span>'
                '<span class="ci-br-val">'+format_inr(pr["gst"])+'</span></div>'
                '</div>'
                + qty_warn +
                '<div class="ci-footer">'
                '<div class="qty-wrap">'
                '<a href="?action=qty_down&item='+cart_id+'" target="_self" class="qty-btn">&#8722;</a>'
                '<span class="qty-val">'+str(qty)+'</span>'
                '<a href="'+plus_href+'" target="_self" class="'+plus_cls+'">&#43;</a>'
                '</div>'
                '<div class="ci-total">'+format_inr(it["line_total"])+qty_multi+'</div>'
                '<a href="?action=remove&item='+cart_id+'" target="_self" class="ci-remove">Remove</a>'
                '</div></div></div>'
            )
        out += '</div>'
        st.markdown(out, unsafe_allow_html=True)

    with right_col:
        sum_html = (
            '<div class="sum-wrap">'
            '<div class="sum-title">Order Summary</div>'
            '<div class="sum-rows">'
            '<div class="sum-row"><span class="sum-lbl">Subtotal ('+item_str+')</span>'
            '<span class="sum-val">'+format_inr(grand_subtotal)+'</span></div>'
        )
        if loyalty_disc > 0:
            sum_html += (
                '<div class="sum-row"><span class="sum-lbl">Loyalty discount'
                '<span class="tier-badge">'+tier.upper()+' '+str(loyalty_pct)+'%</span></span>'
                '<span class="sum-val disc">&minus;'+format_inr(loyalty_disc)+'</span></div>'
            )
        if promo_disc > 0:
            sum_html += (
                '<div class="sum-row"><span class="sum-lbl">Promo code'
                '<span class="promo-tag">'+str(st.session_state["promo_applied"])+'</span></span>'
                '<span class="sum-val disc">&minus;'+format_inr(promo_disc)+'</span></div>'
            )
        sum_html += (
            '<div class="sum-row"><span class="sum-lbl">Shipping</span>'
            '<span class="sum-val free">Free</span></div>'
            '</div><div class="promo-hdr">Have a Promo Code?</div>'
        )
        st.markdown(sum_html, unsafe_allow_html=True)

        with st.form("promo_form", clear_on_submit=True):
            promo_input = st.text_input("",placeholder="Enter promo code e.g. AURUS10",label_visibility="collapsed")
            submitted   = st.form_submit_button("Apply Code", use_container_width=True)
            if submitted:
                code = promo_input.strip().upper()
                if code and code in PROMO_CODES:
                    pc   = PROMO_CODES[code]
                    disc = round(grand_subtotal*pc["value"]/100,2) if pc["type"]=="pct" else min(float(pc["value"]),grand_subtotal)
                    st.session_state["promo_applied"]=code; st.session_state["promo_discount"]=disc
                    st.session_state["promo_msg"]="&#10003; Code "+code+" applied — "+pc["label"]+"!"; st.session_state["promo_msg_type"]="ok"
                else:
                    st.session_state["promo_applied"]=None; st.session_state["promo_discount"]=0.0
                    st.session_state["promo_msg"]="Invalid promo code. Please check and try again."; st.session_state["promo_msg_type"]="err"
                st.rerun()

        if st.session_state["promo_msg"]:
            msg_cls = "promo-ok" if st.session_state["promo_msg_type"]=="ok" else "promo-err"
            st.markdown('<div class="'+msg_cls+'">'+st.session_state["promo_msg"]+'</div>',unsafe_allow_html=True)

        bot_html = ""
        if loyalty_pct > 0:
            bot_html += (
                '<div class="loyalty-band"><span style="font-size:15px;flex-shrink:0;">&#128081;</span>'
                '<div class="loyalty-band-txt">You\'re a <strong>'+tier.title()+' member</strong> — '
                +str(loyalty_pct)+'% loyalty discount applied automatically.</div></div>'
            )
        bot_html += (
            '<div class="total-box">'
            '<span class="total-lbl">Total Payable</span>'
            '<span class="total-val">'+format_inr(total_payable)+'</span>'
            '</div>'
            '<a href="?_nav=Checkout" target="_self" class="btn-checkout">Proceed to Checkout &#8594;</a>'
            '<div class="checkout-sub">Secure checkout &middot; GST invoice included</div>'
            '<div class="safe-strip"><span style="font-size:13px;flex-shrink:0;">&#128274;</span>'
            '<div class="safe-strip-txt">Safe &amp; encrypted checkout. A complete GST invoice is auto-generated and emailed on every order.</div></div>'
            '<div class="rate-note"><div class="rate-note-dot"></div>'
            '<span class="rate-note-txt">Prices are calculated from today\'s IBJA rate. Final amount will be confirmed at checkout.</span>'
            '</div></div>'
        )
        st.markdown(bot_html, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════
st.markdown(
    '<div class="aj-footer"><div class="aj-fg">'
    '<div><div class="aj-fl-main">AURUS<span class="aj-fl-d"></span>JEWELS</div>'
    '<div class="aj-fl-rule"></div><div class="aj-fl-sub">Fine Gold &amp; Silver &middot; BIS Hallmarked</div>'
    '<p class="aj-fl-tag">Fine hallmarked jewellery priced live from the official IBJA gold rate. Transparency is our craft.</p>'
    '<span class="aj-fl-gstin">GSTIN: 07AABCS1429B1Z6</span></div>'
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
    '</div><div class="aj-fb">'
    '<span class="aj-fb-txt">&copy; 2026 Aurus Jewels. All rights reserved. All products BIS hallmarked.</span>'
    '<span class="aj-fb-txt">Prices update daily from IBJA official gold rates.</span>'
    '</div></div>',
    unsafe_allow_html=True
)