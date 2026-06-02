import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.sec_edgar import get_recent_13f_filings, get_holdings_from_filing, KNOWN_INSTITUTIONS, INSTITUTION_PROFILES
from src.news_fetcher import fetch_news
from src.changes_tracker import get_portfolio_changes
from src.aggregator import build_institutional_heatmap
from src.market_data import enrich_holdings
from src.institutional_overlay import find_institutional_holders, render_institutional_holders
from src.market_data import enrich_holdings, get_symbol

st.set_page_config(
    page_title="Whale Tracker — Institutional Monitor",
    page_icon="🐋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.rank-badge {
    display:inline-flex;align-items:center;justify-content:center;
    width:28px;height:28px;border-radius:50%;
    font-size:12px;font-weight:700;color:#fff;
    background:#1565c0;flex-shrink:0;
}
.rank-badge.top3 { background:#b8860b; }
.heat-card {
    border:0.5px solid #e0e0e0;border-radius:10px;
    padding:14px 18px;margin-bottom:8px;
    background:#fff;
    display:flex;align-items:center;gap:14px;
}
.heat-name { font-size:15px;font-weight:600;color:#1a1a2e;flex:1; }
.heat-val  { font-size:18px;font-weight:700;color:#1565c0;min-width:100px;text-align:right; }
.heat-meta { font-size:12px;color:#888;margin-top:3px; }
.inst-pill {
    display:inline-block;padding:2px 8px;border-radius:12px;
    font-size:11px;background:#e8f4fd;color:#1565c0;margin:2px;
}
.news-card { border:1px solid #e0e0e0;border-radius:8px;padding:12px 16px;margin-bottom:10px;background:#fafafa; }
.news-title { font-weight:600;font-size:14px;color:#1a1a2e; }
.news-meta  { font-size:11px;color:#888;margin-top:4px; }
.news-summary { font-size:13px;color:#444;margin-top:6px; }
.change-new  { color:#1a7a1a;font-weight:600; }
.change-sold { color:#c0392b;font-weight:600; }
.change-up   { color:#1a7a1a; }
.change-down { color:#c0392b; }
.last-deal {
    border-radius:12px;padding:18px 22px;margin-top:8px;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.header("🐋 Whale Tracker")
    page = st.radio("עמוד", ["🔥 לוח הכרישים", "🏦 מוסד ספציפי"], label_visibility="collapsed")
    st.divider()
    if page == "🏦 מוסד ספציפי":
        selected_inst = st.selectbox(
            "בחר מוסד",
            options=list(KNOWN_INSTITUTIONS.keys()),
            format_func=lambda x: f'{INSTITUTION_PROFILES[x]["name_he"]} — {KNOWN_INSTITUTIONS[x]}',
        )
        top_n = st.slider("מספר אחזקות", 5, 30, 15)
    st.divider()
    st.caption("נתונים: SEC EDGAR (data.sec.gov)")
    st.caption("חדשות: Google News RSS")

# ════════════════════════════════════════════════════════════
# PAGE 1 — Institutional Heatmap
# ════════════════════════════════════════════════════════════
if page == "🔥 לוח הכרישים":
    st.title("🔥 לוח הכרישים — Top 20 מניות מוסדיות")
    st.caption("המניות עם הווליום המוסדי הגבוה ביותר | מחושב על פי 8 קרנות הגידור הגדולות ביותר")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("קרנות במעקב", len(KNOWN_INSTITUTIONS), help="BlackRock, Berkshire, Vanguard ועוד — קרנות שמנהלות מיליארדים")
    col_b.metric("מניות מנותחות", "Top 20", help="20 המניות עם הכי הרבה כסף מוסדי — אלה שהלוויתנים אוהבים הכי הרבה")
    col_c.metric("מקור", "SEC 13F-HR", help="נתונים רשמיים מ-SEC.gov — הרגולטור האמריקאי. 100% חוקי וחינמי")

    st.divider()

    with st.spinner("שולף ומנתח אחזקות מכל המוסדות... (30-60 שניות)"):
        heatmap = build_institutional_heatmap()

    if not heatmap:
        st.error("לא ניתן לשלוף נתונים כרגע.")
        st.stop()

    # Summary metrics
    total_inst_value = sum(h["total_value_m"] for h in heatmap)
    top1 = heatmap[0] if heatmap else None
    col1, col2, col3 = st.columns(3)
    col1.metric("שווי כולל Top 20", f"${total_inst_value:,.0f}M")
    if top1:
        col2.metric("המניה הכי חמה", top1["name"])
        col3.metric("ווליום מוסדי #1", f"${top1['total_value_m']:,.0f}M")

    st.divider()

    # Heatmap table
    col_table, col_bar = st.columns([3, 2])

    with col_table:
        st.subheader("דירוג מלא")
        st.caption("ווליום ($M) = מיליוני דולרים | # מוסדות = כמה קרנות שונות מחזיקות | CUSIP = מזהה ייחודי של המניה")
        rows = []
        for h in heatmap:
            inst_names = ", ".join([i["name"].split(" ")[0] for i in h["institutions"][:3]])
            if len(h["institutions"]) > 3:
                inst_names += f" +{len(h['institutions'])-3}"
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
        st.subheader("Top 10 — ווליום מוסדי")
        bar_data = pd.DataFrame([
            {"מניה": h["name"][:20], "ווליום ($M)": h["total_value_m"]}
            for h in heatmap[:10]
        ]).set_index("מניה")
        st.bar_chart(bar_data)

    st.divider()
    st.subheader("פירוט מחזיקים לפי מניה")
    selected_stock = st.selectbox(
        "בחר מניה לפירוט",
        options=[h["name"] for h in heatmap],
    )
    stock_data = next((h for h in heatmap if h["name"] == selected_stock), None)
    if stock_data:
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("ווליום מוסדי כולל", f"${stock_data['total_value_m']:,.0f}M")
        sc2.metric("מספר מוסדות מחזיקים", stock_data["institution_count"])
        sc3.metric("CUSIP", stock_data["cusip"] or "—")
        st.markdown("**מחזיקים:**")
        inst_df = pd.DataFrame([
            {"מוסד": i["name"], "שווי ($M)": round(i["value_thousands"]/1000, 1)}
            for i in stock_data["institutions"]
        ])
        st.dataframe(inst_df, use_container_width=True, hide_index=True)

    if stock_data:
        st.subheader('🏛️ פירוט מוסדות מחזיקים')
        from src.sec_edgar import get_recent_13f_filings, get_holdings_from_filing, KNOWN_INSTITUTIONS
        import time
        hcache = {}
        for cik in list(KNOWN_INSTITUTIONS.keys())[:5]:
            filings = get_recent_13f_filings(cik, limit=1)
            if filings:
                h = get_holdings_from_filing(cik, filings[0]['accession'])
                hcache[cik] = {'holdings': h, 'filing_date': filings[0]['date']}
            time.sleep(0.15)
        holders = find_institutional_holders(hcache, asset_name=selected_stock, cusip=stock_data.get('cusip',''))
        render_institutional_holders(holders, selected_stock)

# ════════════════════════════════════════════════════════════
# PAGE 2 — Specific Institution
# ════════════════════════════════════════════════════════════
else:
    inst_name = KNOWN_INSTITUTIONS[selected_inst]
    st.title(f"🏦 {inst_name}")

    with st.spinner(f"שולף 13F..."):
        filings = get_recent_13f_filings(selected_inst, limit=2)

    if not filings:
        st.error("לא נמצאו דיווחי 13F")
        st.stop()

    latest = filings[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("מוסד", inst_name)
    col2.metric("תאריך דיווח אחרון", latest["date"])
    col3.metric("סוג דיווח", latest["form"])

    profile = INSTITUTION_PROFILES.get(selected_inst, {})
    if profile:
        st.markdown(f"""
<div style="border:0.5px solid var(--color-border-tertiary);border-radius:12px;padding:16px 20px;margin:12px 0;background:var(--color-background-secondary)">
  <div style="display:flex;align-items:flex-start;gap:20px;flex-wrap:wrap">
    <div style="flex:1;min-width:200px">
      <div style="font-size:20px;font-weight:600;color:var(--color-text-primary)">{profile["name_he"]}</div>
      <div style="font-size:13px;color:var(--color-text-secondary);margin-top:2px">{profile["title"]}</div>
      <div style="margin-top:10px;font-size:13px;color:var(--color-text-primary);line-height:1.7">{profile["desc"]}</div>
    </div>
    <div style="display:flex;flex-direction:column;gap:8px;min-width:160px">
      <div style="font-size:12px;color:var(--color-text-secondary)">מנהל</div>
      <div style="font-size:14px;font-weight:500;color:var(--color-text-primary)">{profile["manager"]}</div>
      <div style="font-size:12px;color:var(--color-text-secondary);margin-top:4px">סגנון</div>
      <div style="font-size:13px;color:var(--color-text-primary)">{profile["style"]}</div>
      <div style="font-size:12px;color:var(--color-text-secondary);margin-top:4px">נכסים מנוהלים</div>
      <div style="font-size:13px;font-weight:500;color:var(--color-text-info)">{profile["aum"]}</div>
      <div style="font-size:12px;color:var(--color-text-secondary);margin-top:4px">נוסדה</div>
      <div style="font-size:13px;color:var(--color-text-primary)">{profile["founded"]}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 אחזקות", "📡 RSI + מחיר", "🔄 שינויים", "📰 חדשות"])

    def render_last_deal(changes, name):
        if changes.get("error"):
            return
        candidates = []
        for h in changes.get("new", []):
            candidates.append({**h, "action": "קנייה חדשה", "color": "#1a7a1a", "icon": "🟢"})
        for h in changes.get("sold", []):
            candidates.append({**h, "action": "מכירה מלאה", "color": "#c0392b", "icon": "🔴"})
        for h in changes.get("increased", []):
            candidates.append({**h, "action": f"הגדלה +{h['pct_change']}%", "color": "#1565c0", "icon": "📈"})
        for h in changes.get("decreased", []):
            candidates.append({**h, "action": f"קיצוץ {h['pct_change']}%", "color": "#e65100", "icon": "📉"})
        if not candidates:
            return
        deal = max(candidates, key=lambda x: x["value_thousands"])
        val = deal["value_thousands"] / 1000
        old_val = deal.get("old_value", 0) / 1000
        date_range = f"{changes.get('previous_date','?')} → {changes.get('latest_date','?')}"
        st.divider()
        st.markdown(f"""
<div style="border:1.5px solid {deal['color']}44;border-radius:12px;padding:18px 22px;background:{deal['color']}08">
  <div style="font-size:11px;color:#888;margin-bottom:6px">העסקה האחרונה — {name} | {date_range}</div>
  <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
    <span style="font-size:28px">{deal['icon']}</span>
    <div>
      <div style="font-size:16px;font-weight:700;color:{deal['color']}">{deal['action']}</div>
      <div style="font-size:20px;font-weight:600;color:#1a1a2e">{deal['name']}</div>
    </div>
    <div style="margin-left:auto;text-align:right">
      <div style="font-size:12px;color:#888">שווי נוכחי</div>
      <div style="font-size:20px;font-weight:600;color:{deal['color']}">${val:,.0f}M</div>
      {"<div style='font-size:12px;color:#888'>לעומת $" + f"{old_val:,.0f}M" + " קודם</div>" if old_val else ""}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    with tab1:
        with st.spinner("שולף אחזקות..."):
            holdings = get_holdings_from_filing(selected_inst, latest["accession"])
        if not holdings:
            st.warning("לא ניתן לשלוף פירוט אחזקות.")
            st.stop()
        total_val = sum(h["value_thousands"] for h in holdings) / 1000
        st.metric("שווי תיק כולל", f"${total_val:,.0f}M")
        df = pd.DataFrame(holdings[:top_n])
        df["value_m"] = (df["value_thousands"] / 1000).round(1)
        df["pct"] = (df["value_thousands"] / sum(h["value_thousands"] for h in holdings) * 100).round(2)
        df["shares_fmt"] = df["shares"].apply(lambda x: f"{x:,}" if x > 0 else "—")
        df_d = df[["name","value_m","pct","shares_fmt","cusip"]].copy()
        df_d.columns = ["שם מניה","שווי ($M)","% מהתיק","מניות","CUSIP"]
        df_d.index = range(1, len(df_d)+1)
        st.subheader(f"Top {top_n} אחזקות")
        st.dataframe(df_d, use_container_width=True, height=420)
        st.bar_chart(df.set_index("name")[["value_m"]].head(10))
        with st.spinner("טוען עסקה אחרונה..."):
            ch = get_portfolio_changes(selected_inst)
        render_last_deal(ch, inst_name)


    with tab2:
        with st.spinner("שולף מחירים ו-RSI (עד 20 שניות)..."):
            enriched = enrich_holdings(holdings[:15])
        st.subheader("RSI ומחיר נוכחי")
        oversold   = [h for h in enriched if h.get("signal") == "OVERSOLD"]
        overbought = [h for h in enriched if h.get("signal") == "OVERBOUGHT"]
        if oversold:
            st.success(f"OVERSOLD — {len(oversold)} מניות מתחת ל-RSI 30 — הזדמנות קנייה פוטנציאלית")
        if overbought:
            st.warning(f"OVERBOUGHT — {len(overbought)} מניות מעל RSI 70 — שקול זהירות")
        import pandas as pd
        rows = []
        for h in enriched:
            rows.append({
                "מניה": h["name"],
                "סימבול": h.get("symbol","—"),
                "מחיר": f"${h.get('price',0):,.2f}" if h.get("price") else "—",
                "שינוי %": f"{h.get('change_pct',0):+.2f}%" if h.get("change_pct") else "—",
                "RSI": h.get("rsi",0) or "—",
                "סיגנל": h.get("signal","—"),
                "שווי ($M)": round(h["value_thousands"]/1000,1),
            })
        df_rsi = pd.DataFrame(rows)
        df_rsi.index = range(1, len(df_rsi)+1)
        def csig(v):
            if v == "OVERSOLD": return "color:#1a7a1a;font-weight:bold"
            if v == "OVERBOUGHT": return "color:#c0392b;font-weight:bold"
            return ""
        st.dataframe(df_rsi.style.map(csig, subset=["סיגנל"]), use_container_width=True, height=460)
        st.caption("מקור: Twelve Data API | RSI: 14 ימים")

    with tab3:
        with st.spinner("משווה דיווחים..."):
            changes = get_portfolio_changes(selected_inst)
        if changes.get("error"):
            st.warning(changes["error"])
        else:
            st.caption(f"השוואה: {changes['previous_date']} → {changes['latest_date']}")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🟢 פוזיציות חדשות")
                for h in changes["new"]: st.markdown(f"<span class='change-new'>+ {h['name']}</span> — ${h['value_thousands']/1000:,.0f}M", unsafe_allow_html=True)
                if not changes["new"]: st.caption("אין")
                st.markdown("#### 📈 הגדלות")
                for h in changes["increased"]: st.markdown(f"<span class='change-up'>▲ {h['name']}</span> +{h['pct_change']}% | ${h['value_thousands']/1000:,.0f}M", unsafe_allow_html=True)
                if not changes["increased"]: st.caption("אין")
            with c2:
                st.markdown("#### 🔴 פוזיציות שנסגרו")
                for h in changes["sold"]: st.markdown(f"<span class='change-sold'>− {h['name']}</span> — ${h['value_thousands']/1000:,.0f}M", unsafe_allow_html=True)
                if not changes["sold"]: st.caption("אין")
                st.markdown("#### 📉 קיצוצים")
                for h in changes["decreased"]: st.markdown(f"<span class='change-down'>▼ {h['name']}</span> {h['pct_change']}% | ${h['value_thousands']/1000:,.0f}M", unsafe_allow_html=True)
                if not changes["decreased"]: st.caption("אין")
            render_last_deal(changes, inst_name)

    with tab4:
        with st.spinner("שולף חדשות..."):
            news = fetch_news(selected_inst, max_results=5)
        if not news:
            st.warning("לא נמצאו חדשות.")
        else:
            for item in news:
                st.markdown(f"""
<div class="news-card">
  <div class="news-title">{item['title']}</div>
  <div class="news-meta">{item['date']}</div>
  <div class="news-summary">{item['summary']}</div>
  <a href="{item['link']}" target="_blank" style="font-size:12px;color:#1565c0;">קרא עוד ↗</a>
</div>""", unsafe_allow_html=True)
        with st.spinner("טוען עסקה אחרונה..."):
            ch3 = get_portfolio_changes(selected_inst)
        render_last_deal(ch3, inst_name)
        st.divider()
        st.caption("מקור: Google News RSS | SEC EDGAR")
