import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl

try:
    from src.insider_tracker import (
        fetch_biggest_insider_buys, search_insider_by_ticker,
        fetch_form4_details, get_insider_signal,
        TRANSACTION_CODES
    )
    INSIDER_OK = True
except ImportError:
    INSIDER_OK = False

inject_rtl()

st.title("🚨 פקודות מוסדיות — Insider & Smart Money")
st.caption("Form 4 SEC EDGAR | עדכון: תוך 48 שעות מהפקודה | חינמי לחלוטין")

st.info("""
**למה זה הסיגנל הכי חזק בשוק?**

כשמנכ"ל קונה מניות של החברה שלו — הוא לא מנחש. הוא יודע.
הוא רואה את ההכנסות לפני כולם, את החוזים החדשים, את הטכנולוגיה הבאה.
SEC מחייב דיווח תוך 48 שעות — ואנחנו שולפים אותו ישירות.
""")

st.divider()

tab1, tab2, tab3 = st.tabs([
    "🔥 הפקודות הגדולות ביותר",
    "🔍 חיפוש לפי מניה",
    "📚 מדריך קריאת הסיגנלים"
])

# ── TAB 1: Biggest insider buys ───────────────────────────
with tab1:
    col_days, col_run = st.columns([2, 1])
    with col_days:
        days = st.select_slider("טווח ימים", options=[1, 2, 3, 5, 7], value=3)
    with col_run:
        run = st.button("🔍 שלוף פקודות", type="primary")

    if run:
        with st.spinner(f"שולף פקודות מוסדיות מ-{days} הימים האחרונים..."):
            trades = fetch_biggest_insider_buys(days_back=days) if INSIDER_OK else []

        if not trades:
            st.warning("לא נמצאו פקודות גדולות בטווח זה, או ה-API לא זמין.")
            st.info("SEC מעדכן פקודות בימי עסקים בלבד. נסה טווח של 5-7 ימים.")
        else:
            total_vol = sum(t["total_usd"] for t in trades)
            c1, c2, c3 = st.columns(3)
            c1.metric("פקודות נמצאו", len(trades))
            c2.metric("סה\"כ ווליום", f"${total_vol/1e6:.1f}M")
            c3.metric("הגדולה", f"${trades[0]['total_usd']/1e6:.1f}M" if trades else "—")

            st.divider()
            st.subheader("🔥 הפקודות הגדולות ביותר — כסף חכם נכנס")

            for t in trades:
                total_m = t["total_usd"] / 1_000_000
                border_color = "#c0392b" if total_m > 1 else "#e67e22" if total_m > 0.2 else "#2980b9"
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 1])
                    with c1:
                        ticker = t.get("ticker", "")
                        st.markdown(f"### {'$'+ticker if ticker else ''} {t['issuer']}")
                        st.caption(f"👤 {t['owner']} — **{t['role_he']}**")
                        st.caption(f"📅 תאריך עסקה: {t['date']} | דווח: {t['file_date']}")
                    with c2:
                        st.metric("סכום", f"${total_m:,.2f}M")
                        st.metric("מחיר", f"${t['price']:,.2f}" if t['price'] else "—")
                    with c3:
                        st.metric("מניות", f"{t['shares']:,.0f}")
                        st.markdown(f"<div style='color:{border_color};font-size:20px;font-weight:700'>🟢 BUY</div>",
                                    unsafe_allow_html=True)

            st.divider()
            # Summary table
            rows = [{
                "חברה": t["issuer"],
                "סימבול": t.get("ticker", "—"),
                "מנהל": t["owner"],
                "תפקיד": t["role_he"],
                "סכום ($M)": round(t["total_usd"]/1e6, 2),
                "מחיר": f"${t['price']:,.2f}" if t["price"] else "—",
                "מניות": f"{t['shares']:,.0f}",
                "תאריך": t["date"],
            } for t in trades]
            df = pd.DataFrame(rows)
            df.index = range(1, len(df)+1)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("לחץ 'שלוף פקודות' כדי לראות את הפקודות הגדולות ביותר של הימים האחרונים")

# ── TAB 2: Search by ticker ───────────────────────────────
with tab2:
    st.subheader("🔍 חפש פקודות מוסדיות לפי מניה ספציפית")
    col_t, col_d, col_s = st.columns([2, 1, 1])
    with col_t:
        ticker_input = st.text_input("סימבול מניה", placeholder="AAPL, NVDA, TSLA...").upper()
    with col_d:
        search_days = st.selectbox("טווח", [7, 14, 30, 60], index=1)
    with col_s:
        search_btn = st.button("🔍 חפש", type="primary")

    if search_btn and ticker_input:
        with st.spinner(f"מחפש פקודות insider עבור {ticker_input}..."):
            signal = get_insider_signal(ticker_input, days_back=search_days) if INSIDER_OK else {}
            filings = search_insider_by_ticker(ticker_input, days_back=search_days) if INSIDER_OK else []

        if signal:
            color = signal["color"]
            st.markdown(f"""
<div style="border:2px solid {color};border-radius:12px;padding:16px;background:{color}11;margin:10px 0">
  <div style="font-size:22px;font-weight:700;color:{color}">{signal['signal']}</div>
  <div style="margin-top:8px;display:flex;gap:20px;flex-wrap:wrap">
    <div><strong>קניות:</strong> {signal['buys']} | <strong>מכירות:</strong> {signal['sells']}</div>
    <div><strong>סה"כ קנה:</strong> ${signal['total_buy_usd']/1e6:.2f}M</div>
    <div><strong>דיווחים:</strong> {signal['filings_count']} ב-{signal['days_back']} ימים</div>
  </div>
  {'<div style="margin-top:8px"><strong>קונים:</strong> ' + ' | '.join(signal['buyers']) + '</div>' if signal['buyers'] else ''}
</div>
""", unsafe_allow_html=True)

        if filings:
            st.subheader(f"דיווחי Form 4 עבור {ticker_input}")
            rows = [{
                "חברה": f["entity"],
                "תאריך דיווח": f["file_date"],
                "תקופה": f["period"],
                "מדווחים": ", ".join(f["display_names"][:2]) if f["display_names"] else "—",
            } for f in filings[:15]]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info(f"לא נמצאו דיווחים עבור {ticker_input} ב-{search_days} הימים האחרונים")

# ── TAB 3: Guide ─────────────────────────────────────────
with tab3:
    st.subheader("📚 מדריך — איך לקרוא פקודות מוסדיות")

    st.markdown("### 🟢 אות קנייה — מה לחפש")
    signals_buy = [
        ("מנכ\"ל קנה +$1M", "הכי חזק. הוא יודע מה צפוי.", "חזק מאוד"),
        ("כמה מנהלים קנו יחד", "תיאום פנימי — משהו עומד לקרות", "חזק"),
        ("קנייה לאחר ירידה חדה", "הם רואים את המניה זולה", "חזק"),
        ("קנייה חוזרת ב-3 רבעונים", "אמונה לטווח ארוך", "בינוני-חזק"),
    ]
    for sig, explain, strength in signals_buy:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 3, 1])
            c1.markdown(f"**{sig}**")
            c2.caption(explain)
            c3.success(strength)

    st.markdown("### 🔴 אות מכירה — לא תמיד שלילי")
    signals_sell = [
        ("מנהל מכר — כמות קטנה", "לרוב גיוון תיק / מס. לא סיגנל שלילי.", "לא משמעותי"),
        ("מנהל מכר 50%+ אחזקה", "שווה לשים לב — ייתכן חשש", "שים לב"),
        ("כמה מנהלים מוכרים יחד", "סיגנל שלילי — ייתכן בעיות צפויות", "שלילי"),
        ("מכירה לאחר עלייה חדה", "מימוש רווחים — נורמלי", "נייטרלי"),
    ]
    for sig, explain, strength in signals_sell:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 3, 1])
            c1.markdown(f"**{sig}**")
            c2.caption(explain)
            c3.warning(strength)

    st.divider()
    st.markdown("### קודי עסקה — Form 4")
    codes_rows = [{"קוד": k, "משמעות": v[0], "כיוון": v[2]}
                  for k, v in TRANSACTION_CODES.items()]
    st.dataframe(pd.DataFrame(codes_rows), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 📌 כלל הזהב")
    st.success("""
**מנהלים מוכרים מסיבות רבות — אבל קונים מסיבה אחת בלבד:**
הם חושבים שהמניה תעלה.

Peter Lynch, מנהל קרן Magellan שהניב 29% שנתי:
*"Insiders might sell their shares for any number of reasons,
but they buy them for only one: they think the price will rise."*
""")

    st.caption("מקור נתונים: SEC EDGAR Form 4 | עדכון: כל 48 שעות | חינמי לחלוטין")
