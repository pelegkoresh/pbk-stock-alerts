"""
recurring_actions.py
====================
Detects recurring institutional patterns across multiple 13F filings.
Identifies: consistent buys, consistent sells, seasonal patterns.
"""
import time
from .sec_edgar import get_recent_13f_filings, get_holdings_from_filing, KNOWN_INSTITUTIONS, INSTITUTION_PROFILES

QUARTERS = ["Q1 (ינואר-מרץ)", "Q2 (אפריל-יוני)", "Q3 (יולי-ספטמבר)", "Q4 (אוקטובר-דצמבר)"]

def _date_to_quarter(date_str: str) -> str:
    try:
        month = int(date_str[5:7])
        if month <= 3:  return "Q1"
        if month <= 6:  return "Q2"
        if month <= 9:  return "Q3"
        return "Q4"
    except Exception:
        return "?"

def _date_to_year(date_str: str) -> str:
    try: return date_str[:4]
    except: return "?"

def analyze_institution_patterns(cik: str, num_filings: int = 6) -> dict:
    """
    Fetch last N filings for an institution.
    Compare each consecutive pair to find recurring buys/sells/increases.
    Returns patterns dict.
    """
    filings = get_recent_13f_filings(cik, limit=num_filings)
    if len(filings) < 2:
        return {"error": "פחות מ-2 דיווחים זמינים", "patterns": []}

    # Load all holdings per filing
    snapshots = []
    for f in filings:
        holdings = get_holdings_from_filing(cik, f["accession"])
        hdict = {h["cusip"] or h["name"]: h for h in holdings if h.get("cusip") or h.get("name")}
        snapshots.append({
            "date": f["date"],
            "quarter": _date_to_quarter(f["date"]),
            "year": _date_to_year(f["date"]),
            "holdings": hdict,
        })
        time.sleep(0.15)

    # Track per-asset action history across filings
    asset_history = {}  # cusip/name -> [{date, action, value, pct_change}]

    for i in range(len(snapshots) - 1):
        curr = snapshots[i]
        prev = snapshots[i + 1]

        all_keys = set(curr["holdings"]) | set(prev["holdings"])
        for key in all_keys:
            if key not in asset_history:
                asset_history[key] = {
                    "name": (curr["holdings"].get(key) or prev["holdings"].get(key, {})).get("name", key),
                    "cusip": key if len(key) == 9 else "",
                    "actions": [],
                }

            curr_h = curr["holdings"].get(key)
            prev_h = prev["holdings"].get(key)

            if curr_h and not prev_h:
                action = "קנייה חדשה"
                val = curr_h["value_thousands"] / 1000
                pct = 100
            elif not curr_h and prev_h:
                action = "מכירה מלאה"
                val = prev_h["value_thousands"] / 1000
                pct = -100
            elif curr_h and prev_h:
                old_v = prev_h["value_thousands"]
                new_v = curr_h["value_thousands"]
                pct = round((new_v - old_v) / old_v * 100, 1) if old_v else 0
                val = new_v / 1000
                if pct > 5:
                    action = f"הגדלה +{pct}%"
                elif pct < -5:
                    action = f"קיצוץ {pct}%"
                else:
                    action = "החזקה"
            else:
                continue

            asset_history[key]["actions"].append({
                "date": curr["date"],
                "quarter": curr["quarter"],
                "year": curr["year"],
                "action": action,
                "value_m": val,
                "pct_change": pct,
            })

    # Find recurring patterns (same direction ≥ 3 times)
    recurring = []
    for key, data in asset_history.items():
        actions = data["actions"]
        if len(actions) < 2:
            continue

        buys    = [a for a in actions if "קנייה" in a["action"] or "הגדלה" in a["action"]]
        sells   = [a for a in actions if "מכירה" in a["action"] or "קיצוץ" in a["action"]]
        holds   = [a for a in actions if a["action"] == "החזקה"]

        pattern_type = None
        pattern_actions = []
        consistency = 0

        if len(buys) >= 2:
            pattern_type = "קנייה חוזרת"
            pattern_actions = buys
            consistency = len(buys) / len(actions)
        elif len(sells) >= 2:
            pattern_type = "מכירה חוזרת"
            pattern_actions = sells
            consistency = len(sells) / len(actions)
        elif len(holds) >= 3:
            pattern_type = "החזקה יציבה"
            pattern_actions = holds
            consistency = len(holds) / len(actions)

        if not pattern_type:
            continue

        # Check if seasonal (same quarter repeats)
        quarters_in_pattern = [a["quarter"] for a in pattern_actions]
        quarter_counts = {q: quarters_in_pattern.count(q) for q in set(quarters_in_pattern)}
        dominant_quarter = max(quarter_counts, key=quarter_counts.get)
        is_seasonal = quarter_counts[dominant_quarter] >= 2

        avg_val = sum(a["value_m"] for a in pattern_actions) / len(pattern_actions)
        latest_date = pattern_actions[0]["date"] if pattern_actions else ""

        recurring.append({
            "name": data["name"],
            "cusip": data["cusip"],
            "pattern_type": pattern_type,
            "consistency_pct": round(consistency * 100),
            "occurrences": len(pattern_actions),
            "total_filings": len(actions),
            "avg_value_m": round(avg_val, 1),
            "latest_date": latest_date,
            "is_seasonal": is_seasonal,
            "dominant_quarter": dominant_quarter if is_seasonal else "",
            "all_actions": actions,
        })

    recurring.sort(key=lambda x: (x["consistency_pct"], x["avg_value_m"]), reverse=True)
    profile = INSTITUTION_PROFILES.get(cik, {})
    return {
        "institution": KNOWN_INSTITUTIONS.get(cik, cik),
        "institution_he": profile.get("name_he", ""),
        "manager": profile.get("manager", ""),
        "filings_analyzed": len(filings),
        "date_range": f"{filings[-1]['date']} — {filings[0]['date']}",
        "patterns": recurring[:30],
        "error": None,
    }

def get_all_recurring_by_commodity() -> list:
    """
    Cross all institutions: find assets that multiple institutions
    buy/sell in the same quarter every year.
    """
    all_patterns = {}  # asset_name -> {quarters: {Q: [institutions]}}

    for cik in list(KNOWN_INSTITUTIONS.keys())[:6]:
        result = analyze_institution_patterns(cik, num_filings=5)
        if result.get("error"):
            continue
        inst_name = result["institution_he"] or result["institution"]
        for p in result["patterns"]:
            if not p["is_seasonal"]:
                continue
            key = p["name"]
            if key not in all_patterns:
                all_patterns[key] = {
                    "name": key, "cusip": p["cusip"],
                    "quarters": {}, "institutions": [],
                }
            q = p["dominant_quarter"]
            if q not in all_patterns[key]["quarters"]:
                all_patterns[key]["quarters"][q] = []
            all_patterns[key]["quarters"][q].append({
                "institution": inst_name,
                "pattern": p["pattern_type"],
                "consistency": p["consistency_pct"],
                "avg_value_m": p["avg_value_m"],
            })
            if inst_name not in all_patterns[key]["institutions"]:
                all_patterns[key]["institutions"].append(inst_name)

    result_list = [v for v in all_patterns.values() if len(v["institutions"]) >= 1]
    result_list.sort(key=lambda x: len(x["institutions"]), reverse=True)
    return result_list
