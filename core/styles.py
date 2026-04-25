"""
core/styles.py — Global CSS design system + shared UI
components for Aurus Jewels.
Call inject_global_css() at top of every page.
"""
import streamlit as st
import base64, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Page map for navigation ──────────────────────────────────
PAGE_MAP = {
    "Home":      "Home.py",
    "Catalogue": "pages/Catalogue.py",
    "Product":   "pages/Product.py",
    "Cart":      "pages/Cart.py",
    "Checkout":  "pages/Checkout.py",
    "Profile":   "pages/Profile.py",
    "Login":     "pages/Login.py",
    "Admin":     "pages/Admin.py",
}

# ── Global CSS ───────────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?
family=Cinzel:wght@400;500;600;700&
family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400&
family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&
family=Tenor+Sans&
family=Cormorant+Garamond:ital,wght@1,300;1,400;1,500&
display=swap');

/* ── CSS variables ─────────────────────────────────────── */
:root {
  --ivory:      #FFFDF9;
  --cream:      #FFF8EE;
  --antique:    #F5E6C8;
  --antique2:   #EDD9A3;
  --gold:       #B8860B;
  --gold-light: #D4A843;
  --gold-shine: #E8C547;
  --gold-pale:  #F7EBC5;
  --esp:        #1A1008;
  --wal:        #4A3728;
  --moc:        #8B6914;
  --nav-bg:     #FFFDF7;
  --ft-bg:      #F0DFB0;
  --ft-text:    #4A3728;
  --burg:       #9B2335;
  --crim:       #7B1728;
  --border:     #E8D5A3;
  --shadow:     rgba(184,134,11,0.13);
  --shadow-h:   rgba(184,134,11,0.28);
  --success:    #2E7D32;
  --warning:    #E65100;
}

/* ── Streamlit chrome reset ────────────────────────────── */
#MainMenu, footer, header       { display: none !important; }
.stApp                          { background: var(--ivory) !important; }
[data-testid="stAppViewContainer"] > .main { padding: 0 !important; }
[data-testid="stHeader"]        { display: none !important; }
section[data-testid="stSidebar"]{ display: none !important; }
.block-container                { padding: 0 !important; max-width: 100% !important; }
.element-container              { margin: 0 !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }

/* ── Base ──────────────────────────────────────────────── */
body, html {
  font-family: 'DM Sans', sans-serif;
  color: var(--esp);
  background: var(--ivory);
  margin: 0; padding: 0;
}

/* ── Navbar ────────────────────────────────────────────── */
.aj-nav {
  position: sticky; top: 0; z-index: 999;
  background: var(--nav-bg);
  border-bottom: 1.5px solid var(--border);
  box-shadow: 0 2px 16px var(--shadow);
  padding: 0 40px;
  display: flex; align-items: center;
  justify-content: space-between;
  height: 68px;
}
.aj-logo {
  font-family: 'Cinzel', serif;
  font-size: 1.4rem; font-weight: 700;
  color: var(--gold); letter-spacing: 0.12em;
  text-decoration: none;
  display: flex; align-items: center; gap: 8px;
}
.aj-logo span { color: var(--esp); font-weight: 400; }
.aj-nav-links {
  display: flex; gap: 28px; align-items: center;
  list-style: none; margin: 0; padding: 0;
}
.aj-nav-links a {
  font-family: 'Tenor Sans', sans-serif;
  font-size: 0.7rem; letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--wal); text-decoration: none;
  transition: color 0.2s;
}
.aj-nav-links a:hover { color: var(--gold); }
.aj-nav-right {
  display: flex; align-items: center; gap: 18px;
}
.aj-cart-btn {
  position: relative; cursor: pointer;
  font-size: 1.2rem; color: var(--wal);
  text-decoration: none;
}
.aj-cart-btn .badge {
  position: absolute; top: -8px; right: -10px;
  background: var(--burg); color: #fff;
  font-size: 0.6rem; font-weight: 700;
  border-radius: 50%; width: 17px; height: 17px;
  display: flex; align-items: center;
  justify-content: center;
  font-family: 'DM Sans', sans-serif;
}
.aj-btn-nav {
  font-family: 'Tenor Sans', sans-serif;
  font-size: 0.66rem; letter-spacing: 0.14em;
  text-transform: uppercase;
  padding: 7px 18px; border-radius: 2px;
  border: 1.5px solid var(--gold);
  color: var(--gold); background: transparent;
  cursor: pointer; text-decoration: none;
  transition: all 0.2s;
}
.aj-btn-nav:hover {
  background: var(--gold); color: #fff;
}

/* ── Buttons ───────────────────────────────────────────── */
.aj-btn-primary {
  font-family: 'Tenor Sans', sans-serif;
  font-size: 0.7rem; letter-spacing: 0.16em;
  text-transform: uppercase;
  background: var(--gold); color: #fff;
  border: 2px solid var(--gold);
  padding: 13px 34px; border-radius: 2px;
  cursor: pointer; text-decoration: none;
  display: inline-block; transition: all 0.25s;
}
.aj-btn-primary:hover {
  background: var(--moc); border-color: var(--moc);
}
.aj-btn-outline {
  font-family: 'Tenor Sans', sans-serif;
  font-size: 0.7rem; letter-spacing: 0.16em;
  text-transform: uppercase;
  background: transparent; color: var(--gold);
  border: 2px solid var(--gold);
  padding: 13px 34px; border-radius: 2px;
  cursor: pointer; text-decoration: none;
  display: inline-block; transition: all 0.25s;
}
.aj-btn-outline:hover {
  background: var(--gold); color: #fff;
}
.aj-btn-cta {
  font-family: 'Tenor Sans', sans-serif;
  font-size: 0.7rem; letter-spacing: 0.16em;
  text-transform: uppercase;
  background: var(--burg); color: #fff;
  border: 2px solid var(--burg);
  padding: 13px 34px; border-radius: 2px;
  cursor: pointer; text-decoration: none;
  display: inline-block; transition: all 0.25s;
}
.aj-btn-cta:hover {
  background: var(--crim); border-color: var(--crim);
}

/* ── Section chrome ────────────────────────────────────── */
.aj-section     { padding: 64px 40px; }
.aj-section-alt { padding: 64px 40px; background: var(--cream); }
.aj-section-title {
  font-family: 'Cinzel', serif;
  font-size: clamp(1.3rem, 2.5vw, 1.9rem);
  font-weight: 500; color: var(--esp);
  letter-spacing: 0.06em; text-align: center;
  margin-bottom: 8px;
}
.aj-section-rule {
  width: 56px; height: 2px;
  background: linear-gradient(
    to right, var(--gold), var(--gold-light)
  );
  margin: 0 auto 14px;
}
.aj-section-sub {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1rem; color: var(--moc);
  font-style: italic; text-align: center;
  margin-bottom: 44px;
}

/* ── Rate bar ──────────────────────────────────────────── */
.aj-rate-bar {
  background: var(--antique);
  border-bottom: 1px solid var(--border);
  padding: 10px 40px;
  display: flex; align-items: center;
  justify-content: space-between; flex-wrap: wrap; gap: 12px;
}
.aj-rate-item {
  display: flex; align-items: center; gap: 8px;
}
.aj-rate-label {
  font-family: 'Tenor Sans', sans-serif;
  font-size: 0.62rem; letter-spacing: 0.15em;
  text-transform: uppercase; color: var(--moc);
}
.aj-rate-val {
  font-family: 'Playfair Display', serif;
  font-size: 1rem; font-weight: 600; color: var(--gold);
}
.aj-rate-unit {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.68rem; color: var(--moc);
}
.aj-rate-divider { color: var(--border); font-size: 1rem; }
.aj-bis-badge {
  font-family: 'Tenor Sans', sans-serif;
  font-size: 0.62rem; letter-spacing: 0.12em;
  text-transform: uppercase;
  background: var(--gold); color: #fff;
  padding: 4px 12px; border-radius: 2px;
}

/* ── Category grid ─────────────────────────────────────── */
.aj-cat-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}
.aj-cat-card {
  position: relative; overflow: hidden;
  border-radius: 4px; cursor: pointer;
  aspect-ratio: 3/4;
  box-shadow: 0 4px 20px var(--shadow);
  transition: transform 0.3s, box-shadow 0.3s;
  text-decoration: none;
}
.aj-cat-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 36px var(--shadow-h);
}
.aj-cat-card img {
  width: 100%; height: 100%; object-fit: cover;
  transition: transform 0.5s;
}
.aj-cat-card:hover img { transform: scale(1.06); }
.aj-cat-label {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(
    transparent, rgba(26,16,8,0.78)
  );
  padding: 32px 14px 14px;
  font-family: 'Cinzel', serif;
  font-size: 0.82rem; font-weight: 500;
  letter-spacing: 0.1em;
  color: #FFFDF9; text-align: center;
}

/* ── Product grid ──────────────────────────────────────── */
.aj-product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 24px;
}
.aj-product-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 4px; overflow: hidden;
  box-shadow: 0 2px 12px var(--shadow);
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: pointer; text-decoration: none;
  color: inherit; display: block;
}
.aj-product-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 32px var(--shadow-h);
}
.aj-product-img {
  position: relative; aspect-ratio: 1;
  overflow: hidden; background: var(--antique);
}
.aj-product-img img {
  width: 100%; height: 100%; object-fit: cover;
  transition: transform 0.5s;
}
.aj-product-card:hover .aj-product-img img {
  transform: scale(1.08);
}
.aj-product-badge {
  position: absolute; top: 10px; left: 10px;
  font-family: 'Tenor Sans', sans-serif;
  font-size: 0.58rem; letter-spacing: 0.12em;
  text-transform: uppercase;
  background: var(--gold); color: #fff;
  padding: 3px 9px; border-radius: 2px;
}
.aj-product-info  { padding: 14px; }
.aj-product-cat {
  font-family: 'Tenor Sans', sans-serif;
  font-size: 0.58rem; letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--moc); margin-bottom: 4px;
}
.aj-product-name {
  font-family: 'Playfair Display', serif;
  font-size: 0.9rem; font-weight: 500;
  color: var(--esp); margin-bottom: 8px;
  line-height: 1.4;
}
.aj-product-meta {
  display: flex; gap: 8px;
  align-items: center; margin-bottom: 8px;
}
.aj-karat-tag {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.62rem; color: var(--moc);
  border: 1px solid var(--border);
  padding: 2px 7px; border-radius: 2px;
}
.aj-product-price {
  font-family: 'Cinzel', serif;
  font-size: 1rem; font-weight: 600;
  color: var(--gold);
}
.aj-product-weight {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.68rem; color: var(--moc);
}
.aj-wishlist-btn {
  position: absolute; top: 10px; right: 10px;
  background: rgba(255,253,249,0.92);
  border: 1px solid var(--border);
  border-radius: 50%;
  width: 30px; height: 30px;
  display: flex; align-items: center;
  justify-content: center;
  font-size: 0.9rem; cursor: pointer;
  transition: all 0.2s;
}
.aj-wishlist-btn:hover {
  background: var(--gold); color: #fff;
}

/* ── Price breakdown box ───────────────────────────────── */
.aj-price-box {
  background: var(--cream);
  border: 1px solid var(--border);
  border-radius: 4px; padding: 20px;
}
.aj-price-row {
  display: flex; justify-content: space-between;
  align-items: center; padding: 7px 0;
  font-family: 'DM Sans', sans-serif;
  font-size: 0.85rem; color: var(--wal);
  border-bottom: 1px dashed var(--border);
}
.aj-price-row:last-child { border-bottom: none; }
.aj-price-row.total {
  font-family: 'Cinzel', serif;
  font-size: 1.05rem; font-weight: 600;
  color: var(--gold); padding-top: 12px;
}
.aj-price-row .label { color: var(--moc); }

/* ── Status badges ─────────────────────────────────────── */
.status-pending    { background:#FFF3E0;color:#E65100;padding:3px 10px;border-radius:20px;font-size:.7rem; }
.status-confirmed  { background:#E3F2FD;color:#1565C0;padding:3px 10px;border-radius:20px;font-size:.7rem; }
.status-processing { background:#F3E5F5;color:#6A1B9A;padding:3px 10px;border-radius:20px;font-size:.7rem; }
.status-shipped    { background:#E8F5E9;color:#2E7D32;padding:3px 10px;border-radius:20px;font-size:.7rem; }
.status-delivered  { background:#E8F5E9;color:#1B5E20;padding:3px 10px;border-radius:20px;font-size:.7rem;font-weight:600; }
.status-cancelled  { background:#FFEBEE;color:#B71C1C;padding:3px 10px;border-radius:20px;font-size:.7rem; }

/* ── Loyalty tier badges ───────────────────────────────── */
.tier-member   { background:#F5F5F5;color:#616161;padding:3px 12px;border-radius:20px;font-size:.68rem;font-family:'Tenor Sans';letter-spacing:.1em; }
.tier-silver   { background:linear-gradient(135deg,#E0E0E0,#BDBDBD);color:#212121;padding:3px 12px;border-radius:20px;font-size:.68rem;font-family:'Tenor Sans';letter-spacing:.1em; }
.tier-gold     { background:linear-gradient(135deg,var(--gold-light),var(--gold));color:#fff;padding:3px 12px;border-radius:20px;font-size:.68rem;font-family:'Tenor Sans';letter-spacing:.1em; }
.tier-platinum { background:linear-gradient(135deg,#B0BEC5,#546E7A);color:#fff;padding:3px 12px;border-radius:20px;font-size:.68rem;font-family:'Tenor Sans';letter-spacing:.1em; }

/* ── Admin stat card ───────────────────────────────────── */
.aj-stat-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 6px; padding: 22px;
  box-shadow: 0 2px 12px var(--shadow);
}
.aj-stat-label {
  font-family: 'Tenor Sans', sans-serif;
  font-size: 0.62rem; letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--moc); margin-bottom: 8px;
}
.aj-stat-value {
  font-family: 'Cinzel', serif;
  font-size: 1.7rem; font-weight: 600;
  color: var(--gold);
}

/* ── Footer ────────────────────────────────────────────── */
.aj-footer {
  background: var(--ft-bg);
  border-top: 2px solid var(--antique2);
  padding: 52px 40px 24px;
}
.aj-footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 36px; margin-bottom: 36px;
}
.aj-footer-brand {
  font-family: 'Cinzel', serif;
  font-size: 1.2rem; font-weight: 700;
  color: var(--gold); letter-spacing: 0.12em;
  margin-bottom: 10px;
}
.aj-footer-tagline {
  font-family: 'Cormorant Garamond', serif;
  font-size: 0.92rem; color: var(--wal);
  font-style: italic;
  margin-bottom: 14px; line-height: 1.6;
}
.aj-footer-heading {
  font-family: 'Tenor Sans', sans-serif;
  font-size: 0.62rem; letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--moc); margin-bottom: 14px;
}
.aj-footer-links { list-style: none; padding: 0; margin: 0; }
.aj-footer-links li { margin-bottom: 9px; }
.aj-footer-links a {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.83rem; color: var(--wal);
  text-decoration: none; transition: color 0.2s;
}
.aj-footer-links a:hover { color: var(--gold); }
.aj-footer-bottom {
  border-top: 1px solid var(--antique2);
  padding-top: 18px;
  display: flex; justify-content: space-between;
  align-items: center; flex-wrap: wrap; gap: 8px;
}
.aj-footer-copy {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.75rem; color: var(--moc);
}
.aj-gstin-tag {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.7rem; color: var(--moc);
  background: var(--antique2);
  padding: 3px 10px; border-radius: 2px;
}

/* ── Responsive ────────────────────────────────────────── */
@media (max-width: 1024px) {
  .aj-cat-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .aj-footer-grid {
    grid-template-columns: 1fr 1fr;
  }
}
@media (max-width: 768px) {
  .aj-nav { padding: 0 16px; }
  .aj-nav-links { display: none; }
  .aj-section, .aj-section-alt { padding: 40px 16px; }
  .aj-rate-bar { padding: 8px 16px; }
  .aj-cat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .aj-product-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .aj-footer { padding: 36px 16px 20px; }
  .aj-footer-grid {
    grid-template-columns: 1fr;
  }
  .aj-hero { height: 56vh; }
}
@media (max-width: 480px) {
  .aj-cat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .aj-product-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .aj-hero-title { font-size: 1.4rem; }
}
</style>
"""


def inject_global_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def handle_navigation():
    """Read ?_nav= query param and switch page."""
    nav = st.query_params.get("_nav", "")
    if nav and nav in PAGE_MAP:
        st.query_params.clear()
        st.switch_page(PAGE_MAP[nav])


def img_b64(path: str) -> str:
    """Convert image file to base64 data URI."""
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext  = path.rsplit(".", 1)[-1].lower()
        mime = "image/png" if ext == "png" else "image/jpeg"
        return f"data:{mime};base64,{data}"
    except Exception:
        return ""


def img_tag(path: str, alt: str = "", style: str = "") -> str:
    """Return <img> tag with base64 src, or placeholder div."""
    src = img_b64(path)
    if src:
        return (
            f'<img src="{src}" alt="{alt}" '
            f'style="object-fit:cover;{style}">'
        )
    return (
        f'<div style="background:var(--antique);width:100%;'
        f'height:100%;display:flex;align-items:center;'
        f'justify-content:center;color:var(--moc);'
        f'font-size:0.7rem;{style}">No Image</div>'
    )


def render_navbar(
    cart_count:  int  = 0,
    is_logged_in: bool = False,
    role:        str  = "customer"
):
    badge = (
        f'<span class="badge">{cart_count}</span>'
        if cart_count > 0 else ""
    )
    if is_logged_in:
        auth_html = f"""
        <a href="?_nav=Profile" class="aj-btn-nav">
          My Account
        </a>
        {"<a href='?_nav=Admin' class='aj-btn-nav' style='margin-left:6px;'>Admin</a>"
          if role == "admin" else ""}
        """
    else:
        auth_html = (
            '<a href="?_nav=Login" class="aj-btn-nav">'
            'Sign In</a>'
        )

    st.markdown(f"""
    <nav class="aj-nav">
      <a href="?_nav=Home" class="aj-logo">
        ⬡ AURUS<span>&nbsp;JEWELS</span>
      </a>
      <ul class="aj-nav-links">
        <li><a href="?_nav=Home">Home</a></li>
        <li><a href="?_nav=Catalogue">Catalogue</a></li>
        <li><a href="?_nav=Catalogue&cat=pendants">Pendants</a></li>
        <li><a href="?_nav=Catalogue&cat=rings">Rings</a></li>
        <li><a href="?_nav=Catalogue&cat=earrings">Earrings</a></li>
        <li><a href="?_nav=Catalogue&cat=bracelets">Bracelets</a></li>
        <li><a href="?_nav=Catalogue&cat=chains">Chains</a></li>
      </ul>
      <div class="aj-nav-right">
        <a href="?_nav=Cart" class="aj-cart-btn">
          🛒{badge}
        </a>
        {auth_html}
      </div>
    </nav>
    """, unsafe_allow_html=True)


def render_footer():
    st.markdown("""
    <footer class="aj-footer">
      <div class="aj-footer-grid">
        <div>
          <div class="aj-footer-brand">⬡ AURUS JEWELS</div>
          <p class="aj-footer-tagline">
            Fine hallmarked jewellery priced live from the
            official IBJA gold rate. Transparency is our craft.
          </p>
          <span class="aj-gstin-tag">
            GSTIN: 07AABCS1429B1Z6
          </span>
        </div>
        <div>
          <div class="aj-footer-heading">Shop</div>
          <ul class="aj-footer-links">
            <li><a href="?_nav=Catalogue&cat=pendants">Pendants</a></li>
            <li><a href="?_nav=Catalogue&cat=rings">Rings</a></li>
            <li><a href="?_nav=Catalogue&cat=earrings">Earrings</a></li>
            <li><a href="?_nav=Catalogue&cat=bracelets">Bracelets</a></li>
            <li><a href="?_nav=Catalogue&cat=chains">Chains</a></li>
          </ul>
        </div>
        <div>
          <div class="aj-footer-heading">Account</div>
          <ul class="aj-footer-links">
            <li><a href="?_nav=Login">Sign In</a></li>
            <li><a href="?_nav=Login">Register</a></li>
            <li><a href="?_nav=Profile">My Orders</a></li>
            <li><a href="?_nav=Profile">Wishlist</a></li>
          </ul>
        </div>
        <div>
          <div class="aj-footer-heading">Support</div>
          <ul class="aj-footer-links">
            <li><a href="#">About Us</a></li>
            <li><a href="#">BIS Hallmarking</a></li>
            <li><a href="#">Pricing Policy</a></li>
            <li><a href="#">Contact</a></li>
          </ul>
        </div>
      </div>
      <div class="aj-footer-bottom">
        <span class="aj-footer-copy">
          © 2026 Aurus Jewels. All rights reserved.
          All products BIS hallmarked.
        </span>
        <span class="aj-footer-copy">
          Prices update daily from IBJA official gold rates.
        </span>
      </div>
    </footer>
    """, unsafe_allow_html=True)