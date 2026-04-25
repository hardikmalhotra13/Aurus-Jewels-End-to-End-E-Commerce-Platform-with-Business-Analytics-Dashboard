"""
Home.py — Aurus Jewels Homepage
"""
import streamlit as st
import sys, os
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from core.session        import init_session, is_logged_in, get_role
from core.scheduler      import start_scheduler
from core.pricing_engine import get_all_rates, format_inr, price_product
from database.db         import execute_query

st.set_page_config(
    page_title            = "Aurus Jewels — Fine Gold & Silver",
    page_icon             = "✦",
    layout                = "wide",
    initial_sidebar_state = "collapsed",
)

init_session()
start_scheduler()

logged_in  = is_logged_in()
role       = get_role()
cart_count = 0
if logged_in:
    cid  = st.session_state.get("customer_id")
    rows = execute_query(
        "SELECT COALESCE(SUM(quantity),0) AS t "
        "FROM customer_cart WHERE customer_id=%s", (cid,)
    )
    cart_count = int(rows[0]["t"]) if rows else 0

rates = get_all_rates()
r22k  = rates.get(("gold",   "22K"), 6850.00)
r18k  = rates.get(("gold",   "18K"), 5600.00)
r925  = rates.get(("silver", "925"),   85.00)

USD = 0.012; GBP = 0.0095; EUR = 0.011; AED = 0.044
today_str = date.today().strftime("%d %b %Y")

r22k_str  = format_inr(r22k)
r18k_str  = format_inr(r18k)
r925_str  = format_inr(r925)
r22k_10   = format_inr(r22k * 10)
r22k_100  = format_inr(r22k * 100)
r18k_10   = format_inr(r18k * 10)
r18k_100  = format_inr(r18k * 100)
r925_10   = format_inr(r925 * 10)
r925_100  = format_inr(r925 * 100)
r22k_usd  = str(round(r22k * USD, 2))
r22k_gbp  = str(round(r22k * GBP, 2))
r22k_eur  = str(round(r22k * EUR, 2))
r22k_aed  = str(round(r22k * AED, 2))
r18k_usd  = str(round(r18k * USD, 2))
r18k_gbp  = str(round(r18k * GBP, 2))
r18k_eur  = str(round(r18k * EUR, 2))
r18k_aed  = str(round(r18k * AED, 2))
r925_usd  = str(round(r925 * USD, 2))
r925_gbp  = str(round(r925 * GBP, 2))
r925_eur  = str(round(r925 * EUR, 2))
r925_aed  = str(round(r925 * AED, 2))


def img_url(path):
    return path.replace("\\", "/").replace("static/", "/app/static/")


# ════════════════════════════════════════════════════════════
# NAV VARIABLES  (computed here so they can be merged into the
#                 CSS+NAV single st.markdown call below)
# ════════════════════════════════════════════════════════════
badge = (
    '<span class="aj-cart-badge">' + str(cart_count) + '</span>'
    if cart_count > 0 else ""
)
if logged_in:
    _auth = '<a href="/Profile" class="aj-btn-account">My Account</a>'
    _profile_icon = '<a href="/Profile" class="aj-icon-link" title="Profile">&#128100;</a>'
    if role == "admin":
        _auth += '<a href="/Admin" class="aj-btn-admin">Admin</a>'
else:
    _auth = '<a href="/Login" class="aj-btn-signin">Sign In</a>'
    _profile_icon = '<a href="/Login" class="aj-icon-link" title="Sign In">&#128100;</a>'
_wish_icon = '<a href="/Wishlist" class="aj-icon-link" title="Wishlist">&#9825;</a>'


# ════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=DM+Sans:wght@300;400;500;600&display=swap');

#MainMenu,footer,header{display:none!important;}
.stApp{background:#FFFDF9!important;}
[data-testid="stAppViewContainer"]>.main{padding:0!important;}
[data-testid="stHeader"]{display:none!important;height:0!important;min-height:0!important;}
[data-testid="stAppViewBlockContainer"]{padding-top:0!important;margin-top:0!important;}
[data-testid="stDecoration"]{display:none!important;}
[data-testid="stToolbar"]{display:none!important;}
.stApp>header{display:none!important;height:0!important;}
.stApp{margin-top:0!important;padding-top:0!important;}
section[data-testid="stSidebar"]{display:none!important;}
.block-container{padding:0!important;max-width:100%!important;}
.element-container{margin:0!important;}
div[data-testid="stVerticalBlock"]>div{gap:0!important;}
*{box-sizing:border-box;}
a{text-decoration:none!important;color:inherit!important;}

/* ── FIX: remove Streamlit's residual top gap ── */
.stMainBlockContainer{padding-top:0!important;margin-top:0!important;}
.stMain{padding-top:0!important;margin-top:0!important;}
[data-testid="stMainBlockContainer"]{padding-top:0!important;margin-top:0!important;}
div[data-testid="stVerticalBlock"]{padding-top:0!important;margin-top:0!important;}
.main .block-container{padding-top:0!important;margin-top:0!important;}
section.main > div:first-child{padding-top:0!important;margin-top:0!important;}
[data-testid="stAppViewContainer"] > section > div{padding-top:0!important;}

/* NAV */
.aj-nav{
  position:sticky;top:0;z-index:999;
  background:#FFFDF7;
  border-bottom:1.5px solid #E8D5A3;
  box-shadow:0 2px 20px rgba(184,134,11,.1);
  padding:0 5%;height:56px;
  display:flex;align-items:center;justify-content:space-between;
}
.aj-logo{
  display:flex;flex-direction:column;
  align-items:flex-start;gap:3px;
  text-decoration:none!important;cursor:pointer;
}
.aj-logo-main{
  font-family:'Cormorant Garamond',serif;
  font-size:1.3rem;font-weight:600;color:#B8860B!important;
  letter-spacing:.24em;
  display:flex;align-items:center;gap:6px;line-height:1;
}
.aj-logo-diamond{
  width:6px;height:6px;background:#B8860B;
  transform:rotate(45deg);flex-shrink:0;
  display:inline-block;margin:0 2px;
}
.aj-logo-sub{
  font-family:'DM Sans',sans-serif;
  font-size:.44rem;color:#8B6914!important;
  letter-spacing:.32em;text-transform:uppercase;
}
.aj-nav-links{
  display:flex;gap:26px;list-style:none;margin:0;padding:0;
}
.aj-nav-links a{
  font-family:'DM Sans',sans-serif;
  font-size:.64rem;letter-spacing:.14em;text-transform:uppercase;
  color:#4A3728!important;text-decoration:none!important;
  transition:color .2s;white-space:nowrap;
  padding-bottom:2px;border-bottom:1.5px solid transparent;
}
.aj-nav-links a:hover{color:#B8860B!important;border-bottom-color:#B8860B;}
.aj-nav-right{display:flex;align-items:center;gap:14px;}
.aj-cart-link{
  position:relative;text-decoration:none!important;
  font-size:1.1rem;color:#4A3728!important;
  display:flex;align-items:center;
}
.aj-cart-badge{
  position:absolute;top:-6px;right:-8px;
  background:#9B2335;color:#fff;
  font-size:.48rem;font-weight:700;
  border-radius:50%;width:14px;height:14px;
  display:flex;align-items:center;justify-content:center;
}
.aj-btn-signin{
  font-family:'DM Sans',sans-serif;
  font-size:.62rem;letter-spacing:.13em;text-transform:uppercase;
  background:#1A1008;color:#FFFDF9!important;
  padding:8px 18px;border-radius:2px;
  text-decoration:none!important;transition:background .2s;
}
.aj-btn-signin:hover{background:#B8860B;}
.aj-btn-account{
  font-family:'DM Sans',sans-serif;
  font-size:.62rem;letter-spacing:.13em;text-transform:uppercase;
  border:1.5px solid #B8860B;color:#B8860B!important;
  padding:7px 14px;border-radius:2px;
  text-decoration:none!important;transition:all .2s;
}
.aj-btn-account:hover{background:#B8860B;color:#fff!important;}
.aj-btn-admin{
  font-family:'DM Sans',sans-serif;
  font-size:.62rem;letter-spacing:.13em;text-transform:uppercase;
  background:#1A1008;color:#E8C547!important;
  padding:8px 14px;border-radius:2px;
  text-decoration:none!important;margin-left:4px;
}
.aj-icon-link{
  text-decoration:none!important;
  font-size:1.1rem;color:#4A3728!important;
  display:flex;align-items:center;justify-content:center;
  width:28px;height:28px;
  transition:color .2s;
}
.aj-icon-link:hover{color:#B8860B!important;}

/* TICKER */
.aj-ticker{
  background:#1A1008;padding:10px 5%;
  display:flex;align-items:center;
  justify-content:space-between;flex-wrap:wrap;gap:8px;
}
.aj-ticker-items{display:flex;align-items:center;flex-wrap:wrap;}
.aj-ticker-item{
  padding:0 20px;
  border-right:1px solid rgba(184,134,11,.28);
  display:flex;align-items:center;gap:8px;
}
.aj-ticker-item:first-child{padding-left:0;}
.aj-ticker-item:last-child{border-right:none;}
.aj-ticker-lbl{
  font-family:'DM Sans',sans-serif;
  font-size:.58rem;color:rgba(255,253,249,.45);
  letter-spacing:.14em;text-transform:uppercase;
}
.aj-ticker-val{
  font-family:'DM Sans',sans-serif;
  font-size:1rem;font-weight:600;color:#D4A843;
}
.aj-ticker-unit{font-size:.56rem;color:rgba(212,168,67,.5);}
.aj-ticker-right{display:flex;align-items:center;gap:10px;}
.aj-live-dot{width:6px;height:6px;border-radius:50%;background:#4CAF50;flex-shrink:0;}
.aj-live-txt{
  font-family:'DM Sans',sans-serif;
  font-size:.56rem;color:rgba(255,253,249,.38);letter-spacing:.1em;
}
.aj-bis{
  font-family:'DM Sans',sans-serif;
  font-size:.56rem;letter-spacing:.1em;text-transform:uppercase;
  background:rgba(184,134,11,.16);color:#D4A843;
  border:1px solid rgba(184,134,11,.28);
  padding:3px 10px;border-radius:2px;
}

/* HERO SLIDER - CSS animation */
.aj-hero{
  position:relative;width:100%;
  height:88vh;min-height:520px;max-height:900px;
  overflow:hidden;display:flex;align-items:center;
}
.aj-hero-bg{
  position:absolute;inset:0;z-index:0;
  background:linear-gradient(135deg,
    #2C1608 0%,#4A2E14 25%,#3D2214 60%,#1A1008 100%);
}
.aj-hero-slide{
  position:absolute;inset:0;z-index:1;
  opacity:0;
  animation:heroFade 16.5s infinite;
}
.aj-hero-slide:nth-child(2){animation-delay:0s;}
.aj-hero-slide:nth-child(3){animation-delay:5.5s;}
.aj-hero-slide:nth-child(4){animation-delay:11s;}
@keyframes heroFade{
  0%{opacity:0;}
  5%{opacity:1;}
  30%{opacity:1;}
  35%{opacity:0;}
  100%{opacity:0;}
}
.aj-hero-slide img{
  width:100%;height:100%;
  object-fit:cover;object-position:center;
  opacity:.55;display:block;
}
.aj-hero-overlay{
  position:absolute;inset:0;z-index:2;
  background:linear-gradient(to right,
    rgba(26,16,8,.9) 0%,
    rgba(26,16,8,.65) 40%,
    rgba(26,16,8,.1) 100%);
}
.aj-hero-content{
  position:relative;z-index:3;
  padding:0 6%;max-width:620px;
}
.aj-hero-eyebrow{
  font-family:'DM Sans',sans-serif;
  font-size:.62rem;color:#E8C547;
  letter-spacing:.28em;text-transform:uppercase;
  margin-bottom:22px;
  display:flex;align-items:center;gap:12px;
}
.aj-hero-eyebrow::before{content:'';display:block;width:28px;height:1px;background:#E8C547;}
.aj-hero-h1{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(2.4rem,5.5vw,4.2rem);
  font-weight:600;color:#FFFFFF!important;
  line-height:1.12;margin-bottom:20px;letter-spacing:.02em;
}
.aj-hero-h1 em{font-style:italic;color:#D4A843!important;font-weight:400;}
.aj-hero-sub{
  font-family:'DM Sans',sans-serif;
  font-size:.9rem;color:rgba(255,253,249,.65);
  line-height:1.8;margin-bottom:34px;max-width:460px;
}
.aj-hero-cta{
  font-family:'DM Sans',sans-serif;
  font-size:.7rem;letter-spacing:.18em;text-transform:uppercase;
  background:#B8860B;color:#fff!important;
  padding:15px 38px;border-radius:2px;
  text-decoration:none!important;display:inline-block;
  transition:background .25s;font-weight:500;
}
.aj-hero-cta:hover{background:#9B7209;}
.aj-hero-dots{
  position:absolute;bottom:32px;left:6%;
  display:flex;gap:8px;z-index:4;
}
.aj-hero-dot{
  height:3px;border-radius:2px;
  background:rgba(255,255,255,.25);
  transition:all .4s;cursor:pointer;border:none;padding:0;
}
.aj-hero-dot.active{background:#E8C547;}
.aj-hero-side-tag{
  position:absolute;right:5%;bottom:32px;z-index:4;
  background:rgba(26,16,8,.88);
  border:1px solid rgba(184,134,11,.4);
  padding:12px 20px;border-radius:2px;
}
.aj-hero-side-tag span{
  font-family:'DM Sans',sans-serif;
  font-size:.55rem;color:#E8C547;
  letter-spacing:.14em;text-transform:uppercase;
  display:block;margin-bottom:4px;
}
.aj-hero-side-tag p{
  font-family:'DM Sans',sans-serif;
  font-size:.82rem;color:#FFFDF9;margin:0;font-weight:500;
}

/* SECTIONS */
.aj-section     {padding:72px 5%;}
.aj-section-alt {padding:72px 5%;background:#FFF8EE;}
.aj-section-dark{padding:72px 5%;background:#1A1008;}
.aj-section-gold{padding:72px 5%;background:#F5E6C8;border-top:2px solid #EDD9A3;}

.aj-sec-center{text-align:center;margin-bottom:40px;}
.aj-sec-overline{
  font-family:'DM Sans',sans-serif;
  font-size:.6rem;color:#B8860B;
  letter-spacing:.24em;text-transform:uppercase;
  margin-bottom:10px;
  display:inline-flex;align-items:center;gap:10px;
}
.aj-sec-overline::before,
.aj-sec-overline::after{content:'';display:block;width:20px;height:1px;background:#B8860B;}
.aj-sec-overline-lt{
  font-family:'DM Sans',sans-serif;
  font-size:.6rem;color:#D4A843;
  letter-spacing:.24em;text-transform:uppercase;
  margin-bottom:10px;
  display:inline-flex;align-items:center;gap:10px;
}
.aj-sec-overline-lt::before,
.aj-sec-overline-lt::after{content:'';display:block;width:20px;height:1px;background:#D4A843;}
.aj-sec-title{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(2rem,3.5vw,3rem);
  font-weight:600;color:#1A1008;letter-spacing:.02em;line-height:1.2;
}
.aj-sec-title-lt{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(2rem,3.5vw,3rem);
  font-weight:600;color:#FFFDF9;letter-spacing:.02em;line-height:1.2;
}

/* CATEGORY GRID */
.aj-cat-grid{
  display:grid;grid-template-columns:repeat(5,1fr);
  gap:14px;
}
.aj-cat-card{
  border-radius:6px;overflow:hidden;
  position:relative;cursor:pointer;
  text-decoration:none!important;
  display:block;height:260px;
  transition:transform .35s,box-shadow .35s;
  background:linear-gradient(160deg,#3D2214,#8B6914);
}
.aj-cat-card:hover{
  transform:translateY(-6px);
  box-shadow:0 16px 40px rgba(184,134,11,.35);
}
.aj-cat-img{
  position:absolute;top:0;left:0;
  width:100%;height:100%;
  object-fit:cover;object-position:center;
  z-index:1;
  transition:transform .55s;display:block;
}
.aj-cat-card:hover .aj-cat-img{transform:scale(1.07);}
.aj-cat-overlay{
  position:absolute;inset:0;z-index:2;
  background:linear-gradient(to top,
    rgba(26,16,8,.88) 0%,rgba(26,16,8,.3) 50%,rgba(26,16,8,.05) 100%);
}
.aj-cat-info{
  position:absolute;bottom:0;left:0;right:0;
  padding:16px;text-align:center;z-index:3;
}
.aj-cat-name{
  font-family:'DM Sans',sans-serif;
  font-size:.78rem;color:#FFFDF9!important;
  letter-spacing:.16em;text-transform:uppercase;
  font-weight:600;text-decoration:none!important;
}

/* PRODUCT GRID */
.aj-prod-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;}
.aj-prod-card{
  background:#fff;border-radius:8px;overflow:hidden;
  border:1px solid #EDD9A3;
  box-shadow:0 2px 16px rgba(184,134,11,.08);
  transition:transform .35s,box-shadow .35s;
  text-decoration:none!important;color:inherit;display:block;
}
.aj-prod-card:hover{
  transform:translateY(-7px);
  box-shadow:0 18px 44px rgba(184,134,11,.2);
}
.aj-prod-img-wrap{
  aspect-ratio:1;overflow:hidden;position:relative;
  background:linear-gradient(135deg,#F5E6C8,#EDD9A3);
}
.aj-prod-img{
  width:100%;height:100%;object-fit:cover;
  transition:transform .55s;display:block;
}
.aj-prod-card:hover .aj-prod-img{transform:scale(1.07);}
.aj-prod-karat{
  position:absolute;top:10px;left:10px;z-index:1;
  font-family:'DM Sans',sans-serif;font-size:.56rem;
  letter-spacing:.1em;background:#1A1008;color:#E8C547;
  padding:3px 9px;border-radius:2px;font-weight:500;
}
.aj-prod-wish{
  position:absolute;top:10px;right:10px;z-index:1;
  width:28px;height:28px;border-radius:50%;
  background:rgba(255,253,249,.92);
  border:1px solid #EDD9A3;
  display:flex;align-items:center;justify-content:center;
  font-size:.9rem;color:#4A3728;
  cursor:pointer;
  transition:all .2s;
}
.aj-prod-wish:hover{background:#B8860B;color:#fff;border-color:#B8860B;}
.aj-prod-body{padding:16px 18px 20px;}
.aj-prod-cat{
  font-family:'DM Sans',sans-serif;font-size:.55rem;
  color:#B8860B;letter-spacing:.16em;text-transform:uppercase;
  margin-bottom:7px;font-weight:500;
}
.aj-prod-name{
  font-family:'Cormorant Garamond',serif;
  font-size:1.05rem;font-weight:500;color:#1A1008;
  line-height:1.35;margin-bottom:10px;
}
.aj-prod-meta{display:flex;align-items:center;gap:8px;margin-bottom:12px;}
.aj-prod-wt{
  font-family:'DM Sans',sans-serif;font-size:.6rem;
  color:#8B6914;background:#F5E6C8;
  padding:3px 9px;border-radius:2px;font-weight:500;
}
.aj-prod-making{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;}
.aj-prod-divider{height:1px;background:#F0E4C4;margin-bottom:12px;}
.aj-prod-price-row{display:flex;align-items:center;justify-content:space-between;}
.aj-prod-price{
  font-family:'DM Sans',sans-serif;
  font-size:1.1rem;font-weight:600;color:#B8860B;
}
.aj-prod-add{
  font-family:'DM Sans',sans-serif;font-size:.58rem;
  letter-spacing:.1em;text-transform:uppercase;
  background:#1A1008;color:#FFFDF9;
  padding:7px 13px;border-radius:2px;
  cursor:pointer;border:none;transition:background .2s;font-weight:500;
}
.aj-prod-add:hover{background:#B8860B;}

/* PROMISE */
.aj-promise-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;}
.aj-promise-card{
  border:1px solid #EDD9A3;border-radius:8px;
  padding:26px 22px;position:relative;overflow:hidden;
  background:#fff;
  box-shadow:0 2px 14px rgba(184,134,11,.07);
  transition:transform .3s,box-shadow .3s;
}
.aj-promise-card:hover{
  transform:translateY(-5px);
  box-shadow:0 12px 32px rgba(184,134,11,.15);
}
.aj-promise-card::before{
  content:'';position:absolute;
  top:0;left:0;width:3px;height:100%;background:#B8860B;
}
.aj-promise-num{
  font-family:'DM Sans',sans-serif;
  font-size:2.6rem;font-weight:700;color:#F5E6C8;
  position:absolute;top:10px;right:16px;line-height:1;
}
.aj-promise-icon{font-size:1.7rem;margin-bottom:14px;display:block;}
.aj-promise-title{
  font-family:'DM Sans',sans-serif;
  font-size:.82rem;font-weight:600;color:#1A1008;margin-bottom:9px;
}
.aj-promise-text{
  font-family:'DM Sans',sans-serif;font-size:.72rem;color:#8B6914;line-height:1.65;
}

/* LOYALTY */
.aj-loyalty-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
.aj-lcard{
  border:1px solid rgba(184,134,11,.22);
  border-radius:8px;padding:22px 18px;transition:transform .3s;
}
.aj-lcard:hover{transform:translateY(-3px);}
.aj-lcard.active{border-color:#B8860B;background:rgba(184,134,11,.09);}
.aj-ltier{
  font-family:'DM Sans',sans-serif;font-size:.62rem;
  letter-spacing:.16em;text-transform:uppercase;margin-bottom:14px;
  display:inline-block;padding:4px 14px;border-radius:20px;font-weight:600;
}
.lt-m{background:rgba(255,255,255,.07);color:rgba(255,253,249,.45);}
.lt-s{background:rgba(189,189,189,.15);color:#BDBDBD;}
.lt-g{background:rgba(184,134,11,.2);color:#D4A843;}
.lt-p{background:rgba(84,110,122,.25);color:#B0BEC5;}
.aj-ldisc{
  font-family:'DM Sans',sans-serif;
  font-size:2rem;font-weight:700;color:#D4A843;margin-bottom:5px;
}
.aj-lthresh{
  font-family:'DM Sans',sans-serif;
  font-size:.66rem;color:rgba(255,253,249,.42);margin-bottom:12px;
}
.aj-lbar{height:2px;background:rgba(255,255,255,.08);border-radius:2px;overflow:hidden;}
.aj-lfill{height:100%;border-radius:2px;background:linear-gradient(to right,#B8860B,#E8C547);}

/* GOLD RATES */
.aj-rates-header{
  display:flex;justify-content:space-between;
  align-items:flex-end;margin-bottom:28px;flex-wrap:wrap;gap:12px;
}
.aj-metal-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;}
.aj-metal-card{
  background:#fff;border:1px solid #EDD9A3;
  border-radius:8px;padding:24px;
  box-shadow:0 2px 14px rgba(184,134,11,.07);
}
.aj-metal-top{
  display:flex;align-items:center;
  justify-content:space-between;margin-bottom:16px;
}
.aj-metal-type{
  font-family:'DM Sans',sans-serif;font-size:.62rem;
  color:#8B6914;letter-spacing:.14em;text-transform:uppercase;font-weight:500;
}
.aj-metal-badge{
  font-family:'DM Sans',sans-serif;font-size:.6rem;
  background:#1A1008;color:#E8C547;
  padding:3px 10px;border-radius:2px;letter-spacing:.08em;font-weight:500;
}
.aj-metal-price{
  font-family:'DM Sans',sans-serif;
  font-size:2.2rem;font-weight:700;color:#B8860B;
  line-height:1;margin-bottom:5px;
}
.aj-metal-unit{font-family:'DM Sans',sans-serif;font-size:.63rem;color:#8B6914;margin-bottom:16px;}
.aj-metal-divider{height:1px;background:#EDD9A3;margin-bottom:16px;}
.aj-inr-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:14px;}
.aj-inr-row{
  display:flex;justify-content:space-between;
  background:#FFF8EE;border-radius:4px;padding:7px 10px;
}
.aj-inr-lbl{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;}
.aj-inr-val{font-family:'DM Sans',sans-serif;font-size:.66rem;font-weight:600;color:#1A1008;}
.aj-conv-title{
  font-family:'DM Sans',sans-serif;font-size:.56rem;color:#8B6914;
  letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px;font-weight:500;
}
.aj-conv-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px;}
.aj-conv-row{
  display:flex;align-items:center;justify-content:space-between;
  background:#F5E6C8;border-radius:4px;padding:5px 10px;
}
.aj-conv-code{font-family:'DM Sans',sans-serif;font-size:.6rem;color:#8B6914;font-weight:500;}
.aj-conv-val{font-family:'DM Sans',sans-serif;font-size:.66rem;font-weight:600;color:#4A3728;}

/* FOOTER */
.aj-footer{
  background:#3D1F0E;
  border-top:3px solid #5C3420;
  padding:60px 5% 30px;
  display:block;width:100%;
}
.aj-footer-grid{
  display:grid;grid-template-columns:2fr 1fr 1fr 1fr;
  gap:44px;margin-bottom:44px;
}
.aj-footer-logo-main{
  font-family:'Cormorant Garamond',serif;
  font-size:1.1rem;font-weight:600;color:#D4A843;
  letter-spacing:.24em;display:flex;align-items:center;gap:6px;margin-bottom:3px;
}
.aj-footer-logo-diamond{
  width:5px;height:5px;background:#D4A843;
  transform:rotate(45deg);flex-shrink:0;opacity:.8;display:inline-block;
}
.aj-footer-logo-rule{
  width:100%;height:.7px;
  background:linear-gradient(to right,transparent,#B8860B,transparent);
  margin:5px 0;
}
.aj-footer-logo-sub{
  font-family:'DM Sans',sans-serif;
  font-size:.44rem;color:rgba(212,168,67,.45);
  letter-spacing:.3em;text-transform:uppercase;
}
.aj-footer-tagline{
  font-family:'DM Sans',sans-serif;
  font-size:.82rem;color:rgba(255,253,249,.38);
  line-height:1.75;margin-top:16px;margin-bottom:16px;
}
.aj-footer-gstin{
  font-family:'DM Sans',sans-serif;font-size:.6rem;
  color:rgba(212,168,67,.4);background:rgba(184,134,11,.1);
  padding:4px 12px;border-radius:2px;display:inline-block;
}
.aj-footer-col-title{
  font-family:'DM Sans',sans-serif;font-size:.6rem;
  color:rgba(212,168,67,.55);letter-spacing:.2em;
  text-transform:uppercase;margin-bottom:16px;font-weight:600;
}
.aj-footer-links{list-style:none;padding:0;margin:0;}
.aj-footer-links li{margin-bottom:11px;}
.aj-footer-links a{
  font-family:'DM Sans',sans-serif;font-size:.8rem;
  color:rgba(255,253,249,.38)!important;
  text-decoration:none!important;transition:color .2s;
}
.aj-footer-links a:hover{color:#D4A843!important;}
.aj-footer-bottom{
  border-top:1px solid rgba(255,255,255,.08);
  padding-top:22px;display:flex;
  justify-content:space-between;align-items:center;
  flex-wrap:wrap;gap:8px;
}
.aj-footer-copy{
  font-family:'DM Sans',sans-serif;
  font-size:.62rem;color:rgba(255,253,249,.25);
}

/* RESPONSIVE */
@media(max-width:1200px){
  .aj-prod-grid{grid-template-columns:repeat(3,1fr);}
  .aj-footer-grid{grid-template-columns:1fr 1fr;gap:30px;}
}
@media(max-width:1000px){
  .aj-cat-grid{grid-template-columns:repeat(3,1fr);}
  .aj-promise-grid{grid-template-columns:repeat(2,1fr);}
  .aj-loyalty-grid{grid-template-columns:repeat(2,1fr);}
  .aj-metal-grid{grid-template-columns:repeat(2,1fr);}
}
@media(max-width:768px){
  .aj-nav{padding:0 4%;height:60px;}
  .aj-nav-links{display:none;}
  .aj-hero{height:72vh;min-height:420px;}
  .aj-section,.aj-section-alt,
  .aj-section-dark,.aj-section-gold{padding:48px 5%;}
  .aj-cat-grid{grid-template-columns:repeat(2,1fr);}
  .aj-prod-grid{grid-template-columns:repeat(2,1fr);gap:12px;}
  .aj-promise-grid{grid-template-columns:1fr 1fr;gap:12px;}
  .aj-loyalty-grid{grid-template-columns:1fr 1fr;}
  .aj-metal-grid{grid-template-columns:1fr;}
  .aj-footer-grid{grid-template-columns:1fr;gap:24px;}
  .aj-hero-side-tag{display:none;}
}
@media(max-width:480px){
  .aj-cat-grid{grid-template-columns:1fr 1fr;}
  .aj-prod-grid{grid-template-columns:1fr 1fr;gap:10px;}
  .aj-promise-grid{grid-template-columns:1fr;}
  .aj-loyalty-grid{grid-template-columns:1fr 1fr;}
  .aj-hero-h1{font-size:2.1rem;}
}
</style>
"""
    + '<nav class="aj-nav">'
    + '<a href="/" class="aj-logo">'
    + '<div class="aj-logo-main">AURUS<span class="aj-logo-diamond"></span>JEWELS</div>'
    + '<div class="aj-logo-sub">Fine Gold &amp; Silver &middot; BIS Hallmarked</div>'
    + '</a>'
    + '<ul class="aj-nav-links">'
    + '<li><a href="/Catalogue">Catalogue</a></li>'
    + '<li><a href="/Catalogue?cat=pendants">Pendants</a></li>'
    + '<li><a href="/Catalogue?cat=rings">Rings</a></li>'
    + '<li><a href="/Catalogue?cat=earrings">Earrings</a></li>'
    + '<li><a href="/Catalogue?cat=bracelets">Bracelets</a></li>'
    + '<li><a href="/Catalogue?cat=chains">Chains</a></li>'
    + '</ul>'
    + '<div class="aj-nav-right">'
    + _wish_icon
    + '<a href="/Cart" class="aj-cart-link">&#128722;' + badge + '</a>'
    + _profile_icon
    + _auth
    + '</div>'
    + '</nav>',
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════
# RATE TICKER
# ════════════════════════════════════════════════════════════
st.markdown(
    '<div class="aj-ticker">'
    '<div class="aj-ticker-items">'
    '<div class="aj-ticker-item">'
    '<span class="aj-ticker-lbl">Gold 22K</span>'
    '<span class="aj-ticker-val">' + r22k_str + '</span>'
    '<span class="aj-ticker-unit">/g</span>'
    '</div>'
    '<div class="aj-ticker-item">'
    '<span class="aj-ticker-lbl">Gold 18K</span>'
    '<span class="aj-ticker-val">' + r18k_str + '</span>'
    '<span class="aj-ticker-unit">/g</span>'
    '</div>'
    '<div class="aj-ticker-item">'
    '<span class="aj-ticker-lbl">Silver 925</span>'
    '<span class="aj-ticker-val">' + r925_str + '</span>'
    '<span class="aj-ticker-unit">/g</span>'
    '</div>'
    '</div>'
    '<div class="aj-ticker-right">'
    '<div class="aj-live-dot"></div>'
    '<span class="aj-live-txt">Live IBJA &middot; Updates 9 AM daily</span>'
    '<span class="aj-bis">BIS Hallmarked</span>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════
# HERO SLIDER
# ════════════════════════════════════════════════════════════
h1 = img_url("static/images/hero/hero_1.jpg")
h2 = img_url("static/images/hero/hero_2.jpg")
h3 = img_url("static/images/hero/hero_3.jpg")

st.markdown(
    '<div class="aj-hero">'
    '<div class="aj-hero-bg"></div>'
    '<div class="aj-hero-slide" style="animation-delay:0s;">'
    '<img src="' + h1 + '" alt="hero 1">'
    '</div>'
    '<div class="aj-hero-slide" style="animation-delay:5.5s;">'
    '<img src="' + h2 + '" alt="hero 2">'
    '</div>'
    '<div class="aj-hero-slide" style="animation-delay:11s;">'
    '<img src="' + h3 + '" alt="hero 3">'
    '</div>'
    '<div class="aj-hero-overlay"></div>'
    '<div class="aj-hero-content">'
    '<div class="aj-hero-eyebrow">'
    'New Collection &middot; Spring 2026'
    '</div>'
    '<h1 class="aj-hero-h1" style="color:#FFFFFF!important;">'
    'Where Gold Speaks<br>In <em style="color:#D4A843!important;">Living Prices</em>'
    '</h1>'
    '<p class="aj-hero-sub">'
    "Every piece priced live from today's official IBJA gold rate. "
    "No hidden margins. Just pure gold, fairly priced."
    '</p>'
    '<a class="aj-hero-cta" href="/Catalogue">'
    'Explore Collection'
    '</a>'
    '</div>'
    '<div class="aj-hero-side-tag">'
    '<span>BIS Hallmarked</span>'
    '<p>22K &middot; 18K &middot; 925 Silver</p>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════
# CATEGORIES
# ════════════════════════════════════════════════════════════
categories = execute_query(
    "SELECT * FROM dim_categories ORDER BY display_order"
)

cat_html = (
    '<div class="aj-section">'
    '<div class="aj-sec-center">'
    '<div class="aj-sec-overline">Collections</div>'
    '<div class="aj-sec-title">Shop by Category</div>'
    '</div>'
    '<div class="aj-cat-grid">'
)
for cat in categories:
    img_src = img_url(cat["image_path"])
    cat_html += (
        '<a href="/Catalogue?cat=' + cat["slug"] + '" class="aj-cat-card">'
        '<img src="' + img_src + '" class="aj-cat-img" alt="' + cat["name"] + '">'
        '<div class="aj-cat-overlay"></div>'
        '<div class="aj-cat-info">'
        '<div class="aj-cat-name">' + cat["name"] + '</div>'
        '</div>'
        '</a>'
    )
cat_html += '</div></div>'
st.markdown(cat_html, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# FEATURED PRODUCTS
# ════════════════════════════════════════════════════════════
featured = execute_query(
    "SELECT * FROM v_featured_products ORDER BY product_id LIMIT 8"
)

feat_html = (
    '<div class="aj-section-alt">'
    '<div class="aj-sec-center">'
    '<div class="aj-sec-overline">Handpicked</div>'
    '<div class="aj-sec-title">Featured Pieces</div>'
    '</div>'
    '<div class="aj-prod-grid">'
)
for p in featured:
    pr      = price_product(p)
    price_s = format_inr(pr["final_price"])
    making  = str(int(float(p["making_pct"]) * 100))
    img_src = img_url(p["image_main"])
    wt      = str(round(float(p["weight_g"]), 1))
    feat_html += (
        '<a href="/Product?id=' + str(p["product_id"]) + '" class="aj-prod-card">'
        '<div class="aj-prod-img-wrap">'
        '<img src="' + img_src + '" class="aj-prod-img" alt="' + p["name"] + '">'
        '<span class="aj-prod-karat">' + p["karat"] + '</span>'
        '<span class="aj-prod-wish" '
        'onclick="event.preventDefault();event.stopPropagation();'
        'window.location.href=\'/Wishlist?add=' + str(p["product_id"]) + '\'"'
        ' title="Add to Wishlist">&#9825;</span>'
        '</div>'
        '<div class="aj-prod-body">'
        '<div class="aj-prod-cat">' + p["category_name"] + '</div>'
        '<div class="aj-prod-name">' + p["name"] + '</div>'
        '<div class="aj-prod-meta">'
        '<span class="aj-prod-wt">' + wt + 'g</span>'
        '<span class="aj-prod-making">&middot; Making ' + making + '%</span>'
        '</div>'
        '<div class="aj-prod-divider"></div>'
        '<div class="aj-prod-price-row">'
        '<span class="aj-prod-price">' + price_s + '</span>'
        '<span class="aj-prod-add">Add to Cart</span>'
        '</div>'
        '</div>'
        '</a>'
    )
feat_html += '</div></div>'
st.markdown(feat_html, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# PROMISE
# ════════════════════════════════════════════════════════════
st.markdown(
    '<div class="aj-section">'
    '<div class="aj-sec-center">'
    '<div class="aj-sec-overline">Why Aurus</div>'
    '<div class="aj-sec-title">The Aurus Promise</div>'
    '</div>'
    '<div class="aj-promise-grid">'
    '<div class="aj-promise-card">'
    '<div class="aj-promise-num">01</div>'
    '<span class="aj-promise-icon">&#9878;&#65039;</span>'
    '<div class="aj-promise-title">Live Gold Pricing</div>'
    '<div class="aj-promise-text">Every price recalculates daily from the official IBJA rate. What you see is exactly what gold is worth today.</div>'
    '</div>'
    '<div class="aj-promise-card">'
    '<div class="aj-promise-num">02</div>'
    '<span class="aj-promise-icon">&#127941;</span>'
    '<div class="aj-promise-title">BIS Hallmarked</div>'
    '<div class="aj-promise-text">Every single piece carries a BIS hallmark certificate &mdash; your assurance of certified metal purity.</div>'
    '</div>'
    '<div class="aj-promise-card">'
    '<div class="aj-promise-num">03</div>'
    '<span class="aj-promise-icon">&#128221;</span>'
    '<div class="aj-promise-title">GST Invoice</div>'
    '<div class="aj-promise-text">A complete GST invoice with CGST + SGST breakdown is auto-generated and emailed on every order.</div>'
    '</div>'
    '<div class="aj-promise-card">'
    '<div class="aj-promise-num">04</div>'
    '<span class="aj-promise-icon">&#128081;</span>'
    '<div class="aj-promise-title">Loyalty Rewards</div>'
    '<div class="aj-promise-text">Earn Silver, Gold and Platinum status with exclusive discounts on every purchase.</div>'
    '</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════
# LOYALTY
# ════════════════════════════════════════════════════════════
st.markdown(
    '<div class="aj-section-dark">'
    '<div class="aj-sec-center">'
    '<div class="aj-sec-overline-lt">Rewards Programme</div>'
    '<div class="aj-sec-title-lt">Loyalty Programme</div>'
    '<p style="font-family:\'DM Sans\',sans-serif;font-size:.76rem;'
    'color:rgba(255,253,249,.38);margin-top:10px;">'
    'The more you treasure, the more you save</p>'
    '</div>'
    '<div class="aj-loyalty-grid">'
    '<div class="aj-lcard">'
    '<span class="aj-ltier lt-m">Member</span>'
    '<div class="aj-ldisc">Welcome</div>'
    '<div class="aj-lthresh">Starting tier</div>'
    '<div class="aj-lbar"><div class="aj-lfill" style="width:8%"></div></div>'
    '</div>'
    '<div class="aj-lcard">'
    '<span class="aj-ltier lt-s">Silver</span>'
    '<div class="aj-ldisc">3% Off</div>'
    '<div class="aj-lthresh">At &#8377;50,000 spend</div>'
    '<div class="aj-lbar"><div class="aj-lfill" style="width:33%"></div></div>'
    '</div>'
    '<div class="aj-lcard active">'
    '<span class="aj-ltier lt-g">Gold</span>'
    '<div class="aj-ldisc">5% Off</div>'
    '<div class="aj-lthresh">At &#8377;1,50,000 spend</div>'
    '<div class="aj-lbar"><div class="aj-lfill" style="width:66%"></div></div>'
    '</div>'
    '<div class="aj-lcard">'
    '<span class="aj-ltier lt-p">Platinum</span>'
    '<div class="aj-ldisc">5% + Perks</div>'
    '<div class="aj-lthresh">At &#8377;5,00,000 spend</div>'
    '<div class="aj-lbar"><div class="aj-lfill" style="width:100%"></div></div>'
    '</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════
# LIVE GOLD RATES
# ════════════════════════════════════════════════════════════
st.markdown(
    '<div class="aj-section-gold">'
    '<div class="aj-rates-header">'
    '<div>'
    '<div style="font-family:\'DM Sans\',sans-serif;font-size:.6rem;'
    'color:#B8860B;letter-spacing:.24em;text-transform:uppercase;'
    'margin-bottom:10px;display:flex;align-items:center;gap:8px;">'
    '<span style="display:block;width:16px;height:1px;background:#B8860B;"></span>'
    'Today\'s Market'
    '</div>'
    '<div style="font-family:\'Cormorant Garamond\',serif;'
    'font-size:clamp(1.7rem,3vw,2.4rem);font-weight:600;'
    'color:#1A1008;letter-spacing:.02em;">'
    'Live Gold &amp; Silver Rates'
    '</div>'
    '</div>'
    '<div style="display:flex;align-items:center;gap:8px;">'
    '<div style="width:7px;height:7px;border-radius:50%;'
    'background:#4CAF50;flex-shrink:0;"></div>'
    '<span style="font-family:\'DM Sans\',sans-serif;'
    'font-size:.63rem;color:#8B6914;">'
    'Updated &middot; ' + today_str + ' &middot; Source: IBJA'
    '</span>'
    '</div>'
    '</div>'
    '<div class="aj-metal-grid">'
    '<div class="aj-metal-card">'
    '<div class="aj-metal-top">'
    '<span class="aj-metal-type">Gold</span>'
    '<span class="aj-metal-badge">22 Karat</span>'
    '</div>'
    '<div class="aj-metal-price">' + r22k_str + '</div>'
    '<div class="aj-metal-unit">per gram &middot; INR</div>'
    '<div class="aj-metal-divider"></div>'
    '<div class="aj-inr-grid">'
    '<div class="aj-inr-row"><span class="aj-inr-lbl">Per 10g</span>'
    '<span class="aj-inr-val">' + r22k_10 + '</span></div>'
    '<div class="aj-inr-row"><span class="aj-inr-lbl">Per 100g</span>'
    '<span class="aj-inr-val">' + r22k_100 + '</span></div>'
    '</div>'
    '<div class="aj-conv-title">Approx. in other currencies</div>'
    '<div class="aj-conv-grid">'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127482;&#127480; USD</span>'
    '<span class="aj-conv-val">$' + r22k_usd + '/g</span></div>'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127468;&#127463; GBP</span>'
    '<span class="aj-conv-val">&pound;' + r22k_gbp + '/g</span></div>'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127466;&#127482; EUR</span>'
    '<span class="aj-conv-val">&euro;' + r22k_eur + '/g</span></div>'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127462;&#127466; AED</span>'
    '<span class="aj-conv-val">' + r22k_aed + '/g</span></div>'
    '</div>'
    '</div>'
    '<div class="aj-metal-card">'
    '<div class="aj-metal-top">'
    '<span class="aj-metal-type">Gold</span>'
    '<span class="aj-metal-badge">18 Karat</span>'
    '</div>'
    '<div class="aj-metal-price">' + r18k_str + '</div>'
    '<div class="aj-metal-unit">per gram &middot; INR</div>'
    '<div class="aj-metal-divider"></div>'
    '<div class="aj-inr-grid">'
    '<div class="aj-inr-row"><span class="aj-inr-lbl">Per 10g</span>'
    '<span class="aj-inr-val">' + r18k_10 + '</span></div>'
    '<div class="aj-inr-row"><span class="aj-inr-lbl">Per 100g</span>'
    '<span class="aj-inr-val">' + r18k_100 + '</span></div>'
    '</div>'
    '<div class="aj-conv-title">Approx. in other currencies</div>'
    '<div class="aj-conv-grid">'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127482;&#127480; USD</span>'
    '<span class="aj-conv-val">$' + r18k_usd + '/g</span></div>'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127468;&#127463; GBP</span>'
    '<span class="aj-conv-val">&pound;' + r18k_gbp + '/g</span></div>'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127466;&#127482; EUR</span>'
    '<span class="aj-conv-val">&euro;' + r18k_eur + '/g</span></div>'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127462;&#127466; AED</span>'
    '<span class="aj-conv-val">' + r18k_aed + '/g</span></div>'
    '</div>'
    '</div>'
    '<div class="aj-metal-card">'
    '<div class="aj-metal-top">'
    '<span class="aj-metal-type">Silver</span>'
    '<span class="aj-metal-badge">925 Sterling</span>'
    '</div>'
    '<div class="aj-metal-price">' + r925_str + '</div>'
    '<div class="aj-metal-unit">per gram &middot; INR</div>'
    '<div class="aj-metal-divider"></div>'
    '<div class="aj-inr-grid">'
    '<div class="aj-inr-row"><span class="aj-inr-lbl">Per 10g</span>'
    '<span class="aj-inr-val">' + r925_10 + '</span></div>'
    '<div class="aj-inr-row"><span class="aj-inr-lbl">Per 100g</span>'
    '<span class="aj-inr-val">' + r925_100 + '</span></div>'
    '</div>'
    '<div class="aj-conv-title">Approx. in other currencies</div>'
    '<div class="aj-conv-grid">'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127482;&#127480; USD</span>'
    '<span class="aj-conv-val">$' + r925_usd + '/g</span></div>'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127468;&#127463; GBP</span>'
    '<span class="aj-conv-val">&pound;' + r925_gbp + '/g</span></div>'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127466;&#127482; EUR</span>'
    '<span class="aj-conv-val">&euro;' + r925_eur + '/g</span></div>'
    '<div class="aj-conv-row"><span class="aj-conv-code">&#127462;&#127466; AED</span>'
    '<span class="aj-conv-val">' + r925_aed + '/g</span></div>'
    '</div>'
    '</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════
st.markdown(
    '<div class="aj-footer">'
    '<div class="aj-footer-grid">'
    '<div>'
    '<div class="aj-footer-logo-main">'
    'AURUS<span class="aj-footer-logo-diamond"></span>JEWELS'
    '</div>'
    '<div class="aj-footer-logo-rule"></div>'
    '<div class="aj-footer-logo-sub">'
    'Fine Gold &amp; Silver &middot; BIS Hallmarked'
    '</div>'
    '<p class="aj-footer-tagline">'
    'Fine hallmarked jewellery priced live from the official '
    'IBJA gold rate. Transparency is our craft.'
    '</p>'
    '<span class="aj-footer-gstin">GSTIN: 07AABCS1429B1Z6</span>'
    '</div>'
    '<div>'
    '<div class="aj-footer-col-title">Shop</div>'
    '<ul class="aj-footer-links">'
    '<li><a href="/Catalogue?cat=pendants">Pendants</a></li>'
    '<li><a href="/Catalogue?cat=rings">Rings</a></li>'
    '<li><a href="/Catalogue?cat=earrings">Earrings</a></li>'
    '<li><a href="/Catalogue?cat=bracelets">Bracelets</a></li>'
    '<li><a href="/Catalogue?cat=chains">Chains</a></li>'
    '</ul>'
    '</div>'
    '<div>'
    '<div class="aj-footer-col-title">Account</div>'
    '<ul class="aj-footer-links">'
    '<li><a href="/Login">Sign In</a></li>'
    '<li><a href="/Login">Register</a></li>'
    '<li><a href="/Profile">My Orders</a></li>'
    '<li><a href="/Profile">Wishlist</a></li>'
    '</ul>'
    '</div>'
    '<div>'
    '<div class="aj-footer-col-title">Support</div>'
    '<ul class="aj-footer-links">'
    '<li><a href="#">About Us</a></li>'
    '<li><a href="#">BIS Hallmarking</a></li>'
    '<li><a href="#">Pricing Policy</a></li>'
    '<li><a href="#">Contact Us</a></li>'
    '</ul>'
    '</div>'
    '</div>'
    '<div class="aj-footer-bottom">'
    '<span class="aj-footer-copy">'
    '&copy; 2026 Aurus Jewels. All rights reserved. '
    'All products BIS hallmarked.'
    '</span>'
    '<span class="aj-footer-copy">'
    'Prices update daily from IBJA official gold rates.'
    '</span>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)