from typing import Optional
from .sec_edgar import get_recent_13f_filings, get_holdings_from_filing

def get_portfolio_changes(cik: str) -> dict:
    """
    Compare latest 13F vs previous 13F.
    Returns dict with: new, sold, increased, decreased positions.
    """
    filings = get_recent_13f_filings(cik, limit=2)
    if len(filings) < 2:
        return {"error": "רק דיווח אחד זמין — אין השוואה אפשרית"}

    latest = filings[0]
    previous = filings[1]

    h_new = get_holdings_from_filing(cik, latest["accession"])
    h_old = get_holdings_from_filing(cik, previous["accession"])

    if not h_new or not h_old:
        return {"error": "לא ניתן לשלוף נתוני אחזקות להשוואה"}

    new_dict = {h["cusip"]: h for h in h_new if h["cusip"]}
    old_dict = {h["cusip"]: h for h in h_old if h["cusip"]}

    new_positions = []
    sold_positions = []
    increased = []
    decreased = []

    for cusip, h in new_dict.items():
        if cusip not in old_dict:
            new_positions.append(h)
        else:
            old_val = old_dict[cusip]["value_thousands"]
            new_val = h["value_thousands"]
            if old_val > 0:
                pct_change = (new_val - old_val) / old_val * 100
                if pct_change > 5:
                    increased.append({**h, "pct_change": round(pct_change, 1), "old_value": old_val})
                elif pct_change < -5:
                    decreased.append({**h, "pct_change": round(pct_change, 1), "old_value": old_val})

    for cusip, h in old_dict.items():
        if cusip not in new_dict:
            sold_positions.append(h)

    increased.sort(key=lambda x: abs(x["pct_change"]), reverse=True)
    decreased.sort(key=lambda x: abs(x["pct_change"]), reverse=True)
    new_positions.sort(key=lambda x: x["value_thousands"], reverse=True)
    sold_positions.sort(key=lambda x: x["value_thousands"], reverse=True)

    return {
        "latest_date": latest["date"],
        "previous_date": previous["date"],
        "new": new_positions[:5],
        "sold": sold_positions[:5],
        "increased": increased[:5],
        "decreased": decreased[:5],
        "error": None,
    }
