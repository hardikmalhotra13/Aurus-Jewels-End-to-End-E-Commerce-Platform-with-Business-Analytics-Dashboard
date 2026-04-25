"""
core/session.py — Session management for Aurus Jewels.
Uses browser cookies via extra-streamlit-components to
persist login across page navigations and new tabs.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config


# ── Cookie manager ────────────────────────────────────────────
# Module-level singleton — avoids CachedWidgetWarning.
# @st.cache_resource cannot hold Streamlit widgets (CookieManager
# internally calls st.components, which counts as a widget).
# A plain global is safe: the module is imported once per process.
_cookie_mgr_instance = None

def get_cookie_manager():
    global _cookie_mgr_instance
    if _cookie_mgr_instance is None:
        try:
            import extra_streamlit_components as stx
            _cookie_mgr_instance = stx.CookieManager(key="aurus_cookie_mgr")
        except ImportError:
            pass
    return _cookie_mgr_instance


# ── Defaults ──────────────────────────────────────────────────
_DEFAULTS = {
    "logged_in":    False,
    "customer_id":  None,
    "full_name":    "",
    "email":        "",
    "role":         "customer",
    "jwt_token":    "",
    "loyalty_tier": "member",
}

COOKIE_NAME = "aurus_jwt"
COOKIE_DAYS = config.JWT_EXPIRY_DAYS   # e.g. 7


def init_session():
    """
    Call at the very top of every page (before any other st.* call).

    What it does, in order:
      1. Sets session_state defaults — guarded with 'if key not in',
         so existing values are NEVER overwritten on re-runs.
      2. Returns immediately if already logged in (fast path).
      3. Gets the shared CookieManager.
      4. On the very first render of a new session the CookieManager's
         JS hasn't executed yet, so mgr.get() would return None even
         though a valid cookie exists in the browser.  We handle this
         with a single controlled st.rerun() guarded by _cookie_ready,
         which gives the JS one cycle to load.
      5. Reads the JWT cookie, verifies it, and restores the full
         session from the database.
    """

    # ── Step 1: safe defaults (never overwrites existing state) ──
    for k, v in _DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Step 2: already authenticated — nothing to do ────────────
    if st.session_state.get("logged_in"):
        return

    # ── Step 3: get the cookie manager ───────────────────────────
    mgr = get_cookie_manager()
    if mgr is None:
        return

    # ── Step 4: first-render guard ───────────────────────────────
    # On a fresh session (new tab / first load after navigation)
    # session_state is empty and the CookieManager JS hasn't fired.
    # We set the flag and do ONE rerun so the JS can execute.
    # On the second pass _cookie_ready already exists, so we skip
    # straight to the cookie read.
    if "_cookie_ready" not in st.session_state:
        st.session_state["_cookie_ready"] = True
        st.rerun()
        return

    # ── Step 5: read cookie ───────────────────────────────────────
    try:
        token = mgr.get(COOKIE_NAME)
    except Exception:
        token = None

    if not token:
        return

    # ── Step 6: verify JWT ────────────────────────────────────────
    from core.auth import verify_token
    payload = verify_token(token)
    if not payload:
        # Token is expired or tampered — wipe it
        _clear_cookie()
        return

    # ── Step 7: restore session from payload + DB ─────────────────
    st.session_state["logged_in"]   = True
    st.session_state["customer_id"] = payload.get("customer_id")
    st.session_state["email"]       = payload.get("email", "")
    st.session_state["role"]        = payload.get("role", "customer")
    st.session_state["jwt_token"]   = token

    # JWT only carries id/email/role.
    # full_name and loyalty_tier can change so we fetch them live.
    try:
        from database.db import execute_one
        row = execute_one(
            "SELECT full_name, loyalty_tier "
            "FROM dim_customers WHERE customer_id=%s",
            (payload["customer_id"],)
        )
        if row:
            st.session_state["full_name"]    = row["full_name"]
            st.session_state["loyalty_tier"] = row.get("loyalty_tier", "member")
        else:
            st.session_state["full_name"]    = payload.get("email", "")
            st.session_state["loyalty_tier"] = "member"
    except Exception:
        st.session_state["full_name"]    = payload.get("email", "")
        st.session_state["loyalty_tier"] = "member"


def login_session(customer: dict, token: str):
    """
    Call immediately after a successful login or registration.
    Writes session state AND the JWT cookie.
    """
    st.session_state["logged_in"]    = True
    st.session_state["customer_id"]  = customer["customer_id"]
    st.session_state["full_name"]    = customer.get("full_name", "")
    st.session_state["email"]        = customer.get("email", "")
    st.session_state["role"]         = customer.get("role", "customer")
    st.session_state["jwt_token"]    = token
    st.session_state["loyalty_tier"] = customer.get("loyalty_tier", "member")

    # Mark cookie manager as ready so init_session() won't
    # trigger the first-render rerun on the very next page.
    st.session_state["_cookie_ready"] = True

    mgr = get_cookie_manager()
    if mgr:
        try:
            import datetime
            mgr.set(
                COOKIE_NAME,
                token,
                expires_at=datetime.datetime.now()
                + datetime.timedelta(days=COOKIE_DAYS),
            )
        except Exception:
            pass  # Cookie write failed — session still works for this tab


def logout_session():
    """
    Clear session state and delete the JWT cookie.
    Keeps _cookie_ready so the next page doesn't do an extra rerun.
    """
    for k, v in _DEFAULTS.items():
        st.session_state[k] = v
    # Preserve the ready flag — cookie JS is still loaded
    st.session_state["_cookie_ready"] = True
    _clear_cookie()


def _clear_cookie():
    mgr = get_cookie_manager()
    if mgr:
        try:
            mgr.delete(COOKIE_NAME)
        except Exception:
            pass


# ── Public helpers (unchanged API — all existing pages work) ──

def is_logged_in() -> bool:
    """Returns True if the user is authenticated."""
    init_session()
    return bool(st.session_state.get("logged_in", False))


def get_customer_id():
    """Returns the logged-in customer's ID, or None."""
    return st.session_state.get("customer_id")


def get_role() -> str:
    """Returns the user's role string (default: 'customer')."""
    return st.session_state.get("role", "customer")


def get_loyalty_tier() -> str:
    """Returns the user's loyalty tier (default: 'member')."""
    return st.session_state.get("loyalty_tier", "member")


def require_login():
    """Redirect to Login page if not authenticated."""
    init_session()
    if not is_logged_in():
        st.switch_page("pages/Login.py")


def require_admin():
    """Redirect or stop if the user is not an admin."""
    require_login()
    if get_role() != "admin":
        st.error("⚠️ Admin access required.")
        st.stop()