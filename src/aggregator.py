import time
from .sec_edgar import get_recent_13f_filings, get_holdings_from_filing, KNOWN_INSTITUTIONS

def build_institutional_heatmap(max_institutions: int = 8) -> list:
    """
    Fetch latest 13F from all institutions, aggregate by ticker/cusip,
    rank by total institutional value. Returns top 20.
    """
    aggregated = {}  # cusip -> dict

    ciks = list(KNOWN_INSTITUTIONS.keys())[:max_institutions]

    for cik in ciks:
        inst_name = KNOWN_INSTITUTIONS[cik]
        filings = get_recent_13f_filings(cik, limit=1)
        if not filings:
            continue
        holdings = get_holdings_from_filing(cik, filings[0]["accession"])
        for h in holdings:
            key = h["cusip"] or h["name"]
            if not key:
                continue
            if key not in aggregated:
                aggregated[key] = {
                    "name": h["name"],
                    "cusip": h["cusip"],
                    "total_value_thousands": 0,
                    "total_shares": 0,
                    "institution_count": 0,
                    "institutions": [],
                }
            aggregated[key]["total_value_thousands"] += h["value_thousands"]
            aggregated[key]["total_shares"] += h["shares"]
            aggregated[key]["institution_count"] += 1
            aggregated[key]["institutions"].append({
                "name": inst_name,
                "value_thousands": h["value_thousands"],
            })
        time.sleep(0.2)

    ranked = sorted(aggregated.values(), key=lambda x: x["total_value_thousands"], reverse=True)

    result = []
    for i, item in enumerate(ranked[:20]):
        item["rank"] = i + 1
        item["total_value_m"] = round(item["total_value_thousands"] / 1000, 1)
        item["institutions"].sort(key=lambda x: x["value_thousands"], reverse=True)
        result.append(item)

    return result
