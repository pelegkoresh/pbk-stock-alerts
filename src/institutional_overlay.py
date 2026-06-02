"""
institutional_overlay.py
========================
Central module: for ANY asset (stock by name/cusip, commodity by keyword),
returns which institutions hold it and how much.
Used by every page in the dashboard.
"""

import streamlit as st
from .sec_edgar import KNOWN_INSTITUTIONS, INSTITUTION_PROFILES

# ── Commodity → institution keyword mapping ──────────────
# Maps commodity keys to search terms found in 13F holdings
COMMODITY_INSTITUTION_MAP = {
    "crude_oil": {
        "keywords": ["CHEVRON", "EXXON", "CONOCOPHILLIPS", "OCCIDENTAL", "PIONEER", "SUNCOR", "EOG", "DEVON"],
        "etfs": ["XLE", "VDE", "OIH"],
        "note": "חברות נפט גז ואנרגיה",
    },
    "natural_gas": {
        "keywords": ["CONOCOPHILLIPS", "EOG", "DEVON", "PIONEER", "EQT", "RANGE RESOURCES", "COTERRA"],
        "etfs": ["UNG", "XLE"],
        "note": "חברות גז טבעי",
    },
    "coffee": {
        "keywords": ["STARBUCKS", "JAB", "NESTLE", "MONDELEZ", "JM SMUCKER"],
        "etfs": ["JO", "CAFE"],
        "note": "חברות קפה ומשקאות",
    },
    "corn": {
        "keywords": ["ARCHER DANIELS", "ADM", "BUNGE", "CORTEVA", "DEERE", "MOSAIC", "NUTRIEN"],
        "etfs": ["CORN", "WEAT", "DBA"],
        "note": "חברות חקלאות ודשנים",
    },
    "soybeans": {
        "keywords": ["ARCHER DANIELS", "ADM", "BUNGE", "CORTEVA", "CF INDUSTRIES"],
        "etfs": ["SOYB", "DBA"],
        "note": "חברות סויה וחקלאות",
    },
    "gold": {
        "keywords": ["BARRICK", "NEWMONT", "AGNICO", "GOLD FIELDS", "KINROSS"],
        "etfs": ["GLD", "IAU", "GDX"],
        "note": "חברות כרייה + ETF זהב",
    },
    "silver": {
        "keywords": ["WHEATON", "PAN AMERICAN", "FIRST MAJESTIC", "HECLA"],
        "etfs": ["SLV", "SIVR"],
        "note": "חברות כרייה כסף",
    },
    "wheat": {
        "keywords": ["ARCHER DANIELS", "ADM", "BUNGE", "GENERAL MILLS", "MONDELEZ"],
        "etfs": ["WEAT", "DBA"],
        "note": "חברות חיטה ומזון",
    },
}

def find_institutional_holders(
    holdings_cache: dict,    # {cik: [holdings list]} — pre-loaded
    asset_name: str = "",    # stock name to search
    cusip: str = "",         # exact cusip match
    commodity_key: str = "", # commodity key from COMMODITY_INSTITUTION_MAP
) -> list:
    """
    Search all institution holdings for a given asset.
    Returns list of {institution, cik, value_m, pct_of_portfolio, filing_date}
    sorted by value descending.
    """
    results = []

    # Build search terms
    search_terms = []
    if asset_name:
        parts = asset_name.upper().split()
        search_terms += [parts[0]] if parts else []
        if len(parts) > 1:
            search_terms.append(" ".join(parts[:2]))
    if commodity_key and commodity_key in COMMODITY_INSTITUTION_MAP:
        search_terms += COMMODITY_INSTITUTION_MAP[commodity_key]["keywords"]

    for cik, holdings_info in holdings_cache.items():
        holdings = holdings_info.get("holdings", [])
        filing_date = holdings_info.get("filing_date", "")
        total_val = sum(h["value_thousands"] for h in holdings) if holdings else 1

        for h in holdings:
            h_name = h.get("name", "").upper()
            h_cusip = h.get("cusip", "")
            matched = False

            if cusip and h_cusip == cusip:
                matched = True
            elif search_terms:
                for term in search_terms:
                    if term and term in h_name:
                        matched = True
                        break

            if matched:
                val_m = round(h["value_thousands"] / 1000, 1)
                pct = round(h["value_thousands"] / total_val * 100, 2) if total_val else 0
                profile = INSTITUTION_PROFILES.get(cik, {})
                results.append({
                    "cik": cik,
                    "institution": KNOWN_INSTITUTIONS.get(cik, cik),
                    "institution_he": profile.get("name_he", ""),
                    "manager": profile.get("manager", ""),
                    "holding_name": h["name"],
                    "value_m": val_m,
                    "pct_of_portfolio": pct,
                    "filing_date": filing_date,
                    "cusip": h_cusip,
                })

    results.sort(key=lambda x: x["value_m"], reverse=True)
    return results


def render_institutional_holders(holders: list, asset_label: str = ""):
    """
    Render a compact institutional holders widget.
    Call this from any page after finding holders.
    """
    if not holders:
        st.markdown(f"""
<div style="border:0.5px solid #e0e0e0;border-radius:8px;padding:12px 16px;background:#fafafa;margin-top:12px">
  <div style="font-size:13px;color:#888">🏛️ אף מוסד מה-8 הגדולים לא מחזיק ב{asset_label} לפי הדיווח האחרון</div>
</div>
""", unsafe_allow_html=True)
        return

    total_inst_val = sum(h["value_m"] for h in holders)
    count = len(holders)

    st.markdown(f"""
<div style="border:1px solid #1565c033;border-radius:10px;padding:14px 18px;background:#e8f4fd22;margin-top:12px">
  <div style="font-size:13px;font-weight:600;color:#1565c0;margin-bottom:10px">
    🏛️ {count} מוסד{'ות' if count>1 else ''} מחזיק{'ים' if count>1 else ''} ב{asset_label} | ווליום מוסדי: ${total_inst_val:,.0f}M
  </div>
""", unsafe_allow_html=True)

    for h in holders:
        bar_pct = min(h["value_m"] / max(holders[0]["value_m"], 1) * 100, 100)
        st.markdown(f"""
  <div style="display:flex;align-items:center;gap:10px;margin:7px 0;flex-wrap:wrap">
    <div style="min-width:180px;font-size:13px">
      <strong>{h['institution_he'] or h['institution']}</strong>
      <span style="color:#888;font-size:11px"> — {h['manager']}</span>
    </div>
    <div style="flex:1;background:#e0e0e0;border-radius:4px;height:16px;min-width:80px">
      <div style="width:{bar_pct:.0f}%;height:100%;background:#1565c0;border-radius:4px"></div>
    </div>
    <div style="min-width:80px;text-align:right;font-size:13px;font-weight:600;color:#1565c0">${h['value_m']:,.0f}M</div>
    <div style="font-size:11px;color:#888">{h['pct_of_portfolio']}% מהתיק</div>
    <div style="font-size:10px;color:#bbb">{h['filing_date']}</div>
  </div>
""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
