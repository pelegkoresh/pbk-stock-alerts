import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl
from src.crypto_data import fetch_top_crypto, fetch_crypto_global, get_institutional_crypto_etfs

inject_rtl()

st.title("₿ קריפטו — מעקב מוסדי")
st.caption(f"עדכון: {datetime.now().strftime('%H:%M:%S')} | מקור: CoinGecko API (חינמי)")

@st.cache_data(ttl=120, show_spinner=False)
def load_crypto(limit):
    return fetch_top_crypto(limit)

@st.cache_data(ttl=120, show_spinner=False)
def load_global():
    return fetch_crypto_global()

col_ref, col_lim = st.columns([1, 2])
with col_ref:
    if st.button("🔄 רענן"):
        st.cache_data.clear()
        st.rerun()
with col_lim:
    limit = st.selectbox("כמה מטבעות", [25, 50, 100], index=1)

with st.spinner("שולף נתוני קריפטו..."):
    coins = load_crypto(limit)
    global_data = load_global()

if not coins:
    st.error("לא ניתן לשלוף נתוני קריפטו. CoinGecko מגביל בקשות — נסה בעוד דקה.")
    st.stop()

# Global metrics
g1, g2, g3, g4, g5 = st.columns(5)
mcap = global_data.get("total_market_cap", 0)
vol  = global_data.get("total_volume", 0)
g1.metric("שווי שוק כולל", f"${mcap/1e12:.2f}T")
g2.metric("ווליום 24h", f"${vol/1e9:.1f}B")
g3.metric("דומיננטיות BTC", f"{global_data.get('btc_dominance', 0)}%")
g4.metric("דומיננטיות ETH", f"{global_data.get('eth_dominance', 0)}%")
g5.metric("שינוי שוק 24h", f"{global_data.get('market_cap_change_24h', 0):.2f}%",
          delta=f"{global_data.get('market_cap_change_24h', 0):.2f}%")

st.divider()

tab1, tab2, tab3 = st.tabs(["🔥 הכי חמות", "📋 כל המטבעות", "🏛️ מוסדיים"])

# ── TAB 1: Hot ────────────────────────────────────────────
with tab1:
    top_up   = sorted(coins, key=lambda x: x.get("change_24h", 0), reverse=True)[:6]
    top_down = sorted(coins, key=lambda x: x.get("change_24h", 0))[:6]

    c_up, c_dn = st.columns(2)
    with c_up:
        st.markdown("### 📈 עולות 24h")
        for c in top_up:
            with st.container(border=True):
                a, b = st.columns([2, 1])
                with a:
                    st.markdown(f"**{c['name']} ({c['symbol']})**")
                    if c.get("inst_holders"):
                        st.caption("🏛️ " + " | ".join(c["inst_holders"][:2]))
                    if c.get("has_etf"):
                        st.caption("✅ יש ETF מוסדי")
                with b:
                    st.metric("מחיר", f"${c['price']:,.2f}", delta=f"+{c['change_24h']:.2f}%")
                st.caption(f"שווי שוק: ${c['market_cap']/1e9:.1f}B | ווליום: ${c['volume_24h']/1e6:.0f}M")

    with c_dn:
        st.markdown("### 📉 יורדות 24h")
        for c in top_down:
            with st.container(border=True):
                a, b = st.columns([2, 1])
                with a:
                    st.markdown(f"**{c['name']} ({c['symbol']})**")
                    if c.get("inst_holders"):
                        st.caption("🏛️ " + " | ".join(c["inst_holders"][:2]))
                with b:
                    st.metric("מחיר", f"${c['price']:,.2f}", delta=f"{c['change_24h']:.2f}%")
                st.caption(f"שווי שוק: ${c['market_cap']/1e9:.1f}B")

# ── TAB 2: Full table ─────────────────────────────────────
with tab2:
    rows = []
    for c in coins:
        rows.append({
            "#": c["rank"],
            "מטבע": f"{c['name']} ({c['symbol']})",
            "מחיר": f"${c['price']:,.4f}" if c["price"] < 1 else f"${c['price']:,.2f}",
            "% 24h": f"{'+' if c['change_24h']>0 else ''}{c['change_24h']:.2f}%",
            "% 7d":  f"{'+' if c['change_7d']>0 else ''}{c['change_7d']:.2f}%",
            "שווי שוק ($B)": round(c["market_cap"]/1e9, 2),
            "ווליום 24h ($M)": round(c["volume_24h"]/1e6, 1),
            "מוסדיים": "✅" if c.get("has_etf") else ("🏛️" if c.get("inst_holders") else ""),
        })

    df = pd.DataFrame(rows).set_index("#")

    def color_pct(val):
        if str(val).startswith("+"): return "color:#c0392b;font-weight:600"
        if str(val).startswith("-"): return "color:#27ae60;font-weight:600"
        return ""

    st.dataframe(
        df.style.map(color_pct, subset=["% 24h", "% 7d"]),
        use_container_width=True, height=600
    )

# ── TAB 3: Institutional ──────────────────────────────────
with tab3:
    st.subheader("🏛️ החזקות מוסדיות ידועות בקריפטו")
    st.caption("מקורות: SEC filings, Bloomberg, דוחות ציבוריים")

    etfs = get_institutional_crypto_etfs()
    total_aum = sum(e["aum_b"] for e in etfs)
    st.metric("סה\"כ AUM ETF קריפטו מוסדי", f"${total_aum:.1f}B")
    st.divider()

    df_etf = pd.DataFrame(etfs)
    df_etf.columns = ["שם ETF", "מנפיק", "AUM ($B)", "מטבע"]
    df_etf.index = range(1, len(df_etf)+1)
    st.dataframe(df_etf, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🐳 מטבעות עם מחזיקים מוסדיים")
    for c in coins[:20]:
        if c.get("inst_holders") or c.get("has_etf"):
            with st.container(border=True):
                a, b = st.columns([2, 1])
                with a:
                    st.markdown(f"**{c['name']} ({c['symbol']})**")
                    for h in c.get("inst_holders", []):
                        st.caption(f"🏛️ {h}")
                with b:
                    st.metric("מחיר", f"${c['price']:,.2f}")
                    st.caption(f"ETF מוסדי: {'✅ כן' if c.get('has_etf') else '❌ לא'}")

    st.divider()
    st.caption("מקורות: SEC filings, Bloomberg Terminal, CoinGecko, דוחות ציבוריים | אינו ייעוץ השקעות")
