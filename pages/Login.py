"""
pages/Login.py — Aurus Jewels Login & Register Page
"""
import streamlit as st
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.session import init_session, login_session, is_logged_in, get_role
from core.auth    import login_customer, register_customer, google_login_or_register, generate_token
import config

st.set_page_config(
    page_title            = "Sign In — Aurus Jewels",
    page_icon             = "✦",
    layout                = "wide",
    initial_sidebar_state = "collapsed",
)

init_session()

# ── already logged in ────────────────────────────────────────
if is_logged_in():
    st.switch_page("Home.py" if get_role() != "admin" else "pages/Admin.py")

# ── nav redirect ─────────────────────────────────────────────
PAGE_MAP = {
    "Home":"Home.py","Catalogue":"pages/Catalogue.py",
    "Product":"pages/Product.py","Cart":"pages/Cart.py",
    "Checkout":"pages/Checkout.py","Profile":"pages/Profile.py",
    "Login":"pages/Login.py","Admin":"pages/Admin.py",
}
_nav = st.query_params.get("_nav","")
if _nav and _nav in PAGE_MAP and _nav != "Login":
    st.query_params.clear(); st.switch_page(PAGE_MAP[_nav])

# ── Google callback ──────────────────────────────────────────
_code = st.query_params.get("code","")
if _code:
    with st.spinner("Signing you in with Google…"):
        customer, err = google_login_or_register(_code)
    if customer:
        token = generate_token(customer)
        login_session(customer, token)
        st.query_params.clear()
        st.switch_page("Home.py")
    else:
        st.error(err)

# ── tab state ────────────────────────────────────────────────
if "login_tab" not in st.session_state:
    st.session_state["login_tab"] = "signin"
_tp = st.query_params.get("tab","")
if _tp in ("signin","register"):
    st.session_state["login_tab"] = _tp
tab = st.session_state["login_tab"]

# ── Google OAuth URL ─────────────────────────────────────────
G_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth"
    "?response_type=code"
    f"&client_id={config.GOOGLE_CLIENT_ID}"
    "&redirect_uri=http://localhost:8502/Login"
    "&scope=openid%20email%20profile"
    "&access_type=offline&prompt=consent"
)

G_ICON = (
    '<svg width="16" height="16" viewBox="0 0 24 24" style="flex-shrink:0">'
    '<path fill="#4285F4" d="M23.745 12.27c0-.79-.07-1.54-.19-2.27h-11.3v4.51h6.47'
    'c-.29 1.48-1.14 2.73-2.4 3.58v3h3.86c2.26-2.09 3.56-5.17 3.56-8.82z"/>'
    '<path fill="#34A853" d="M12.255 24c3.24 0 5.95-1.08 7.93-2.91l-3.86-3'
    'c-1.08.72-2.45 1.16-4.07 1.16-3.13 0-5.78-2.11-6.73-4.96h-3.98v3.09'
    'C3.515 21.3 7.565 24 12.255 24z"/>'
    '<path fill="#FBBC05" d="M5.525 14.29c-.25-.72-.38-1.49-.38-2.29s.14-1.57'
    '.38-2.29V6.62h-3.98a11.86 11.86 0 000 10.76l3.98-3.09z"/>'
    '<path fill="#EA4335" d="M12.255 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42'
    'C18.205 1.19 15.495 0 12.255 0c-4.69 0-8.74 2.7-10.71 6.62l3.98 3.09'
    'c.95-2.85 3.6-4.96 6.73-4.96z"/></svg>'
)

# ════════════════════════════════════════════════════════════
# CSS — key: style the columns themselves, not wrapper divs
# ════════════════════════════════════════════════════════════
st.markdown('<base target="_parent">', unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

#MainMenu,footer,header{display:none!important;}
[data-testid="stAppViewContainer"]>.main{padding:0!important;}
[data-testid="stHeader"]{display:none!important;}
section[data-testid="stSidebar"]{display:none!important;}
.block-container{padding:0!important;max-width:100%!important;}
.element-container{margin:0!important;}
div[data-testid="stVerticalBlock"]>div{gap:0!important;}
*{box-sizing:border-box;}
a{text-decoration:none!important;}

/* ── Force columns flush, no gap ────────────────────────── */
[data-testid="stHorizontalBlock"]{
  gap:0!important;padding:0!important;align-items:stretch!important;
}
[data-testid="stHorizontalBlock"]>div{padding:0!important;}

/* ── Left column — dark walnut ──────────────────────────── */
[data-testid="stHorizontalBlock"]>div:first-child{
  background:linear-gradient(150deg,#2C1608 0%,#4A2E14 45%,#1A1008 100%)!important;
  position:relative;overflow:hidden;
}

/* ── Right column — ivory ───────────────────────────────── */
[data-testid="stHorizontalBlock"]>div:last-child{
  background:#FFFDF9!important;
  border-left:1.5px solid #E8D5A3;
  padding:0 52px!important;
  display:flex!important;flex-direction:column!important;
  justify-content:center!important;
}

/* ── App background matches left ────────────────────────── */
.stApp{background:#1A1008!important;}

/* ── Left panel HTML ────────────────────────────────────── */
.ajl{
  padding:52px 48px;min-height:100vh;
  display:flex;flex-direction:column;justify-content:space-between;
  position:relative;z-index:1;
}
.ajl-glow1{
  position:absolute;right:-60px;top:-60px;
  width:340px;height:340px;border-radius:50%;
  background:rgba(184,134,11,.07);pointer-events:none;z-index:0;
}
.ajl-glow2{
  position:absolute;left:-80px;bottom:-80px;
  width:280px;height:280px;border-radius:50%;
  background:rgba(184,134,11,.05);pointer-events:none;z-index:0;
}
.ajl-logo-main{
  font-family:'Cormorant Garamond',serif;
  font-size:1.9rem;font-weight:600;color:#D4A843;
  letter-spacing:.22em;display:flex;align-items:center;gap:8px;line-height:1;
}
.ajl-dot{width:7px;height:7px;background:#D4A843;transform:rotate(45deg);flex-shrink:0;}
.ajl-rule{
  width:100%;height:.7px;
  background:linear-gradient(to right,transparent,#B8860B,transparent);margin:8px 0;
}
.ajl-sub{
  font-family:'DM Sans',sans-serif;
  font-size:.58rem;color:rgba(212,168,67,.45);letter-spacing:.3em;text-transform:uppercase;
}
.ajl-quote{
  font-family:'Cormorant Garamond',serif;
  font-size:3.2rem;font-weight:300;color:#FFFDF9;
  line-height:1.2;margin-bottom:24px;
}
.ajl-quote em{font-style:italic;color:#D4A843;font-weight:400;}
.ajl-desc{
  font-family:'DM Sans',sans-serif;
  font-size:1rem;color:rgba(255,253,249,.45);line-height:1.85;
}
.ajl-pill{
  display:inline-flex;align-items:center;gap:8px;
  background:rgba(184,134,11,.12);border:1px solid rgba(184,134,11,.28);
  padding:9px 18px;border-radius:20px;
}
.ajl-pill-dot{width:5px;height:5px;border-radius:50%;background:#4CAF50;flex-shrink:0;}
.ajl-pill-txt{
  font-family:'DM Sans',sans-serif;
  font-size:.65rem;color:#D4A843;letter-spacing:.1em;
}

/* ── Right panel elements ───────────────────────────────── */
.ajr-top{padding:52px 0 0;}
.ajr-tabs{
  display:flex;justify-content:center;
  border-bottom:1.5px solid #E8D5A3;margin-bottom:28px;gap:40px;
}
.ajr-tab{
  font-family:'DM Sans',sans-serif;
  font-size:.88rem;letter-spacing:.14em;text-transform:uppercase;
  color:#8B6914;padding:0 0 12px;
  border-bottom:2px solid transparent;margin-bottom:-1.5px;
  cursor:pointer;text-decoration:none!important;transition:color .2s;display:inline-block;
}
.ajr-tab-on{color:#B8860B!important;border-bottom-color:#B8860B;}
.ajr-title{
  font-family:'Cormorant Garamond',serif;
  font-size:1.65rem;font-weight:400;color:#1A1008;margin-bottom:4px;
}
.ajr-sub{
  font-family:'DM Sans',sans-serif;
  font-size:.74rem;color:#8B6914;margin-bottom:22px;
}
.ajr-gbtn{
  display:flex;align-items:center;justify-content:center;gap:10px;
  border:1.5px solid #E8D5A3;border-radius:3px;padding:11px 16px;
  font-family:'DM Sans',sans-serif;font-size:.72rem;letter-spacing:.08em;
  color:#4A3728!important;background:#FFFDF7;cursor:pointer;
  margin-bottom:18px;width:100%;transition:border-color .2s,background .2s;
  text-decoration:none!important;
}
.ajr-gbtn:hover{border-color:#B8860B;background:#FFF8EE;}
.ajr-div{display:flex;align-items:center;gap:10px;margin-bottom:20px;}
.ajr-div-line{flex:1;height:1px;background:#EDD9A3;}
.ajr-div-txt{
  font-family:'DM Sans',sans-serif;
  font-size:.62rem;color:#8B6914;letter-spacing:.1em;white-space:nowrap;
}
.ajr-forgot{
  font-family:'DM Sans',sans-serif;
  font-size:.62rem;color:#B8860B;text-align:right;
  display:block;margin-bottom:4px;cursor:pointer;
}
.ajr-btm{
  text-align:center;margin-top:16px;
  font-family:'DM Sans',sans-serif;font-size:.7rem;color:#8B6914;
}
.ajr-btm a{color:#B8860B!important;font-weight:600;}
.ajr-loyalty{
  margin-top:16px;background:#FFF8EE;border:1px solid #EDD9A3;
  border-radius:3px;padding:10px 13px;
  font-family:'DM Sans',sans-serif;font-size:.65rem;color:#8B6914;
  line-height:1.6;display:flex;align-items:flex-start;gap:8px;
}
.ajr-err{
  background:#FDF0F0;border:1px solid #F5C6C6;border-radius:3px;
  padding:9px 12px;font-family:'DM Sans',sans-serif;
  font-size:.72rem;color:#9B2335;margin-bottom:14px;
}
.ajr-ok{
  background:#F0FDF4;border:1px solid #BBF7D0;border-radius:3px;
  padding:9px 12px;font-family:'DM Sans',sans-serif;
  font-size:.72rem;color:#166534;margin-bottom:14px;
}

/* Tab buttons */
.stButton>button[kind="primary"]{
  background:#B8860B!important;color:#fff!important;
  border:none!important;border-radius:2px!important;
  font-family:'DM Sans',sans-serif!important;
  font-size:.8rem!important;letter-spacing:.14em!important;
  text-transform:uppercase!important;padding:10px!important;
}
.stButton>button[kind="secondary"]{
  background:transparent!important;color:#8B6914!important;
  border:1px solid #E8D5A3!important;border-radius:2px!important;
  font-family:'DM Sans',sans-serif!important;
  font-size:.8rem!important;letter-spacing:.14em!important;
  text-transform:uppercase!important;padding:10px!important;
}
.stButton>button[kind="secondary"]:hover{
  background:#FFF8EE!important;border-color:#B8860B!important;
  color:#B8860B!important;
}
/* Center submit and goto buttons */
.stButton>button{display:block!important;margin:0 auto!important;}

.stCheckbox{background:transparent!important;}
.stCheckbox>label{background:transparent!important;}
.stCheckbox [data-testid="stCheckbox"]{background:transparent!important;}
/* Fix goto buttons (Register here / Sign in here) */
button[data-testid="baseButton-secondary"]{
  background:transparent!important;
  color:#B8860B!important;
  border:none!important;
  padding:0!important;
  font-size:.72rem!important;
  letter-spacing:.08em!important;
  text-transform:none!important;
  width:auto!important;
  display:inline!important;
}
/* Top gap for right panel */
.ajr-top-gap{margin-top:40px;}
.stTextInput>div>div>input{
  border:1.5px solid #E8D5A3!important;border-radius:2px!important;
  background:#FFFDF9!important;color:#1A1008!important;
  padding:9px 12px!important;
  font-family:'DM Sans',sans-serif!important;font-size:.84rem!important;
}
.stTextInput>div>div>input:focus{
  border-color:#B8860B!important;box-shadow:none!important;
}
.stTextInput label{
  font-family:'DM Sans',sans-serif!important;font-size:.6rem!important;
  letter-spacing:.14em!important;text-transform:uppercase!important;
  color:#8B6914!important;font-weight:400!important;
}
.stCheckbox label{
  font-family:'DM Sans',sans-serif!important;
  font-size:.74rem!important;color:#4A3728!important;
}
.stButton>button{
  background:#1A1008!important;color:#FFFDF9!important;
  border:none!important;border-radius:2px!important;padding:12px!important;
  font-family:'DM Sans',sans-serif!important;font-size:.7rem!important;
  letter-spacing:.14em!important;text-transform:uppercase!important;
  width:100%!important;transition:background .2s!important;
}
.stButton>button:hover{background:#B8860B!important;}
[data-testid="stForm"]{
  border:none!important;padding:0!important;background:transparent!important;
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# COLUMNS
# ════════════════════════════════════════════════════════════
left_col, right_col = st.columns(2, gap="small")

# ── LEFT ─────────────────────────────────────────────────────
with left_col:
    st.markdown("""
    <div class="ajl">
      <div class="ajl-glow1"></div>
      <div class="ajl-glow2"></div>

      <div>
        <div class="ajl-logo-main">
          AURUS <span class="ajl-dot"></span> JEWELS
        </div>
        <div class="ajl-rule"></div>
        <div class="ajl-sub">Fine Gold &amp; Silver &middot; BIS Hallmarked</div>
      </div>

      <div>
        <div class="ajl-quote">
          Where Gold<br>Speaks In<br><em>Living Prices</em>
        </div>
        <div class="ajl-desc">
          Sign in to track your orders, manage your wishlist
          and unlock your loyalty rewards. Every rupee spent
          brings you closer to Platinum.
        </div>
      </div>

      <div>
        <div class="ajl-pill">
          <div class="ajl-pill-dot"></div>
          <span class="ajl-pill-txt">
            All products BIS Hallmarked &middot; GST Invoice on every order
          </span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── RIGHT ─────────────────────────────────────────────────────
with right_col:
    # Top gap
    st.markdown('<div style="height:40px;"></div>', unsafe_allow_html=True)
    # Tabs — use columns + buttons to avoid new tab
    t1, t2 = st.columns(2)
    with t1:
        if st.button("Sign In", key="tab_signin",
                     type="primary" if tab=="signin" else "secondary",
                     use_container_width=True):
            st.session_state["login_tab"] = "signin"
            st.rerun()
    with t2:
        if st.button("Register", key="tab_register",
                     type="primary" if tab=="register" else "secondary",
                     use_container_width=True):
            st.session_state["login_tab"] = "register"
            st.rerun()

    # ── SIGN IN ──────────────────────────────────────────────
    if tab == "signin":
        st.markdown("""
        <div style="text-align:center;margin-bottom:22px;">
          <div class="ajr-title">Welcome!</div>
          <div class="ajr-sub">Sign in to your Aurus Jewels account</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            f'<a href="{G_URL}" class="ajr-gbtn">{G_ICON} Continue with Google</a>'
            '<div class="ajr-div">'
            '<div class="ajr-div-line"></div>'
            '<div class="ajr-div-txt">or continue with email</div>'
            '<div class="ajr-div-line"></div>'
            '</div>',
            unsafe_allow_html=True
        )

        with st.form("signin_form"):
            email    = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            remember  = st.checkbox("Remember me")
            st.markdown(
                '<div style="text-align:right;margin-top:-32px;margin-bottom:8px;">'
                '<span class="ajr-forgot">Forgot password?</span></div>',
                unsafe_allow_html=True
            )
            sub = st.form_submit_button("Sign In to Aurus Jewels")
            if sub:
                if not email or not password:
                    st.markdown(
                        '<div class="ajr-err">Please enter your email and password.</div>',
                        unsafe_allow_html=True
                    )
                else:
                    with st.spinner("Signing in…"):
                        customer, err = login_customer(email.strip(), password)
                    if customer:
                        token = generate_token(customer)
                        login_session(customer, token)
                        st.switch_page("Home.py")
                    else:
                        st.markdown(
                            f'<div class="ajr-err">{err}</div>',
                            unsafe_allow_html=True
                        )

        st.markdown(
            '<div class="ajr-btm" style="text-align:center;margin-top:16px;">'
            'Don\'t have an account? </div>',
            unsafe_allow_html=True
        )
        if st.button("Register here →", key="goto_register", use_container_width=False):
            st.session_state["login_tab"] = "register"
            st.rerun()
        st.markdown("""
        <div class="ajr-loyalty">
          <span style="font-size:14px;flex-shrink:0;">&#128081;</span>
          <span>New to Aurus? Register today and start earning loyalty points.
          &#8377;50,000 in purchases unlocks Silver &mdash; 3% off everything.</span>
        </div>
        """, unsafe_allow_html=True)

    # ── REGISTER ─────────────────────────────────────────────
    else:
        st.markdown("""
        <div class="ajr-title">Create account</div>
        <div class="ajr-sub">Join Aurus Jewels and start earning rewards</div>
        """, unsafe_allow_html=True)

        st.markdown(
            f'<a href="{G_URL}" class="ajr-gbtn">{G_ICON} Register with Google</a>'
            '<div class="ajr-div">'
            '<div class="ajr-div-line"></div>'
            '<div class="ajr-div-txt">or register with email</div>'
            '<div class="ajr-div-line"></div>'
            '</div>',
            unsafe_allow_html=True
        )

        with st.form("register_form"):
            full_name   = st.text_input("Full name", placeholder="Hardik Malhotra")
            email       = st.text_input("Email address", placeholder="you@example.com")
            phone       = st.text_input("Phone number (optional)", placeholder="+91 98765 43210")
            password    = st.text_input("Password", type="password", placeholder="Min 8 characters")
            confirm_pwd = st.text_input("Confirm password", type="password", placeholder="Re-enter password")
            sub         = st.form_submit_button("Create My Account")
            if sub:
                err = None
                if not full_name or not email or not password:
                    err = "Please fill in all required fields."
                elif len(password) < 8:
                    err = "Password must be at least 8 characters."
                elif password != confirm_pwd:
                    err = "Passwords do not match."
                if err:
                    st.markdown(f'<div class="ajr-err">{err}</div>', unsafe_allow_html=True)
                else:
                    with st.spinner("Creating your account…"):
                        customer, err = register_customer(
                            full_name = full_name.strip(),
                            email     = email.strip(),
                            phone     = phone.strip() if phone else "",
                            password  = password,
                        )
                    if customer:
                        token = generate_token(customer)
                        login_session(customer, token)
                        st.switch_page("Home.py")
                    else:
                        st.markdown(f'<div class="ajr-err">{err}</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="ajr-btm" style="text-align:center;margin-top:16px;">'
            'Already have an account?</div>',
            unsafe_allow_html=True
        )
        if st.button("Sign in here →", key="goto_signin", use_container_width=False):
            st.session_state["login_tab"] = "signin"
            st.rerun()
        st.markdown("""
        <div class="ajr-loyalty">
          <span style="font-size:14px;flex-shrink:0;">&#128081;</span>
          <span>Every purchase earns loyalty points. Silver at &#8377;50K &rarr;
          Gold at &#8377;1.5L &rarr; Platinum at &#8377;5L with exclusive perks.</span>
        </div>
        """, unsafe_allow_html=True)