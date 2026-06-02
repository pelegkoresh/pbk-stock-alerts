import requests
import time

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
HEADERS = {"User-Agent": "MarketMonitor contact@marketmonitor.local", "Accept": "application/json"}

# Known institutional crypto holdings (from public filings + reports)
INSTITUTIONAL_CRYPTO = {
    "bitcoin":  {"holders": ["MicroStrategy ($15B)", "Tesla ($1B)", "BlackRock ETF ($25B)", "Fidelity ETF ($12B)", "ARK Invest"], "sec_filing": True},
    "ethereum": {"holders": ["Grayscale ($9B)", "BlackRock ETF", "Fidelity", "ConsenSys"], "sec_filing": True},
    "solana":   {"holders": ["Grayscale", "VanEck", "Alameda (bankrupt)"], "sec_filing": False},
    "xrp":      {"holders": ["Grayscale", "WisdomTree"], "sec_filing": False},
    "cardano":  {"holders": ["Grayscale"], "sec_filing": False},
    "avalanche":{"holders": ["Grayscale", "a16z Crypto"], "sec_filing": False},
    "chainlink":{"holders": ["Grayscale", "Jump Crypto"], "sec_filing": False},
    "polkadot": {"holders": ["Grayscale", "Polychain Capital"], "sec_filing": False},
}

def fetch_top_crypto(limit: int = 50) -> list:
    """Fetch top N cryptocurrencies by market cap from CoinGecko."""
    try:
        url = f"{COINGECKO_BASE}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h,7d",
        }
        r = requests.get(url, headers=HEADERS, params=params, timeout=12)
        r.raise_for_status()
        coins = r.json()

        results = []
        for c in coins:
            inst = INSTITUTIONAL_CRYPTO.get(c["id"], {})
            results.append({
                "id":           c["id"],
                "name":         c["name"],
                "symbol":       c["symbol"].upper(),
                "price":        c.get("current_price", 0),
                "change_24h":   round(c.get("price_change_percentage_24h") or 0, 2),
                "change_7d":    round(c.get("price_change_percentage_7d_in_currency") or 0, 2),
                "market_cap":   c.get("market_cap", 0),
                "volume_24h":   c.get("total_volume", 0),
                "rank":         c.get("market_cap_rank", 0),
                "high_24h":     c.get("high_24h", 0),
                "low_24h":      c.get("low_24h", 0),
                "image":        c.get("image", ""),
                "inst_holders": inst.get("holders", []),
                "has_etf":      inst.get("sec_filing", False),
            })
        return results
    except Exception as e:
        return []

def fetch_crypto_detail(coin_id: str) -> dict:
    """Fetch detailed data for a single coin."""
    try:
        url = f"{COINGECKO_BASE}/coins/{coin_id}"
        params = {"localization": False, "tickers": False, "community_data": True, "developer_data": False}
        r = requests.get(url, headers=HEADERS, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
        return {
            "description": data.get("description", {}).get("en", "")[:300],
            "homepage": data.get("links", {}).get("homepage", [""])[0],
            "reddit": data.get("links", {}).get("subreddit_url", ""),
            "twitter": data.get("links", {}).get("twitter_screen_name", ""),
            "reddit_subscribers": data.get("community_data", {}).get("reddit_subscribers", 0),
            "twitter_followers": data.get("community_data", {}).get("twitter_followers", 0),
            "sentiment_up_pct": data.get("sentiment_votes_up_percentage", 0),
        }
    except Exception:
        return {}

def fetch_crypto_global() -> dict:
    """Fetch global crypto market stats."""
    try:
        r = requests.get(f"{COINGECKO_BASE}/global", headers=HEADERS, timeout=10)
        data = r.json().get("data", {})
        return {
            "total_market_cap": data.get("total_market_cap", {}).get("usd", 0),
            "total_volume": data.get("total_volume", {}).get("usd", 0),
            "btc_dominance": round(data.get("market_cap_percentage", {}).get("btc", 0), 1),
            "eth_dominance": round(data.get("market_cap_percentage", {}).get("eth", 0), 1),
            "active_coins": data.get("active_cryptocurrencies", 0),
            "market_cap_change_24h": round(data.get("market_cap_change_percentage_24h_usd", 0), 2),
        }
    except Exception:
        return {}

def get_institutional_crypto_etfs() -> list:
    """Return known institutional crypto ETF holdings."""
    return [
        {"etf": "iShares Bitcoin Trust (IBIT)", "issuer": "BlackRock", "aum_b": 25.0,  "coin": "Bitcoin"},
        {"etf": "Fidelity Wise Origin Bitcoin", "issuer": "Fidelity",  "aum_b": 12.0,  "coin": "Bitcoin"},
        {"etf": "ARK 21Shares Bitcoin ETF",     "issuer": "ARK/21Shares","aum_b": 4.5, "coin": "Bitcoin"},
        {"etf": "Grayscale Bitcoin Trust (GBTC)","issuer": "Grayscale", "aum_b": 18.0, "coin": "Bitcoin"},
        {"etf": "iShares Ethereum Trust",        "issuer": "BlackRock", "aum_b": 9.0,   "coin": "Ethereum"},
        {"etf": "Grayscale Ethereum Trust",      "issuer": "Grayscale", "aum_b": 5.5,   "coin": "Ethereum"},
        {"etf": "VanEck Bitcoin Trust",          "issuer": "VanEck",    "aum_b": 0.8,   "coin": "Bitcoin"},
    ]
