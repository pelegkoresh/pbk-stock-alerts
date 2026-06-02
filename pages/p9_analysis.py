import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl
from src.investment_analyzer import analyze_asset, analyze_with_insider, analyze_with_insider

try:
    from src.aggregator import build_institutional_heatmap
    from src.sec_edgar import KNOWN_INSTITUTIONS
except ImportError:
    def build_institutional_heatmap(): return []
    KNOWN_INSTITUTIONS = {}

try:
    from src.live_commodities_v2 import fetch_top_commodities
except ImportError:
    def fetch_top_commodities(limit=10): return []

try:
    from src.crypto_data import fetch_top_crypto
except ImportError:
    def fetch_top_crypto(limit=10): return []

try:
    from src.forex_data import fetch_all_forex
except ImportError:
    def fetch_all_forex(): return []

try:
    from src.commodities_data import SEASONAL_MOVES, MONTHS_HE
    from src.hot_score import SUPPLY_SIGNALS
    SEASONAL_OK = True
except ImportError:
    SEASONAL_OK = False
    SEASONAL_MOVES = {}
    SUPPLY_SIGNALS = {}
    MONTHS_HE = {}

inject_rtl()

st.title("🎯 ניתוח השקעה — Top 10 לפי קטגוריה")
st.caption("ניתוח מולטי-סיגנל | מניות + סחורות + קריפטו + Forex")
st.warning("⚠️ המידע לצרכי מחקר בלבד — אינו ייעוץ השקעות. תמיד התייעץ עם יועץ מוסמך.")

st.divider()

# ── Category selector ─────────────────────────────────────
category = st.selectbox(
    "בחר קטגוריה לניתוח",
    ["🐋 מניות — Top מוסדי", "🛢️ סחורות — Top חמות", "🪙 קריפטו — Top 10", "💱 Forex — הכי תנודתי"],
)

now_month = datetime.now().month

@st.cache_data(ttl=3600, show_spinner=False)
def load_stocks():
    return build_institutional_heatmap()

@st.cache_data(ttl=300, show_spinner=False)
def load_commodities():
    return fetch_top_commodities(limit=30)

@st.cache_data(ttl=120, show_spinner=False)
def load_crypto():
    return fetch_top_crypto(limit=20)

@st.cache_data(ttl=180, show_spinner=False)
def load_forex():
    return fetch_all_forex()

def render_signal_card(sig: dict):
    w = sig["weight"]
    sc = sig["score"]
    bar_pct = int(sc)
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.markdown(f"**{sig['label']}**")
        c2.markdown(f"<span style='color:{sig['color']};font-weight:700'>{sig['signal']}</span>",
                    unsafe_allow_html=True)
        c3.markdown(f"**{sig['weighted_score']}** / {w} נק'")
        st.progress(bar_pct / 100)
        st.caption(f"ערך: {sig['value']} | {sig['explanation']}")

def render_analysis(result: dict):
    if not result:
        st.error("לא ניתן לנתח נכס זה")
        return

    score = result["total_score"]
    color = result["rec_color"]

    # Header
    col_score, col_rec = st.columns([1, 3])
    with col_score:
        st.markdown(f"""
<div style="text-align:center;border:3px solid {color};border-radius:50%;
     width:90px;height:90px;display:flex;align-items:center;justify-content:center;
     margin:auto;font-size:28px;font-weight:900;color:{color}">
  {score}
</div>
<div style="text-align:center;font-size:12px;color:#888;margin-top:6px">ציון מתוך 100</div>
""", unsafe_allow_html=True)
    with col_rec:
        st.markdown(f"## {result['rec_emoji']} {result['recommendation']}")
        st.markdown(f"**{result['rec_detail']}**")
        if result.get("price"):
            sign = "+" if result["change_pct"] > 0 else ""
            st.caption(f"מחיר: ${result['price']:,.4f} | שינוי: {sign}{result['change_pct']:.2f}% | RSI: {result['rsi'] or '—'}")

    st.divider()

    # Signals breakdown
    st.subheader("פירוט סיגנלים")
    for sig in result["signals"].values():
        render_signal_card(sig)

    # Custom notes
    if result.get("custom_notes"):
        st.divider()
        st.markdown("#### 📌 הערות נוספות")
        for note in result["custom_notes"]:
            st.info(note)

    st.caption(f"עודכן: {result['timestamp']} | {result['disclaimer']}")

# ══════════════════════════════════════════════════════════
# STOCKS
# ══════════════════════════════════════════════════════════
if "מניות" in category:
    with st.spinner("טוען Top 10 מניות מוסדיות..."):
        heatmap = load_stocks()

    if not heatmap:
        st.warning("לא ניתן לטעון נתוני מניות")
        st.stop()

    top10 = heatmap[:10]
    names = [h["name"] for h in top10]
    selected = st.selectbox("בחר מניה לניתוח מעמיק", names)
    stock_data = next((h for h in top10 if h["name"] == selected), None)

    # Summary table
    st.subheader("Top 10 מניות — לפי ווליום מוסדי")
    rows = [{"#": h["rank"], "מניה": h["name"],
             "ווליום מוסדי": f"${h['total_value_m']:,.0f}M",
             "מוסדות": h["institution_count"]}
            for h in top10]
    st.dataframe(pd.DataFrame(rows).set_index("#"), use_container_width=True, hide_index=True)

    if stock_data:
        st.divider()
        st.subheader(f"🔍 ניתוח מעמיק — {selected}")

        from src.market_data import get_symbol
        sym = get_symbol(stock_data.get("cusip",""), selected)

        inst_consistency = 0
        try:
            from src.recurring_actions import analyze_institution_patterns
            from src.sec_edgar import KNOWN_INSTITUTIONS as KI
            for cik in list(KI.keys())[:3]:
                res = analyze_institution_patterns(cik, num_filings=4)
                for p in res.get("patterns", []):
                    if selected[:6].upper() in p["name"].upper():
                        inst_consistency = max(inst_consistency, p["consistency_pct"])
                        break
        except Exception:
            pass

        with st.spinner(f"מנתח {selected}..."):
            result = analyze_with_insider(
                name=selected,
                asset_type="stock",
                symbol=sym or "",
                inst_value_m=stock_data["total_value_m"],
                inst_count=stock_data["institution_count"],
                inst_consistency_pct=inst_consistency,
                seasonal_score=10,
                supply_score=5,
                include_insider=True,
                custom_notes=[
                    f"מחזיקים: {', '.join([i['name'] for i in stock_data['institutions'][:4]])}",
                    f"סה\"כ ווליום מוסדי: ${stock_data['total_value_m']:,.0f}M",
                ]
            )
        render_analysis(result)

# ══════════════════════════════════════════════════════════
# COMMODITIES
# ══════════════════════════════════════════════════════════
elif "סחורות" in category:
    with st.spinner("טוען סחורות..."):
        commodities = load_commodities()

    available = [c for c in commodities if c.get("available")][:10]
    if not available:
        st.warning("לא ניתן לטעון נתוני סחורות")
        st.stop()

    names = [f"{c['emoji']} {c['name']}" for c in available]
    selected = st.selectbox("בחר סחורה לניתוח", names)
    com_data = next((c for c in available if f"{c['emoji']} {c['name']}" == selected), None)

    st.subheader("Top 10 סחורות — לפי תנודה")
    rows = [{"#": i+1, "סחורה": f"{c['emoji']} {c['name']}",
             "מחיר": f"${c['price']:,.4f}",
             "% שינוי": f"{'+' if c['change_pct']>0 else ''}{c['change_pct']:.2f}%",
             "קטגוריה": c["category"]}
            for i, c in enumerate(available)]
    st.dataframe(pd.DataFrame(rows).set_index("#"), use_container_width=True, hide_index=True)

    if com_data:
        st.divider()
        st.subheader(f"🔍 ניתוח מעמיק — {com_data['name']}")

        sea_score = 0
        sup_score = 0
        if SEASONAL_OK:
            month_data = SEASONAL_MOVES.get(com_data["key"], {}).get("monthly", {}).get(now_month, {})
            hist_move = month_data.get("avg_move", 0)
            is_hot = month_data.get("hot", False)
            sea_score = 20 if (is_hot and hist_move > 3) else 14 if is_hot else 10 if hist_move > 0 else 4
            sigs = SUPPLY_SIGNALS.get(com_data["key"], [])
            sup_score = round(sum(s["severity"] for s in sigs) / max(len(sigs), 1)) if sigs else 0

        with st.spinner(f"מנתח {com_data['name']}..."):
            result = analyze_asset(
                name=com_data["name"],
                asset_type="commodity",
                symbol=com_data.get("twelve", ""),
                yahoo_ticker=com_data.get("yahoo", ""),
                inst_value_m=0,
                inst_count=0,
                seasonal_score=sea_score,
                supply_score=sup_score,
                custom_notes=[f"קטגוריה: {com_data['category']}",
                               f"מקור: {com_data.get('source','—')}"]
            )
        render_analysis(result)

# ══════════════════════════════════════════════════════════
# CRYPTO
# ══════════════════════════════════════════════════════════
elif "קריפטו" in category:
    with st.spinner("טוען קריפטו..."):
        coins = load_crypto()

    top10 = coins[:10]
    if not top10:
        st.warning("לא ניתן לטעון נתוני קריפטו")
        st.stop()

    names = [f"{c['name']} ({c['symbol']})" for c in top10]
    selected = st.selectbox("בחר מטבע לניתוח", names)
    coin = next((c for c in top10 if f"{c['name']} ({c['symbol']})" == selected), None)

    st.subheader("Top 10 קריפטו — לפי שווי שוק")
    rows = [{"#": c["rank"], "מטבע": f"{c['name']} ({c['symbol']})",
             "מחיר": f"${c['price']:,.2f}",
             "% 24h": f"{'+' if c['change_24h']>0 else ''}{c['change_24h']:.2f}%",
             "שווי שוק": f"${c['market_cap']/1e9:.1f}B",
             "מוסדיים": "✅" if c.get("has_etf") else ("🏛️" if c.get("inst_holders") else "")}
            for c in top10]
    st.dataframe(pd.DataFrame(rows).set_index("#"), use_container_width=True, hide_index=True)

    if coin:
        st.divider()
        st.subheader(f"🔍 ניתוח מעמיק — {coin['name']}")

        inst_v = sum(e["aum_b"] * 1000 for e in [
            {"aum_b": 25} if coin["id"] == "bitcoin" else
            {"aum_b": 9}  if coin["id"] == "ethereum" else
            {"aum_b": 0}
        ])

        notes = []
        if coin.get("inst_holders"):
            notes.append("🏛️ מחזיקים מוסדיים: " + " | ".join(coin["inst_holders"][:3]))
        if coin.get("has_etf"):
            notes.append("✅ יש ETF מוסדי מאושר — אות אמון גדול")
        notes.append(f"שווי שוק: ${coin['market_cap']/1e9:.1f}B | ווליום 24h: ${coin['volume_24h']/1e6:.0f}M")

        with st.spinner(f"מנתח {coin['name']}..."):
            result = analyze_asset(
                name=coin["name"],
                asset_type="crypto",
                symbol=f"{coin['symbol']}/USD",
                inst_value_m=inst_v,
                inst_count=len(coin.get("inst_holders", [])),
                inst_consistency_pct=80 if coin.get("has_etf") else 30,
                seasonal_score=10,
                supply_score=5,
                custom_notes=notes,
            )
        render_analysis(result)

# ══════════════════════════════════════════════════════════
# FOREX
# ══════════════════════════════════════════════════════════
else:
    with st.spinner("טוען Forex..."):
        forex = load_forex()

    top10 = [f for f in forex if f.get("available")][:10]
    if not top10:
        st.warning("לא ניתן לטעון נתוני Forex")
        st.stop()

    names = [f"{f['emoji']} {f['pair']} — {f['name']}" for f in top10]
    selected = st.selectbox("בחר זוג לניתוח", names)
    pair = next((f for f in top10 if f"{f['emoji']} {f['pair']} — {f['name']}" == selected), None)

    st.subheader("Top 10 Forex — לפי תנודתיות")
    rows = [{"#": i+1, "זוג": f"{f['emoji']} {f['pair']}",
             "שם": f["name"], "שער": f"{f['price']:.5f}",
             "% שינוי": f"{'+' if f['change_pct']>0 else ''}{f['change_pct']:.4f}%",
             "קטגוריה": f["category"]}
            for i, f in enumerate(top10)]
    st.dataframe(pd.DataFrame(rows).set_index("#"), use_container_width=True, hide_index=True)

    if pair:
        st.divider()
        st.subheader(f"🔍 ניתוח מעמיק — {pair['pair']}")
        with st.spinner(f"מנתח {pair['pair']}..."):
            result = analyze_asset(
                name=pair["pair"],
                asset_type="forex",
                symbol=pair.get("twelve", ""),
                yahoo_ticker=pair.get("yahoo", ""),
                inst_count=0,
                seasonal_score=8,
                supply_score=4,
                custom_notes=[
                    f"קטגוריה: {pair['category']}",
                    "Forex מושפע מריבית בנקים מרכזיים + נתוני מאקרו"
                ]
            )
        render_analysis(result)
