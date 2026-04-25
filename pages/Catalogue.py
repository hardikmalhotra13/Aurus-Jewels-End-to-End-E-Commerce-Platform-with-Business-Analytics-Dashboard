"""
pages/Catalogue.py — Aurus Jewels Catalogue
"""
import streamlit as st
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.session        import init_session, is_logged_in, get_role
from core.pricing_engine import get_all_rates, format_inr, price_product
from database.db         import execute_query

st.set_page_config(
    page_title            = "Catalogue — Aurus Jewels",
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
    _pid = st.query_params.get("id","")
    if _nav == "Product" and _pid:
        st.session_state["nav_product_id"] = _pid
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

rates = get_all_rates()
r22k  = rates.get(("gold","22K"), 6850.0)
r18k  = rates.get(("gold","18K"), 5600.0)
r925  = rates.get(("silver","925"), 85.0)

cat_p   = st.query_params.get("cat",   "all")
metal_p = st.query_params.get("metal", "all")
karat_p = st.query_params.get("karat", "all")
sort_p  = st.query_params.get("sort",  "featured")
page_p  = int(st.query_params.get("page", 1))

CATS = {"all":"All Jewellery","pendants":"Pendants","rings":"Rings",
        "earrings":"Earrings","bracelets":"Bracelets","chains":"Chains"}
PER_PAGE = 12

def img_url(p):
    return p.replace("\\","/").replace("static/","/app/static/")

def qurl(**kw):
    p = {"cat":cat_p,"metal":metal_p,"karat":karat_p,"sort":sort_p,"page":"1"}
    p.update({k:str(v) for k,v in kw.items()})
    return "?" + "&".join(f"{k}={v}" for k,v in p.items())

# ── fetch ────────────────────────────────────────────────────
def fetch():
    w, params = ["p.is_active=1"], []
    if cat_p != "all":
        w.append("LOWER(c.slug)=%s"); params.append(cat_p)
    if metal_p == "gold":   w.append("p.metal_type='gold'")
    elif metal_p == "silver": w.append("p.metal_type='silver'")
    if karat_p != "all":
        km = {"22k":"22K","18k":"18K","925":"925"}
        w.append("p.karat=%s"); params.append(km.get(karat_p, karat_p.upper()))
    om = {"featured":"p.is_featured DESC,p.product_id ASC",
          "price_asc":"p.weight_g ASC","price_desc":"p.weight_g DESC","newest":"p.product_id DESC"}
    sql = ("SELECT p.*,c.name AS category_name,c.slug FROM dim_products p "
           "JOIN dim_categories c ON p.category_id=c.category_id "
           "WHERE " + " AND ".join(w) + " ORDER BY " + om.get(sort_p, om["featured"]))
    return execute_query(sql, tuple(params)) or []

all_prods   = fetch()
total       = len(all_prods)
total_pages = max(1,(total+PER_PAGE-1)//PER_PAGE)
page_num    = max(1,min(page_p,total_pages))
start       = (page_num-1)*PER_PAGE
products    = all_prods[start:start+PER_PAGE]

# ════════════════════════════════════════════════════════════
# CSS
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
div[data-testid="stVerticalBlock"]>div{gap:0!important;width:100%!important;}
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
.aj-nav-links a:hover,.aj-nav-links a.cur{color:#B8860B;border-bottom-color:#B8860B;}
.aj-nav-right{display:flex;align-items:center;gap:12px;}
.aj-icon{font-size:1.05rem;color:#4A3728;display:flex;align-items:center;justify-content:center;width:26px;height:26px;position:relative;transition:color .2s;}
.aj-icon:hover{color:#B8860B;}
.aj-badge{position:absolute;top:-5px;right:-6px;background:#9B2335;color:#fff;font-size:.44rem;font-weight:700;border-radius:50%;width:13px;height:13px;display:flex;align-items:center;justify-content:center;}
.aj-btn-si{font-family:'DM Sans',sans-serif;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;background:#1A1008;color:#FFFDF9!important;padding:7px 16px;border-radius:2px;transition:background .2s;}
.aj-btn-si:hover{background:#B8860B;color:#FFFDF9!important;}
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
.aj-bis{font-family:'DM Sans',sans-serif;font-size:.52rem;background:rgba(184,134,11,.16);color:#D4A843;border:1px solid rgba(184,134,11,.28);padding:2px 9px;border-radius:2px;}

/* COLLECTION HEADER */
.col-hdr{text-align:center;padding:28px 5% 16px;border-bottom:1px solid #EDD9A3;background:#FFFDF9;}
.col-hdr-line{display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:8px;}
.col-hdr-rule{width:28px;height:1px;background:#B8860B;}
.col-hdr-over{font-family:'DM Sans',sans-serif;font-size:.56rem;color:#B8860B;letter-spacing:.24em;text-transform:uppercase;}
.col-hdr-title{font-family:'Cormorant Garamond',serif;font-size:clamp(1.8rem,3.5vw,2.8rem);font-weight:600;color:#B8860B;letter-spacing:.06em;line-height:1.1;margin-bottom:6px;}
.col-hdr-sub{font-family:'DM Sans',sans-serif;font-size:.68rem;color:#8B6914;}

/* FILTER BAR */
.fbar{
  padding:11px 5%;
  background:#FFFDF7;
  border-bottom:1px solid #EDD9A3;
  display:flex;align-items:center;gap:7px;flex-wrap:wrap;
  width:calc(100% + 0px);
  margin-left:0;margin-right:0;
  position:relative;left:0;right:0;
}
/* Force Streamlit wrappers to be truly full width */
section.main .block-container{padding-left:0!important;padding-right:0!important;max-width:100%!important;}
.stMarkdown,.stMarkdown>div{width:100%!important;max-width:100%!important;}
.f-lbl{font-family:'DM Sans',sans-serif;font-size:.52rem;color:#8B6914;letter-spacing:.1em;text-transform:uppercase;white-space:nowrap;}
.f-pill{font-family:'DM Sans',sans-serif;font-size:.56rem;padding:4px 12px;border-radius:20px;border:1px solid #EDD9A3;color:#4A3728;background:#FFFDF9;white-space:nowrap;cursor:pointer;transition:all .2s;}
.f-pill:hover{border-color:#B8860B;color:#B8860B;}
.f-pill.on{background:#1A1008;color:#E8C547;border-color:#1A1008;}
.f-kpill{font-family:'DM Sans',sans-serif;font-size:.58rem;padding:5px 14px;border-radius:2px;border:1px solid #EDD9A3;color:#4A3728;background:#FFFDF9;white-space:nowrap;cursor:pointer;transition:all .2s;}
.f-kpill:hover{border-color:#B8860B;}
.f-kpill.on{background:#B8860B;color:#fff;border-color:#B8860B;}
.f-div{width:1px;height:16px;background:#EDD9A3;flex-shrink:0;margin:0 4px;}
.f-clr{font-family:'DM Sans',sans-serif;font-size:.56rem;color:#9B2335;cursor:pointer;margin-left:auto;white-space:nowrap;}
.f-clr:hover{color:#7A1828;}
.f-sort{font-family:'DM Sans',sans-serif;font-size:.58rem;color:#4A3728;border:1px solid #EDD9A3;border-radius:2px;padding:5px 14px;background:#FFFDF9;cursor:pointer;outline:none;margin-left:auto;}
.f-sort:focus{border-color:#B8860B;}

/* PRODUCT GRID */
.cg-wrap{padding:22px 5%;}
.cpgrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px;}
.cpcard{background:#fff;border-radius:8px;overflow:hidden;border:1px solid #EDD9A3;box-shadow:0 2px 12px rgba(184,134,11,.07);transition:transform .3s,box-shadow .3s;display:flex;flex-direction:column;cursor:pointer;}
.cpcard:hover{transform:translateY(-5px);box-shadow:0 14px 36px rgba(184,134,11,.16);}
.cpimg{width:100%;padding-top:100%;position:relative;overflow:hidden;background:linear-gradient(135deg,#F5E6C8,#EDD9A3);flex-shrink:0;}
.cpimg img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .5s;display:block;}
.cpcard:hover .cpimg img{transform:scale(1.06);}
.cpkarat{position:absolute;top:7px;left:7px;z-index:1;font-family:'DM Sans',sans-serif;font-size:.5rem;letter-spacing:.1em;background:#1A1008;color:#E8C547;padding:2px 6px;border-radius:2px;}
.cpwish{position:absolute;top:7px;right:7px;z-index:2;width:24px;height:24px;border-radius:50%;background:rgba(255,253,249,.92);border:1px solid #EDD9A3;display:flex;align-items:center;justify-content:center;font-size:.76rem;color:#4A3728;cursor:pointer;transition:all .2s;}
.cpwish:hover{background:#B8860B;color:#fff;border-color:#B8860B;}
.cpbody{padding:11px 13px 13px;display:flex;flex-direction:column;min-height:135px;}
.cpcat{font-family:'DM Sans',sans-serif;font-size:.5rem;color:#B8860B;letter-spacing:.14em;text-transform:uppercase;margin-bottom:3px;font-weight:500;}
.cpname{font-family:'Cormorant Garamond',serif;font-size:.9rem;font-weight:500;color:#1A1008;line-height:1.3;margin-bottom:6px;flex:1;}
.cpmeta{display:flex;align-items:center;gap:5px;margin-bottom:7px;}
.cpwt{font-family:'DM Sans',sans-serif;font-size:.54rem;color:#8B6914;background:#F5E6C8;padding:1px 6px;border-radius:2px;}
.cpmk{font-family:'DM Sans',sans-serif;font-size:.54rem;color:#8B6914;}
.cpdiv{height:1px;background:#F0E4C4;margin-bottom:8px;}
.cppr{display:flex;align-items:center;justify-content:space-between;}
.cpprice{font-family:'DM Sans',sans-serif;font-size:.95rem;font-weight:600;color:#B8860B;}
.cpadd{font-family:'DM Sans',sans-serif;font-size:.5rem;letter-spacing:.1em;text-transform:uppercase;background:#1A1008;color:#FFFDF9;padding:5px 10px;border-radius:2px;cursor:pointer;border:none;transition:background .2s;}
.cpadd:hover{background:#B8860B;}

/* EMPTY */
.cat-empty{text-align:center;padding:72px 20px;}
.cat-empty-icon{font-size:2.8rem;margin-bottom:14px;}
.cat-empty-t{font-family:'Cormorant Garamond',serif;font-size:1.4rem;color:#1A1008;margin-bottom:7px;}
.cat-empty-s{font-family:'DM Sans',sans-serif;font-size:.76rem;color:#8B6914;}

/* PAGINATION */
.cat-pag{display:flex;justify-content:center;align-items:center;gap:5px;padding:22px 0 6px;}
.pgbtn{font-family:'DM Sans',sans-serif;font-size:.62rem;width:30px;height:30px;border-radius:2px;border:1px solid #EDD9A3;display:inline-flex;align-items:center;justify-content:center;color:#4A3728;transition:all .2s;}
.pgbtn:hover{border-color:#B8860B;color:#B8860B;}
.pgon{background:#1A1008!important;color:#E8C547!important;border-color:#1A1008!important;}
.pgdis{opacity:.3;pointer-events:none;}
.pginfo{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;margin:0 10px;}

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

/* RESPONSIVE */
@media(max-width:1200px){.cpgrid{grid-template-columns:repeat(3,minmax(0,1fr));}}
@media(max-width:900px){.cpgrid{grid-template-columns:repeat(2,minmax(0,1fr));}.aj-fg{grid-template-columns:1fr 1fr;gap:24px;}}
@media(max-width:640px){.aj-nav-links{display:none;}.cpgrid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;}.fbar{gap:5px;}.aj-fg{grid-template-columns:1fr;}}
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
    '<li><a href="?_nav=Catalogue" target="_self" class="cur">Catalogue</a></li>'
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
    '<span class="aj-bis">BIS Hallmarked</span></div></div>',
    unsafe_allow_html=True
)

# ── COLLECTION HEADER ────────────────────────────────────────
cat_label = CATS.get(cat_p, "All Jewellery")
st.markdown(
    '<div class="col-hdr">'
    '<div class="col-hdr-line">'
    '<div class="col-hdr-rule"></div>'
    '<span class="col-hdr-over">Collections</span>'
    '<div class="col-hdr-rule"></div>'
    '</div>'
    '<div class="col-hdr-title">Our Collection</div>'
    '</div>',
    unsafe_allow_html=True
)

# ── FILTER BAR ───────────────────────────────────────────────
def pill(label, param, val, cur, cls="f-pill"):
    on  = " on" if cur == val else ""
    url = qurl(**{param: val, "page": 1})
    return f'<a href="{url}" target="_self" class="{cls}{on}">{label}</a>'

has_filters = cat_p != "all" or metal_p != "all" or karat_p != "all"

# sort options for the <select>
sort_opts = {
    "featured":"Featured","price_asc":"Price: Low → High",
    "price_desc":"Price: High → Low","newest":"Newest First"
}

fb = '<div class="fbar">'
fb += '<span class="f-lbl">Category</span>'
for slug, name in CATS.items():
    fb += pill("All" if slug=="all" else name, "cat", slug, cat_p)
fb += '<div class="f-div"></div><span class="f-lbl">Metal</span>'
fb += pill("All","metal","all",metal_p)
fb += pill("Gold","metal","gold",metal_p)
fb += pill("Silver","metal","silver",metal_p)
fb += '<div class="f-div"></div><span class="f-lbl">Karat</span>'
fb += pill("22K","karat","22k",karat_p,"f-kpill")
fb += pill("18K","karat","18k",karat_p,"f-kpill")
fb += pill("925","karat","925",karat_p,"f-kpill")
if has_filters:
    clr = qurl(cat="all",metal="all",karat="all",page=1)
    fb += f'<a href="{clr}" target="_self" class="f-clr">&#215; Clear filters</a>'

fb += '<span style="flex:1;"></span>'
# sort select — pure HTML onchange navigates same tab
base_url = qurl(page=1)
fb += '<select class="f-sort" onchange="location.href=\''+base_url+'\'.replace(/sort=[^&]*/,\'sort=\'+this.value)">'
for k,v in sort_opts.items():
    sel = " selected" if k == sort_p else ""
    fb += f'<option value="{k}"{sel}>{v}</option>'
fb += '</select></div>'
st.markdown(fb, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# GRID + PAGINATION + FOOTER — single block
# ════════════════════════════════════════════════════════════
out = '<div class="cg-wrap">'

if not products:
    out += ('<div class="cat-empty">'
            '<div class="cat-empty-icon">&#128142;</div>'
            '<div class="cat-empty-t">No pieces found</div>'
            '<div class="cat-empty-s">Try adjusting your filters.</div>'
            '</div>')
else:
    out += '<div class="cpgrid">'
    for p in products:
        pr      = price_product(p)
        price_s = format_inr(pr["final_price"])
        making  = str(int(float(p["making_pct"]) * 100))
        wt      = str(round(float(p["weight_g"]), 1))
        iurl    = img_url(p["image_main"])
        pid     = str(p["product_id"])
        wjs = (
            'onclick="event.preventDefault();event.stopPropagation();'
            'window.location.href=\'?_nav=Wishlist&add=' + pid + '\'"'
            if logged_in else
            'onclick="event.preventDefault();event.stopPropagation();'
            'window.location.href=\'?_nav=Login\'"'
        )

        out += (
            '<a href="?_nav=Product&id=' + pid + '" class="cpcard">'
            '<div class="cpimg">'
            '<img src="' + iurl + '" alt="' + p["name"] + '">'
            '<span class="cpkarat">' + p["karat"] + '</span>'
            '<span class="cpwish" ' + wjs + '>&#9825;</span>'
            '</div>'
            '<div class="cpbody">'
            '<div class="cpcat">' + p["category_name"] + '</div>'
            '<div class="cpname">' + p["name"] + '</div>'
            '<div class="cpmeta">'
            '<span class="cpwt">' + wt + 'g</span>'
            '<span class="cpmk">&middot; Making ' + making + '%</span>'
            '</div>'
            '<div class="cpdiv"></div>'
            '<div class="cppr">'
            '<span class="cpprice">' + price_s + '</span>'
            '<span class="cpadd">Add to Cart</span>'
            '</div></div></a>'
        )
    out += '</div>'

# pagination
if total_pages > 1:
    s1 = start + 1
    s2 = min(start + PER_PAGE, total)
    out += '<div class="cat-pag">'
    out += ('<a href="' + qurl(page=page_num-1) + '" target="_self" class="pgbtn">&#8249;</a>'
            if page_num > 1 else '<span class="pgbtn pgdis">&#8249;</span>')
    for i in range(1, total_pages + 1):
        if i == page_num:
            out += '<span class="pgbtn pgon">' + str(i) + '</span>'
        elif abs(i - page_num) <= 2 or i == 1 or i == total_pages:
            out += '<a href="' + qurl(page=i) + '" target="_self" class="pgbtn">' + str(i) + '</a>'
        elif abs(i - page_num) == 3:
            out += '<span class="pginfo">…</span>'
    out += ('<a href="' + qurl(page=page_num+1) + '" target="_self" class="pgbtn">&#8250;</a>'
            if page_num < total_pages else '<span class="pgbtn pgdis">&#8250;</span>')
    out += '<span class="pginfo">Showing ' + str(s1) + '–' + str(s2) + ' of ' + str(total) + '</span>'
    out += '</div>'

out += '</div>'  # close cg-wrap

# footer
out += (
    '<div class="aj-footer">'
    '<div class="aj-fg">'
    '<div>'
    '<div class="aj-fl-main">AURUS<span class="aj-fl-d"></span>JEWELS</div>'
    '<div class="aj-fl-rule"></div>'
    '<div class="aj-fl-sub">Fine Gold &amp; Silver &middot; BIS Hallmarked</div>'
    '<p class="aj-fl-tag">Fine hallmarked jewellery priced live from the official IBJA gold rate. Transparency is our craft.</p>'
    '<span class="aj-fl-gstin">GSTIN: 07AABCS1429B1Z6</span>'
    '</div>'
    '<div><div class="aj-fc-title">Shop</div><ul class="aj-fc-links">'
    '<li><a href="?cat=pendants" target="_self">Pendants</a></li>'
    '<li><a href="?cat=rings" target="_self">Rings</a></li>'
    '<li><a href="?cat=earrings" target="_self">Earrings</a></li>'
    '<li><a href="?cat=bracelets" target="_self">Bracelets</a></li>'
    '<li><a href="?cat=chains" target="_self">Chains</a></li>'
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
    '</div></div>'
)

st.markdown(out, unsafe_allow_html=True)