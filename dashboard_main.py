import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Fix 5: Safe imports with fallbacks ───────────────────
try:
    from src.sec_edgar import (
        get_recent_13f_filings, get_holdings_from_filing,
        KNOWN_INSTITUTIONS, INSTITUTION_PROFILES
    )
except ImportError as e:
    st.error(f"שגיאה קריטית: src/sec_edgar.py — {e}")
    st.stop()

try:
    from src.news_fetcher import fetch_news
except ImportError:
    def fetch_news(*a, **kw): return []

try:
    from src.changes_tracker import get_portfolio_changes
except ImportError:
    def get_portfolio_changes(*a): return {"error": "מודול חסר"}

try:
    from src.aggregator import build_institutional_heatmap
except ImportError:
    def build_institutional_heatmap(*a): return []

try:
    from src.market_data import enrich_holdings, get_symbol
except ImportError:
    def enrich_holdings(h, **kw): return h
    def get_symbol(*a): return None

try:
    from src.institutional_overlay import find_institutional_holders, render_institutional_holders
except ImportError:
    def find_institutional_holders(*a, **kw): return []
    def render_institutional_holders(*a, **kw): pass

try:
    from src.recurring_actions import analyze_institution_patterns
except ImportError:
    def analyze_institution_patterns(*a, **kw): return {"error": "מודול חסר", "patterns": []}

# ── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="Whale Tracker",
    page_icon="🐋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Fix 4: Full RTL CSS using correct Streamlit selectors ─
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    direction: rtl;
    text-align: right;
}
[data-testid="stSidebar"] {
    direction: rtl;
    text-align: right;
}
[data-testid="stMarkdownContainer"] {
    text-align: right;
}
[data-testid="stMetricValue"] {
    text-align: right;
}
.stTabs [data-baseweb="tab-list"] {
    direction: rtl;
}
.stDataFrame {
    direction: rtl;
}
.news-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
    background: #fafafa;
}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale Tracker — SEC 13F Institutional Holdings")
st.caption("נתונים רשמיים ממאגר SEC EDGAR | מתעדכן לפי דיווחים רבעוניים")

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.header("הגדרות")
    page = st.radio(
        "עמוד",
        ["🔥 לוח הכרישים", "🏦 מוסד ספציפי"],
        label_visibility="collapsed"
    )
    st.divider()
    if page == "🏦 מוסד ספציפי":
        selected_inst = st.selectbox(
            "בחר מוסד",
            options=list(KNOWN_INSTITUTIONS.keys()),
            format_func=lambda x: f"{INSTITUTION_PROFILES[x]['name_he']} — {KNOWN_INSTITUTIONS[x]}",
        )
        top_n = st.slider("מספר אחזקות", 5, 30, 15)
    st.divider()
    st.caption("נתונים: SEC EDGAR (data.sec.gov)")

# ── Fix 2: All API calls cached ───────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_filings(cik, limit=2):
    return get_recent_13f_filings(cik, limit=limit)

@st.cache_data(ttl=3600, show_spinner=False)
def load_holdings(cik, accession):
    return get_holdings_from_filing(cik, accession)

@st.cache_data(ttl=7200, show_spinner=False)
def load_heatmap():
    return build_institutional_heatmap()

@st.cache_data(ttl=3600, show_spinner=False)
def load_changes(cik):
    return get_portfolio_changes(cik)

@st.cache_data(ttl=600, show_spinner=False)
def load_news(cik):
    return fetch_news(cik, max_results=5)

@st.cache_data(ttl=3600, show_spinner=False)
def load_enriched(cik, accession):
    h = get_holdings_from_filing(cik, accession)
    return enrich_holdings(h[:15]) if h else []

# ══════════════════════════════════════════════════════════
# PAGE 1 — Heatmap
# ══════════════════════════════════════════════════════════
if page == "🔥 לוח הכרישים":
    st.subheader("🔥 Top 20 מניות — לפי ווליום מוסדי")
    st.caption("מחושב על פי 8 קרנות הגידור הגדולות ביותר")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("קרנות במעקב", len(KNOWN_INSTITUTIONS))
    col_b.metric("מניות מנותחות", "Top 20")
    col_c.metric("מקור", "SEC 13F-HR")
    st.divider()

    with st.spinner("שולף ומנתח אחזקות... (30-60 שניות)"):
        heatmap = load_heatmap()

    if not heatmap:
        st.warning("לא ניתן לשלוף נתונים כרגע. נסה שוב.")
        st.stop()

    top1 = heatmap[0]
    total_val = sum(h["total_value_m"] for h in heatmap)
    c1, c2, c3 = st.columns(3)
    c1.metric("שווי כולל Top 20", f"${total_val:,.0f}M")
    c2.metric("המניה הכי חמה", top1["name"])
    c3.metric("ווליום מוסדי #1", f"${top1['total_value_m']:,.0f}M")
    st.divider()

    col_table, col_bar = st.columns([3, 2])
    with col_table:
        st.subheader("דירוג מלא")
        rows = []
        for h in heatmap:
            inst_names = ", ".join([i["name"].split(" ")[0] for i in h["institutions"][:3]])
            if len(h["institutions"]) > 3:
                inst_names += f' +{len(h["institutions"])-3}'
            rows.append({
                "#": h["rank"],
                "שם": h["name"],
                "ווליום ($M)": h["total_value_m"],
                "# מוסדות": h["institution_count"],
                "מחזיקים": inst_names,
                "CUSIP": h["cusip"],
            })
        df = pd.DataFrame(rows).set_index("#")
        st.dataframe(df, use_container_width=True, height=560)

    with col_bar:
        st.subheader("Top 10")
        bar_data = pd.DataFrame([
            {"מניה": h["name"][:18], "ווליום ($M)": h["total_value_m"]}
            for h in heatmap[:10]
        ]).set_index("מניה")
        st.bar_chart(bar_data)

    st.divider()
    st.subheader("פירוט מחזיקים לפי מניה")
    selected_stock = st.selectbox("בחר מניה", [h["name"] for h in heatmap])
    stock_data = next((h for h in heatmap if h["name"] == selected_stock), None)
    if stock_data:
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("ווליום מוסדי", f"${stock_data['total_value_m']:,.0f}M")
        sc2.metric("מוסדות מחזיקים", stock_data["institution_count"])
        sc3.metric("CUSIP", stock_data["cusip"] or "—")
        inst_df = pd.DataFrame([
            {"מוסד": i["name"], "שווי ($M)": round(i["value_thousands"]/1000, 1)}
            for i in stock_data["institutions"]
        ])
        st.dataframe(inst_df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# PAGE 2 — Institution
# ══════════════════════════════════════════════════════════
else:
    inst_name = KNOWN_INSTITUTIONS[selected_inst]
    st.title(f"🏦 {inst_name}")

    with st.spinner("שולף דיווחים..."):
        filings = load_filings(selected_inst, limit=2)

    if not filings:
        st.error("לא נמצאו דיווחי 13F")
        st.stop()

    latest = filings[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("מוסד", inst_name)
    c2.metric("תאריך דיווח אחרון", latest["date"])
    c3.metric("סוג דיווח", latest["form"])

    profile = INSTITUTION_PROFILES.get(selected_inst, {})
    if profile:
        with st.container(border=True):
            col_desc, col_stats = st.columns([2, 1])
            with col_desc:
                st.markdown(f"### {profile['name_he']}")
                st.caption(profile["title"])
                st.write(profile["desc"])
            with col_stats:
                st.metric("מנהל", profile["manager"])
                st.metric("סגנון", profile["style"])
                st.metric("נכסים", profile["aum"])
                st.metric("נוסדה", profile["founded"])

    st.divider()
    tab1, tab2, tab3, tab4 = st.tabs(["📊 אחזקות", "📡 RSI + מחיר", "🔄 שינויים", "📰 חדשות"])

    with tab1:
        with st.spinner("שולף אחזקות..."):
            holdings = load_holdings(selected_inst, latest["accession"])
        if not holdings:
            st.warning("לא ניתן לשלוף פירוט אחזקות.")
        else:
            total_val = sum(h["value_thousands"] for h in holdings) / 1000
            st.metric("שווי תיק כולל", f"${total_val:,.0f}M")
            df = pd.DataFrame(holdings[:top_n])
            df["value_m"]  = (df["value_thousands"] / 1000).round(1)
            df["pct"]      = (df["value_thousands"] / sum(h["value_thousands"] for h in holdings) * 100).round(2)
            df["shares_fmt"] = df["shares"].apply(lambda x: f"{x:,}" if x > 0 else "—")
            df_d = df[["name","value_m","pct","shares_fmt","cusip"]].copy()
            df_d.columns = ["שם מניה","שווי ($M)","% מהתיק","מניות","CUSIP"]
            df_d.index = range(1, len(df_d)+1)
            st.subheader(f"Top {top_n} אחזקות")
            st.dataframe(df_d, use_container_width=True, height=420)
            st.bar_chart(df.set_index("name")[["value_m"]].head(10))

    with tab2:
        with st.spinner("שולף RSI ומחירים..."):
            enriched = load_enriched(selected_inst, latest["accession"])
        if enriched:
            oversold   = [h for h in enriched if h.get("signal") == "OVERSOLD"]
            overbought = [h for h in enriched if h.get("signal") == "OVERBOUGHT"]
            if oversold:
                st.success(f"OVERSOLD — {len(oversold)} מניות מתחת ל-RSI 30")
            if overbought:
                st.warning(f"OVERBOUGHT — {len(overbought)} מניות מעל RSI 70")
            rsi_rows = [{
                "מניה": h["name"],
                "סימבול": h.get("symbol","—"),
                "מחיר": f"${h.get('price',0):,.2f}" if h.get("price") else "—",
                "שינוי %": f"{'+' if h.get('change_pct',0)>0 else ''}{h.get('change_pct',0):.2f}%",
                "RSI": h.get("rsi", "—"),
                "סיגנל": h.get("signal","—"),
                "שווי ($M)": round(h["value_thousands"]/1000, 1),
            } for h in enriched]
            df_rsi = pd.DataFrame(rsi_rows)
            df_rsi.index = range(1, len(df_rsi)+1)
            st.dataframe(df_rsi, use_container_width=True, height=460)
            st.caption("מקור: Twelve Data API | RSI: 14 ימים")

    with tab3:
        with st.spinner("משווה דיווחים..."):
            changes = load_changes(selected_inst)
        if changes.get("error"):
            st.warning(changes["error"])
        else:
            st.caption(f"השוואה: {changes['previous_date']} → {changes['latest_date']}")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🟢 פוזיציות חדשות")
                for h in changes.get("new",[]):
                    st.success(f"+ {h['name']} — ${h['value_thousands']/1000:,.0f}M")
                if not changes.get("new"): st.caption("אין")
                st.markdown("#### 📈 הגדלות")
                for h in changes.get("increased",[]):
                    st.info(f"▲ {h['name']} +{h['pct_change']}% | ${h['value_thousands']/1000:,.0f}M")
                if not changes.get("increased"): st.caption("אין")
            with c2:
                st.markdown("#### 🔴 פוזיציות שנסגרו")
                for h in changes.get("sold",[]):
                    st.error(f"- {h['name']} — ${h['value_thousands']/1000:,.0f}M")
                if not changes.get("sold"): st.caption("אין")
                st.markdown("#### 📉 קיצוצים")
                for h in changes.get("decreased",[]):
                    st.warning(f"▼ {h['name']} {h['pct_change']}% | ${h['value_thousands']/1000:,.0f}M")
                if not changes.get("decreased"): st.caption("אין")

            st.divider()
            st.markdown("#### 🔁 דפוסים חוזרים")
            with st.spinner("בודק היסטוריה..."):
                rec = analyze_institution_patterns(selected_inst, num_filings=4)
            if not rec.get("error") and rec.get("patterns"):
                buy_rec  = [p for p in rec["patterns"] if "קנייה" in p["pattern_type"]][:5]
                sell_rec = [p for p in rec["patterns"] if "מכירה" in p["pattern_type"]][:3]
                if buy_rec:
                    st.markdown("**קניות שחוזרות:**")
                    for p in buy_rec:
                        seas = f" | {p['dominant_quarter']}" if p["is_seasonal"] else ""
                        st.success(f"🟢 {p['name']} — {p['consistency_pct']}% | {p['occurrences']} פעמים | ${p['avg_value_m']:,.0f}M{seas}")
                if sell_rec:
                    st.markdown("**מכירות שחוזרות:**")
                    for p in sell_rec:
                        st.error(f"🔴 {p['name']} — {p['consistency_pct']}% עקביות")

    with tab4:
        with st.spinner("שולף חדשות..."):
            news = load_news(selected_inst)
        if not news:
            st.warning("לא נמצאו חדשות.")
        else:
            for item in news:
                with st.container(border=True):
                    st.markdown(f"**{item['title']}**")
                    st.caption(item["date"])
                    st.write(item["summary"])
                    st.markdown(f"[קרא עוד ↗]({item['link']})")
        st.caption("מקור: Google News RSS | SEC EDGAR")
