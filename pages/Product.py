"""
pages/Product.py — Aurus Jewels Product Detail Page
"""
import streamlit as st
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.session        import init_session, is_logged_in, get_role
from core.pricing_engine import get_all_rates, format_inr, price_product
from database.db         import execute_query, execute_write

st.set_page_config(
    page_title            = "Product — Aurus Jewels",
    page_icon             = "✦",
    layout                = "wide",
    initial_sidebar_state = "collapsed",
)

init_session()

PAGE_MAP = {
    "Home":"Home.py","Catalogue":"pages/Catalogue.py",
    "Product":"pages/Product.py","Cart":"pages/Cart.py",
    "Checkout":"pages/Checkout.py","Profile":"pages/Profile.py",
    "Login":"pages/Login.py","Admin":"pages/Admin.py","Wishlist":"pages/Wishlist.py",
}
_nav = st.query_params.get("_nav","")
if _nav and _nav in PAGE_MAP:
    st.query_params.clear()
    st.switch_page(PAGE_MAP[_nav])

logged_in  = is_logged_in()
role       = get_role()
cart_count = 0
wish_count = 0
if logged_in:
    cid = st.session_state.get("customer_id")
    r = execute_query("SELECT COALESCE(SUM(quantity),0) AS t FROM customer_cart WHERE customer_id=%s",(cid,))
    cart_count = int(r[0]["t"]) if r else 0
    w = execute_query("SELECT COUNT(*) AS t FROM customer_wishlist WHERE customer_id=%s",(cid,))
    wish_count = int(w[0]["t"]) if w else 0

# ── get product id ───────────────────────────────────────────
pid = st.query_params.get("id","")
if not pid:
    pid = st.session_state.pop("nav_product_id", "")
if not pid:
    st.switch_page("pages/Catalogue.py")

product = None
if pid:
    rows = execute_query(
        "SELECT p.*, c.name AS category_name, c.slug "
        "FROM dim_products p "
        "JOIN dim_categories c ON p.category_id=c.category_id "
        "WHERE p.product_id=%s AND p.is_active=1",
        (pid,)
    )
    product = rows[0] if rows else None

if not product:
    st.error("Product not found.")
    st.stop()

# ── handle actions ───────────────────────────────────────────
# CRITICAL: use st.query_params.clear() then set individual keys
# NOT st.query_params.update() — update() leaves 'action' in the URL
# causing an infinite rerun loop (blank page bug)

action = st.query_params.get("action","")

if action == "addcart":
    if not logged_in:
        st.switch_page("pages/Login.py")
    else:
        existing = execute_query(
            "SELECT cart_id, quantity FROM customer_cart "
            "WHERE customer_id=%s AND product_id=%s",
            (cid, pid)
        )
        if existing:
            execute_write(
                "UPDATE customer_cart SET quantity=quantity+1 "
                "WHERE cart_id=%s",
                (existing[0]["cart_id"],)
            )
        else:
            execute_write(
                "INSERT INTO customer_cart (customer_id, product_id, quantity) "
                "VALUES (%s,%s,1)",
                (cid, pid)
            )
        # Clear ALL params first, then set only id + msg (no action!)
        st.query_params.clear()
        st.query_params["id"]  = str(pid)
        st.query_params["msg"] = "added"
        st.rerun()

if action == "addwish":
    if not logged_in:
        st.switch_page("pages/Login.py")
    else:
        exists = execute_query(
            "SELECT wishlist_id FROM customer_wishlist "
            "WHERE customer_id=%s AND product_id=%s",
            (cid, pid)
        )
        if not exists:
            execute_write(
                "INSERT INTO customer_wishlist (customer_id, product_id) VALUES (%s,%s)",
                (cid, pid)
            )
        # Clear ALL params first, then set only id + msg (no action!)
        st.query_params.clear()
        st.query_params["id"]  = str(pid)
        st.query_params["msg"] = "wished"
        st.rerun()

msg = st.query_params.get("msg","")

# ── rates & pricing ──────────────────────────────────────────
rates   = get_all_rates()
r22k    = rates.get(("gold","22K"), 6850.0)
r18k    = rates.get(("gold","18K"), 5600.0)
r925    = rates.get(("silver","925"), 85.0)
pr      = price_product(product)
wt      = float(product["weight_g"])
making  = float(product["making_pct"])
karat   = product["karat"]

metal_type = product.get("metal_type","gold")
if metal_type == "silver":
    rate_per_g = r925
    rate_label = "₹" + format_inr(r925) + "/g · Silver 925"
elif karat == "22K":
    rate_per_g = r22k
    rate_label = format_inr(r22k) + "/g · Gold 22K"
else:
    rate_per_g = r18k
    rate_label = format_inr(r18k) + "/g · Gold 18K"

gold_value    = round(wt * rate_per_g, 2)
making_amt    = round(gold_value * making, 2)
subtotal      = gold_value + making_amt
gst_amt       = round(subtotal * 0.03, 2)
total_price   = round(subtotal + gst_amt, 2)

gold_val_s  = format_inr(gold_value)
making_s    = format_inr(making_amt)
gst_s       = format_inr(gst_amt)
total_s     = format_inr(total_price)
making_pct  = str(int(making * 100))

def img_url(p):
    return p.replace("\\","/").replace("static/","/app/static/")

img_main  = img_url(product["image_main"])

img_b_raw = product.get("image_2") or product["image_main"]
img_b     = img_url(img_b_raw)

img_c = None
if img_b_raw != product["image_main"] and "_b." in img_b_raw:
    img_c_raw = img_b_raw.replace("_b.", "_c.")
    abs_c     = os.path.join(ROOT, img_c_raw.replace("\\", "/"))
    if os.path.exists(abs_c):
        img_c = img_url(img_c_raw)

cat_name  = product["category_name"]
cat_slug  = product["slug"]
prod_name = product["name"]

# ════════════════════════════════════════════════════════════
# CSS — <base> tag MUST be in its own separate st.markdown()
# call BEFORE the <style> block. Putting <base> inside the
# same call as <style> causes the CSS to render as plain text.
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

/* NAV */
.aj-nav{position:sticky;top:0;z-index:999;background:#FFFDF7;border-bottom:1.5px solid #E8D5A3;box-shadow:0 2px 20px rgba(184,134,11,.1);padding:0 5%;height:56px;display:flex;align-items:center;justify-content:space-between;}
.aj-logo{display:flex;flex-direction:column;align-items:flex-start;gap:2px;}
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
.aj-btn-si{font-family:'DM Sans',sans-serif;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;background:#1A1008;color:#FFFDF9!important;padding:7px 16px;border-radius:2px;transition:background .2s;}
.aj-btn-si:hover{background:#B8860B;}
.aj-btn-ac{font-family:'DM Sans',sans-serif;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;border:1.5px solid #B8860B;color:#B8860B!important;padding:6px 12px;border-radius:2px;transition:all .2s;}
.aj-btn-ac:hover{background:#B8860B;color:#fff!important;}

/* TICKER */
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

/* BREADCRUMB */
.bc{padding:11px 5%;border-bottom:1px solid #EDD9A3;display:flex;align-items:center;gap:5px;background:#FFFDF9;}
.bc a{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;}
.bc a:hover{color:#B8860B;}
.bc-sep{font-size:.6rem;color:#C8A96A;}
.bc-cur{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#1A1008;font-weight:500;}

/* PRODUCT MAIN */
.prod-wrap{padding:32px 5%;display:grid;grid-template-columns:1fr 1fr;gap:48px;}

/* CSS-only radio gallery */
.gallery-radio { display:none; }
.gmain {
  width:100%; aspect-ratio:1; border-radius:8px; overflow:hidden;
  border:1px solid #EDD9A3;
  background:linear-gradient(135deg,#F5E6C8,#EDD9A3);
  position:relative; margin-bottom:12px;
}
.gslide { display:none; width:100%; height:100%; }
.gslide img { width:100%; height:100%; object-fit:cover; display:block; }
#gi1:checked ~ .gmain .gs1 { display:block; }
#gi2:checked ~ .gmain .gs2 { display:block; }
#gi3:checked ~ .gmain .gs3 { display:block; }
.img-karat {
  position:absolute; top:12px; left:12px; z-index:2;
  font-family:'DM Sans',sans-serif; font-size:.56rem; letter-spacing:.1em;
  background:#1A1008; color:#E8C547; padding:3px 9px; border-radius:2px; font-weight:500;
}
.gthumbs { display:flex; gap:10px; }
.gthumb {
  flex:1; min-width:0; aspect-ratio:1; border-radius:6px; overflow:hidden;
  border:2px solid #EDD9A3; cursor:pointer; display:block; transition:border-color .2s;
}
.gthumb img { width:100%; height:100%; object-fit:cover; display:block; transition:transform .4s; }
.gthumb:hover { border-color:#D4A843; }
.gthumb:hover img { transform:scale(1.05); }
#gi1:checked ~ .gthumbs label[for="gi1"] { border-color:#B8860B; }
#gi2:checked ~ .gthumbs label[for="gi2"] { border-color:#B8860B; }
#gi3:checked ~ .gthumbs label[for="gi3"] { border-color:#B8860B; }

/* DETAIL COL */
.det-cat{font-family:'DM Sans',sans-serif;font-size:.56rem;color:#B8860B;letter-spacing:.18em;text-transform:uppercase;font-weight:500;margin-bottom:6px;}
.det-name{font-family:'Cormorant Garamond',serif;font-size:clamp(1.4rem,2.5vw,2rem);font-weight:600;color:#1A1008;line-height:1.2;margin-bottom:14px;}
.det-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:16px;}
.det-pill{font-family:'DM Sans',sans-serif;font-size:.58rem;background:#F5E6C8;color:#8B6914;padding:4px 10px;border-radius:2px;font-weight:500;}
.det-bis{font-family:'DM Sans',sans-serif;font-size:.58rem;background:#E8F5E9;color:#2E7D32;padding:4px 10px;border-radius:2px;font-weight:500;}
.det-divider{height:1px;background:#EDD9A3;margin-bottom:18px;}

/* PRICE BOX */
.price-box{background:#FFF8EE;border:1px solid #EDD9A3;border-radius:6px;padding:18px 20px;margin-bottom:18px;}
.price-main{font-family:'DM Sans',sans-serif;font-size:2rem;font-weight:700;color:#B8860B;margin-bottom:12px;line-height:1;}
.price-rows{display:flex;flex-direction:column;gap:6px;margin-bottom:12px;}
.price-row{display:flex;justify-content:space-between;align-items:center;}
.price-lbl{font-family:'DM Sans',sans-serif;font-size:.63rem;color:#8B6914;}
.price-val{font-family:'DM Sans',sans-serif;font-size:.67rem;color:#1A1008;font-weight:500;}
.price-total-row{border-top:1px solid #EDD9A3;padding-top:8px;margin-top:4px;}
.price-total-lbl{font-family:'DM Sans',sans-serif;font-size:.66rem;color:#1A1008;font-weight:600;}
.price-total-val{font-family:'DM Sans',sans-serif;font-size:.86rem;color:#B8860B;font-weight:700;}
.price-note{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;border-top:1px solid #EDD9A3;padding-top:10px;display:flex;align-items:center;gap:5px;}
.rate-dot{width:5px;height:5px;border-radius:50%;background:#4CAF50;flex-shrink:0;}

/* MSG */
.msg-ok{font-family:'DM Sans',sans-serif;font-size:.7rem;background:#E8F5E9;border:1px solid #A5D6A7;border-radius:4px;padding:9px 14px;color:#2E7D32;margin-bottom:14px;display:flex;align-items:center;gap:6px;}

/* ACTION BUTTONS */
.btn-row{display:flex;gap:10px;margin-bottom:16px;}
.btn-cart{flex:1;background:#1A1008;color:#FFFDF9!important;border:none;border-radius:2px;padding:13px;font-family:'DM Sans',sans-serif;font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;cursor:pointer;transition:background .2s;text-align:center;text-decoration:none!important;display:flex;align-items:center;justify-content:center;}
.btn-cart:hover{background:#B8860B;}
.btn-wish{width:46px;height:46px;flex-shrink:0;border-radius:2px;border:1.5px solid #E8D5A3;background:#FFFDF9;display:flex;align-items:center;justify-content:center;font-size:1.1rem;color:#4A3728;cursor:pointer;text-decoration:none!important;transition:all .2s;}
.btn-wish:hover{border-color:#B8860B;color:#B8860B;}
.btn-wish.wished{background:#FFF0F0;border-color:#E57373;color:#C62828;}

/* GST NOTE */
.gst-note{background:#FFFDF9;border:1px solid #EDD9A3;border-radius:6px;padding:12px 14px;display:flex;align-items:flex-start;gap:10px;}
.gst-note-txt{font-family:'DM Sans',sans-serif;font-size:.62rem;color:#8B6914;line-height:1.65;}
.gst-note-txt strong{color:#1A1008;font-weight:600;}

/* ASSURANCE */
.assurance-wrap{padding:0 5% 32px;}
.assurance-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;}
.assurance-card{border-left:3px solid #B8860B;padding:14px 16px;background:#FFFDF9;border-top:1px solid #EDD9A3;border-right:1px solid #EDD9A3;border-bottom:1px solid #EDD9A3;}
.assurance-icon{font-size:1.3rem;margin-bottom:8px;display:block;}
.assurance-title{font-family:'DM Sans',sans-serif;font-size:.68rem;color:#1A1008;font-weight:600;margin-bottom:4px;}
.assurance-sub{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;line-height:1.55;}

/* FOOTER */
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

@media(max-width:900px){.prod-wrap{grid-template-columns:1fr;gap:24px;}.assurance-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.aj-fg{grid-template-columns:1fr 1fr;gap:24px;}}
@media(max-width:600px){.aj-nav-links{display:none;}.aj-fg{grid-template-columns:1fr;}.assurance-grid{grid-template-columns:1fr 1fr;}}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# NAVBAR
# ════════════════════════════════════════════════════════════
badge  = '<span class="aj-badge">' + str(cart_count) + '</span>' if cart_count > 0 else ""
wbadge = '<span class="aj-badge">' + str(wish_count) + '</span>' if wish_count > 0 else ""
auth   = (
    '<a href="?_nav=Profile" target="_self" class="aj-btn-ac">My Account</a>'
    if logged_in else
    '<a href="?_nav=Login" target="_self" class="aj-btn-si">Sign In</a>'
)
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

# ── TICKER ───────────────────────────────────────────────────
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

# ── BREADCRUMB ───────────────────────────────────────────────
st.markdown(
    '<div class="bc">'
    '<a href="?_nav=Home" target="_self">Home</a>'
    '<span class="bc-sep">›</span>'
    '<a href="?_nav=Catalogue" target="_self">Catalogue</a>'
    '<span class="bc-sep">›</span>'
    '<a href="?_nav=Catalogue&cat=' + cat_slug + '" target="_self">' + cat_name + '</a>'
    '<span class="bc-sep">›</span>'
    '<span class="bc-cur">' + prod_name + '</span>'
    '</div>',
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════
# PRODUCT MAIN
# ════════════════════════════════════════════════════════════
is_wished = False
if logged_in:
    wq = execute_query(
        "SELECT wishlist_id FROM customer_wishlist WHERE customer_id=%s AND product_id=%s",
        (cid, pid)
    )
    is_wished = bool(wq)

wish_cls  = "btn-wish wished" if is_wished else "btn-wish"
wish_icon = "&#9829;" if is_wished else "&#9825;"

msg_html = ""
if msg == "added":
    msg_html = '<div class="msg-ok">&#10003; Added to cart successfully!</div>'
elif msg == "wished":
    msg_html = '<div class="msg-ok">&#10003; Added to wishlist!</div>'

radios = '<input type="radio" class="gallery-radio" name="gallery" id="gi1" checked>'
slides = '<div class="gslide gs1"><img src="' + img_main + '" alt="' + prod_name + '"></div>'
thumbs = '<label for="gi1" class="gthumb"><img src="' + img_main + '" alt="view 1"></label>'

if img_b != img_main:
    radios += '<input type="radio" class="gallery-radio" name="gallery" id="gi2">'
    slides += '<div class="gslide gs2"><img src="' + img_b + '" alt="view 2"></div>'
    thumbs += '<label for="gi2" class="gthumb"><img src="' + img_b + '" alt="view 2"></label>'

if img_c:
    radios += '<input type="radio" class="gallery-radio" name="gallery" id="gi3">'
    slides += '<div class="gslide gs3"><img src="' + img_c + '" alt="view 3"></div>'
    thumbs += '<label for="gi3" class="gthumb"><img src="' + img_c + '" alt="view 3"></label>'

block = (
    '<div class="prod-wrap">'
    '<div>'
    + radios +
    '<div class="gmain">'
    '<span class="img-karat">' + karat + '</span>'
    + slides +
    '</div>'
    '<div class="gthumbs">'
    + thumbs +
    '</div>'
    '</div>'
    '<div>'
    + msg_html +
    '<div class="det-cat">' + cat_name + ' &middot; ' + karat + ' ' + product.get("metal_type","Gold").title() + '</div>'
    '<div class="det-name">' + prod_name + '</div>'
    '<div class="det-meta">'
    '<span class="det-pill">' + karat + '</span>'
    '<span class="det-pill">' + str(round(wt,1)) + 'g</span>'
    '<span class="det-pill">Making ' + making_pct + '%</span>'
    '<span class="det-bis">&#10003; BIS Hallmarked</span>'
    '</div>'
    '<div class="det-divider"></div>'
    '<div class="price-box">'
    '<div class="price-main">' + total_s + '</div>'
    '<div class="price-rows">'
    '<div class="price-row">'
    '<span class="price-lbl">Gold value (' + str(round(wt,1)) + 'g &times; ' + format_inr(round(rate_per_g,2)) + '/g)</span>'
    '<span class="price-val">' + gold_val_s + '</span>'
    '</div>'
    '<div class="price-row">'
    '<span class="price-lbl">Making charges (' + making_pct + '%)</span>'
    '<span class="price-val">' + making_s + '</span>'
    '</div>'
    '<div class="price-row">'
    '<span class="price-lbl">GST (3%)</span>'
    '<span class="price-val">' + gst_s + '</span>'
    '</div>'
    '<div class="price-row price-total-row">'
    '<span class="price-total-lbl">Total</span>'
    '<span class="price-total-val">' + total_s + '</span>'
    '</div>'
    '</div>'
    '<div class="price-note">'
    '<div class="rate-dot"></div>'
    'Price calculated from today\'s IBJA rate &middot; ' + rate_label +
    '</div>'
    '</div>'
    '<div class="btn-row">'
    '<a href="?id=' + str(pid) + '&action=addcart" target="_self" class="btn-cart">Add to Cart</a>'
    '<a href="?id=' + str(pid) + '&action=addwish" target="_self" class="' + wish_cls + '">' + wish_icon + '</a>'
    '</div>'
    '<div class="gst-note">'
    '<span style="font-size:1rem;flex-shrink:0;">&#128221;</span>'
    '<div class="gst-note-txt">'
    '<strong>GST Invoice included</strong> &mdash; A complete GST invoice with '
    'CGST + SGST breakdown will be emailed after your order is confirmed.'
    '</div>'
    '</div>'
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px;">'
    '<div style="background:linear-gradient(135deg,#FFF8EE,#FFF3E0);border:1.5px solid #EDD9A3;'
    'border-radius:8px;padding:18px 16px;position:relative;overflow:hidden;">'
    '<div style="position:absolute;top:-10px;right:-10px;width:60px;height:60px;'
    'border-radius:50%;background:rgba(184,134,11,.06);"></div>'
    '<div style="font-size:1.4rem;margin-bottom:8px;">&#128666;</div>'
    '<div style="font-family:\'DM Sans\',sans-serif;font-size:.72rem;font-weight:600;'
    'color:#1A1008;margin-bottom:5px;">Free Delivery</div>'
    '<div style="font-family:\'DM Sans\',sans-serif;font-size:.62rem;color:#8B6914;line-height:1.6;">'
    'On all orders across India.<br>Fully insured &amp; tracked.</div>'
    '</div>'
    '<div style="background:linear-gradient(135deg,#FFF8EE,#FFF3E0);border:1.5px solid #EDD9A3;'
    'border-radius:8px;padding:18px 16px;position:relative;overflow:hidden;">'
    '<div style="position:absolute;top:-10px;right:-10px;width:60px;height:60px;'
    'border-radius:50%;background:rgba(184,134,11,.06);"></div>'
    '<div style="font-size:1.4rem;margin-bottom:8px;">&#128260;</div>'
    '<div style="font-family:\'DM Sans\',sans-serif;font-size:.72rem;font-weight:600;'
    'color:#1A1008;margin-bottom:5px;">Easy Returns</div>'
    '<div style="font-family:\'DM Sans\',sans-serif;font-size:.62rem;color:#8B6914;line-height:1.6;">'
    '7-day hassle-free returns<br>with full refund guaranteed.</div>'
    '</div>'
    '</div>'
    '<div style="margin-top:14px;background:#1A1008;border-radius:8px;padding:18px 20px;'
    'display:flex;align-items:flex-start;gap:14px;">'
    '<div style="flex-shrink:0;width:36px;height:36px;border-radius:50%;'
    'background:rgba(184,134,11,.2);display:flex;align-items:center;justify-content:center;'
    'font-size:1rem;">&#9878;&#65039;</div>'
    '<div>'
    '<div style="font-family:\'DM Sans\',sans-serif;font-size:.62rem;color:#E8C547;'
    'letter-spacing:.14em;text-transform:uppercase;margin-bottom:6px;font-weight:600;">'
    'Price Transparency Promise</div>'
    '<div style="font-family:\'DM Sans\',sans-serif;font-size:.64rem;'
    'color:rgba(255,253,249,.5);line-height:1.7;">'
    'This price is calculated live from the IBJA official gold rate updated every morning. '
    'No hidden markup — what you see is exactly what gold costs today.'
    '</div>'
    '</div>'
    '</div>'
    '</div>'
    '</div>'
)
st.markdown(block, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# ASSURANCE + FOOTER
# ════════════════════════════════════════════════════════════
st.markdown(
    '<div class="assurance-wrap">'
    '<div class="assurance-grid">'
    '<div class="assurance-card">'
    '<span class="assurance-icon">&#9878;&#65039;</span>'
    '<div class="assurance-title">Live IBJA Pricing</div>'
    '<div class="assurance-sub">Price updates daily from official IBJA gold rates. No hidden margins.</div>'
    '</div>'
    '<div class="assurance-card">'
    '<span class="assurance-icon">&#127941;</span>'
    '<div class="assurance-title">BIS Hallmarked</div>'
    '<div class="assurance-sub">Certified purity guaranteed on every piece we sell.</div>'
    '</div>'
    '<div class="assurance-card">'
    '<span class="assurance-icon">&#128221;</span>'
    '<div class="assurance-title">GST Invoice</div>'
    '<div class="assurance-sub">Full GST invoice emailed on every order automatically.</div>'
    '</div>'
    '<div class="assurance-card">'
    '<span class="assurance-icon">&#128081;</span>'
    '<div class="assurance-title">Loyalty Rewards</div>'
    '<div class="assurance-sub">Every purchase earns loyalty points towards Silver, Gold &amp; Platinum.</div>'
    '</div>'
    '</div>'
    '</div>'
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