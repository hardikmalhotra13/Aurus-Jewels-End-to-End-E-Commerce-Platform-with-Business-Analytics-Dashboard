"""
core/rate_fetcher.py — Fetches daily gold/silver rates.
Tries multiple sources. Falls back to last known DB rate if all scrapers fail.
"""
import requests
from bs4 import BeautifulSoup
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.db import execute_one, execute_write, execute_query
from core.pricing_engine import invalidate_rate_cache

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}


def _rate_exists_today(metal_type: str, karat: str) -> bool:
    row = execute_one(
        "SELECT rate_id FROM dim_gold_rates "
        "WHERE metal_type=%s AND karat=%s AND effective_date=CURDATE()",
        (metal_type, karat)
    )
    return row is not None


def _save_rate(metal_type: str, karat: str, rate: float, source: str = "IBJA"):
    execute_write(
        """INSERT INTO dim_gold_rates
             (metal_type, karat, rate_per_gram, effective_date, source)
           VALUES (%s, %s, %s, CURDATE(), %s)
           ON DUPLICATE KEY UPDATE rate_per_gram=%s, source=%s""",
        (metal_type, karat, rate, source, rate, source)
    )
    invalidate_rate_cache()


# ── Source 1: IBJA primary ────────────────────────────────────
def _fetch_from_ibja() -> dict | None:
    """Try IBJA website with multiple parsing strategies."""
    try:
        resp = requests.get("https://ibja.co/", headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        rates = {}

        # Strategy A: table rows
        for row in soup.select("table tr"):
            cells = [c.get_text(strip=True) for c in row.select("td")]
            if len(cells) >= 2:
                label = cells[0].upper().replace(" ", "")
                raw = re.sub(r"[^\d.]", "", cells[1].replace(",", ""))
                try:
                    val = float(raw)
                except (ValueError, TypeError):
                    continue
                if ("999" in label or "24KT" in label or "24K" in label) and 50000 < val < 150000:
                    rates["22K"] = round(val / 10 * (22/24), 2)
                    rates["18K"] = round(val / 10 * (18/24), 2)
                elif ("SILVER" in label or "925" in label) and val > 500:
                    rates["925"] = round(val / 1000 * 0.925, 2)

        # Strategy B: scan all text for numeric patterns near gold keywords
        if "22K" not in rates:
            text_lines = [l.strip() for l in soup.get_text().split('\n') if l.strip()]
            for i, line in enumerate(text_lines):
                upper = line.upper()
                if "999" in upper or "24 KT" in upper:
                    for j in range(i, min(i + 5, len(text_lines))):
                        raw = re.sub(r"[^\d.]", "", text_lines[j])
                        try:
                            val = float(raw)
                            if 50000 < val < 150000:
                                rates["22K"] = round(val / 10 * (22/24), 2)
                                rates["18K"] = round(val / 10 * (18/24), 2)
                                break
                        except (ValueError, TypeError):
                            pass
                if "SILVER" in upper and "925" not in rates:
                    for j in range(i, min(i + 5, len(text_lines))):
                        raw = re.sub(r"[^\d.]", "", text_lines[j])
                        try:
                            val = float(raw)
                            if 50000 < val < 200000:
                                rates["925"] = round(val / 1000 * 0.925, 2)
                                break
                        except (ValueError, TypeError):
                            pass

        return rates if len(rates) >= 2 else None
    except Exception:
        return None


# ── Source 2: goldpriceindia.com (fallback) ───────────────────
def _fetch_from_goldpriceindia() -> dict | None:
    """Fallback scraper."""
    try:
        resp = requests.get(
            "https://www.goldpriceindia.com/",
            headers=HEADERS, timeout=12
        )
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        rates = {}
        text_lines = [l.strip() for l in soup.get_text().split('\n') if l.strip()]

        for i, line in enumerate(text_lines):
            upper = line.upper()
            if ("22K" in upper or "22 KT" in upper or "22KT" in upper) and "22K" not in rates:
                for j in range(i, min(i + 5, len(text_lines))):
                    raw = re.sub(r"[^\d.]", "", text_lines[j])
                    try:
                        val = float(raw)
                        if 4000 < val < 15000:  # per gram
                            rates["22K"] = round(val, 2)
                            rates["18K"] = round(val * (18/22), 2)
                            break
                    except (ValueError, TypeError):
                        pass
            if "SILVER" in upper and "925" not in rates:
                for j in range(i, min(i + 5, len(text_lines))):
                    raw = re.sub(r"[^\d.]", "", text_lines[j])
                    try:
                        val = float(raw)
                        if 60 < val < 500:  # per gram
                            rates["925"] = round(val * 0.925, 2)
                            break
                    except (ValueError, TypeError):
                        pass

        return rates if len(rates) >= 2 else None
    except Exception:
        return None


# ── Source 3: last DB rate (safe fallback) ────────────────────
def _get_last_known_rates() -> dict:
    """Get most recent rates from DB for any date before today."""
    result = {}
    try:
        for metal, karat in [("gold","22K"), ("gold","18K"), ("silver","925")]:
            row = execute_one(
                "SELECT rate_per_gram FROM dim_gold_rates "
                "WHERE metal_type=%s AND karat=%s AND effective_date < CURDATE() "
                "ORDER BY effective_date DESC LIMIT 1",
                (metal, karat)
            )
            if row:
                result[(metal, karat)] = float(row["rate_per_gram"])
    except Exception:
        pass
    return result


# ── Main public functions ─────────────────────────────────────
def fetch_ibja_rates() -> dict | None:
    """Public: try all live sources, return rates dict or None."""
    rates = _fetch_from_ibja()
    if rates and "22K" in rates:
        return rates
    rates = _fetch_from_goldpriceindia()
    if rates and "22K" in rates:
        return rates
    return None


def fetch_if_missing():
    """
    Fetch today's rates only if not already in DB.
    Falls back to yesterday's rate if all scrapers fail.
    Safe to call on every app startup.
    """
    today_22k = _rate_exists_today("gold",   "22K")
    today_18k = _rate_exists_today("gold",   "18K")
    today_925 = _rate_exists_today("silver", "925")

    if today_22k and today_18k and today_925:
        return

    rates = fetch_ibja_rates()

    if rates:
        if not today_22k and "22K" in rates:
            _save_rate("gold",   "22K", rates["22K"], "IBJA")
        if not today_18k and "18K" in rates:
            _save_rate("gold",   "18K", rates["18K"], "IBJA")
        if not today_925 and "925" in rates:
            _save_rate("silver", "925", rates["925"], "IBJA")
    else:
        # All scrapers failed — carry forward yesterday's rate
        last = _get_last_known_rates()
        for (metal, karat), rate in last.items():
            if metal == "gold" and karat == "22K" and not today_22k:
                _save_rate("gold",   "22K", rate, "Carried")
            elif metal == "gold" and karat == "18K" and not today_18k:
                _save_rate("gold",   "18K", rate, "Carried")
            elif metal == "silver" and karat == "925" and not today_925:
                _save_rate("silver", "925", rate, "Carried")


def manual_update_rates(rate_22k: float, rate_18k: float, rate_925: float, admin_id: int = 0):
    """Admin manual override — always replaces today's rate."""
    for metal, karat, rate in [
        ("gold",   "22K", rate_22k),
        ("gold",   "18K", rate_18k),
        ("silver", "925", rate_925),
    ]:
        execute_write(
            """INSERT INTO dim_gold_rates
                 (metal_type, karat, rate_per_gram, effective_date, source)
               VALUES (%s, %s, %s, CURDATE(), 'Manual')
               ON DUPLICATE KEY UPDATE rate_per_gram=%s, source='Manual'""",
            (metal, karat, rate, rate)
        )
    invalidate_rate_cache()


def debug_fetch():
    """
    Diagnose rate fetching. Run from terminal:
    python -c "from core.rate_fetcher import debug_fetch; debug_fetch()"
    """
    print("=" * 55)
    print("AURUS JEWELS — Rate Fetcher Diagnostics")
    print("=" * 55)

    print("\n[1] Today's rates in DB:")
    for metal, karat in [("gold","22K"), ("gold","18K"), ("silver","925")]:
        if _rate_exists_today(metal, karat):
            row = execute_one(
                "SELECT rate_per_gram, source FROM dim_gold_rates "
                "WHERE metal_type=%s AND karat=%s AND effective_date=CURDATE()",
                (metal, karat)
            )
            print(f"   {karat}: Rs.{row['rate_per_gram']}/g  [{row['source']}]  OK")
        else:
            print(f"   {karat}: MISSING")

    print("\n[2] Testing IBJA scraper...")
    rates = _fetch_from_ibja()
    if rates:
        print(f"   22K = Rs.{rates.get('22K')}/g")
        print(f"   18K = Rs.{rates.get('18K')}/g")
        print(f"   925 = Rs.{rates.get('925')}/g")
        print("   Result: SUCCESS")
    else:
        print("   Result: FAILED (site may have changed structure)")

    print("\n[3] Testing fallback scraper (goldpriceindia.com)...")
    rates2 = _fetch_from_goldpriceindia()
    if rates2:
        print(f"   22K = Rs.{rates2.get('22K')}/g")
        print(f"   18K = Rs.{rates2.get('18K')}/g")
        print("   Result: SUCCESS")
    else:
        print("   Result: FAILED")

    print("\n[4] Last known DB rates:")
    last = _get_last_known_rates()
    if last:
        for (m, k), v in last.items():
            print(f"   {k}: Rs.{v}/g")
    else:
        print("   No historical rates in DB")

    print("\n[5] Running fetch_if_missing()...")
    fetch_if_missing()
    print("   Done.")
    print("=" * 55)