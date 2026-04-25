"""
core/pricing_engine.py — Live price calculator for Aurus Jewels.

Formula:
  metal_value   = weight_g × rate_per_gram
  making_charge = metal_value × making_pct
  pre_gst       = metal_value + making_charge
  gst           = pre_gst × 0.05
  final_price   = pre_gst + gst

GST split on invoice: CGST 2.5% + SGST 2.5%
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.db import execute_query

# ── In-memory rate cache ─────────────────────────────────────
_rate_cache: dict = {}


def _load_rates(force: bool = False):
    global _rate_cache
    if not _rate_cache or force:
        rows = execute_query(
            "SELECT metal_type, karat, rate_per_gram FROM v_current_rates"
        )
        _rate_cache = {
            (r["metal_type"], r["karat"]): float(r["rate_per_gram"])
            for r in rows
        }


def get_rate(metal_type: str, karat: str) -> float:
    """Return current rate per gram."""
    _load_rates()
    return _rate_cache.get((metal_type, karat), 0.0)


def get_all_rates() -> dict:
    """Return all current rates as dict."""
    _load_rates()
    return dict(_rate_cache)


def calculate_price(
    weight_g: float,
    making_pct: float,
    metal_type: str,
    karat: str
) -> dict:
    """Return full pricing breakdown dict."""
    rate          = get_rate(metal_type, karat)
    metal_value   = weight_g * rate
    making_charge = metal_value * making_pct
    pre_gst       = metal_value + making_charge
    gst           = pre_gst * 0.05
    final_price   = pre_gst + gst

    return {
        "rate_per_gram":  round(rate,          2),
        "metal_value":    round(metal_value,    2),
        "making_charge":  round(making_charge,  2),
        "pre_gst":        round(pre_gst,        2),
        "gst":            round(gst,            2),
        "cgst":           round(pre_gst * 0.025, 2),
        "sgst":           round(pre_gst * 0.025, 2),
        "final_price":    round(final_price,    2),
    }


def price_product(product: dict) -> dict:
    """Shortcut — pass a product row dict, get pricing back."""
    return calculate_price(
        float(product["weight_g"]),
        float(product["making_pct"]),
        product["metal_type"],
        product["karat"],
    )


def format_inr(amount: float) -> str:
    """Format a number as Indian Rupees — ₹1,23,456.00"""
    try:
        amount  = float(amount)
        integer = str(int(amount))
        decimal = f"{amount:.2f}".split(".")[1]

        # Indian comma format
        if len(integer) > 3:
            last3 = integer[-3:]
            rest  = integer[:-3]
            groups = []
            while len(rest) > 2:
                groups.append(rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.append(rest)
            groups.reverse()
            integer = ",".join(groups) + "," + last3

        return f"₹{integer}.{decimal}"
    except Exception:
        return f"₹{amount}"


def invalidate_rate_cache():
    """Call this after admin updates gold rates."""
    global _rate_cache
    _rate_cache = {}