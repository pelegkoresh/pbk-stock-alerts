import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl
from src.tesla_monitor import (
    get_tesla_price, get_volume_spike,
    get_tesla_insider_activity, get_tesla_material_events,
    check_spacex_s1, send_telegram, build_alert_message,
    TELEGRAM_BOT_TOKEN
)

inject_rtl()

TELEGRAM_CONFIGURED = "ENTER" not in TELEGRAM_BOT_TOKEN

st.title("🚀 Tesla & SpaceX — סוכן מעקב")
st.caption("SEC EDGAR real-time | Volume Spikes | Insider Activity | Telegram Alerts")

# ── Telegram status bar ───────────────────────────────────
if TELEGRAM_CONFIGURED:
    st.success("✅ Telegram מחובר — תקבל התראות אוטומטיות")
else:
    st.warning("⚠️ Telegram לא מוגדר — הגדר Bot Token בקובץ `src/tesla_monitor.py` לקבלת התראות")

# ── Auto-refresh ──────────────────────────────────────────
col_ref, col_auto, col_int = st.columns([1, 2, 1])
with col_ref:
    if st.button("🔄 רענן עכשיו"):
        st.cache_data.clear()
        st.rerun()
with col_auto:
    auto_refresh = st.toggle("רענון אוטומטי כל 5 דקות", value=False)
with col_int:
    st.caption(f"עדכון: {datetime.now().strftime('%H:%M:%S')}")

if auto_refresh:
    time.sleep(300)
    st.rerun()

# ── Cached loaders ────────────────────────────────────────
@st.cache_data(ttl=60,   show_spinner=False)
def load_tsla_price():   return get_tesla_price()

@st.cache_data(ttl=60,   show_spinner=False)
def load_volume():       return get_volume_spike()

@st.cache_data(ttl=300,  show_spinner=False)
def load_insider(days):  return get_tesla_insider_activity(days)

@st.cache_data(ttl=300,  show_spinner=False)
def load_8k(days):       return get_tesla_material_events(days)

@st.cache_data(ttl=300,  show_spinner=False)
def load_spacex():       return check_spacex_s1()

st.divider()

# ══════════════════════════════════════════════════════════
# SECTION 1: LIVE METRICS
# ══════════════════════════════════════════════════════════
st.subheader("📊 מדדים חיים — $TSLA")

with st.spinner("שולף מחיר ונתוני ווליום..."):
    price_data = load_tsla_price()
    vol_data   = load_volume()

if price_data:
    pct = price_data.get("change_pct", 0)
    vol = price_data.get("volume", 0)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("מחיר $TSLA", f"${price_data.get('price', 0):,.2f}",
              delta=f"{'+' if pct>0 else ''}{pct:.2f}%")
    c2.metric("פתיחה", f"${price_data.get('open', 0):,.2f}")
    c3.metric("גבוה", f"${price_data.get('high', 0):,.2f}")
    c4.metric("נמוך",  f"${price_data.get('low', 0):,.2f}")
    c5.metric("ווליום", f"{vol:,}" if vol else "—")

if vol_data:
    spike_color = "#c0392b" if vol_data.get("is_spike") else "#27ae60"
    st.markdown(f"""
<div style="padding:12px;border-radius:8px;background:{spike_color}18;border:1px solid {spike_color};margin:8px 0">
  <strong style="color:{spike_color}">{vol_data.get('signal','')}</strong> |
  ווליום היום: <strong>{vol_data.get('today_volume',0):,}</strong> |
  ממוצע 20 ימים: {vol_data.get('avg20_volume',0):,} |
  <strong>{vol_data.get('spike_label','')}</strong>
</div>
""", unsafe_allow_html=True)

    # Auto-alert volume spike
    if vol_data.get("is_spike") and TELEGRAM_CONFIGURED:
        alert_data = {**vol_data, "price": price_data.get("price", 0)}
        msg = build_alert_message("VOLUME_SPIKE", alert_data)
        if send_telegram(msg):
            st.success("📱 התראת Telegram נשלחה — Volume Spike זוהה!")

st.divider()

# ══════════════════════════════════════════════════════════
# SECTION 2: SPACEX S-1 STATUS
# ══════════════════════════════════════════════════════════
st.subheader("🚀 SpaceX — סטטוס S-1 ו-IPO")

with st.spinner("בודק סטטוס SpaceX S-1..."):
    spacex = load_spacex()

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**{spacex.get('company', 'SpaceX')}**")
    c1.caption(f"CIK: {spacex.get('cik', '')}")
    c2.markdown(f"**{spacex.get('status', '—')}**")
    c3.metric("הגשות S-1", spacex.get("s1_count", 0))

    latest = spacex.get("latest_filing", {})
    if latest:
        st.markdown(f"**הגשה אחרונה:** {latest.get('form','')} | תאריך: {latest.get('date','')} | [פתח ב-SEC EDGAR]({latest.get('url','')})")

        if spacex.get("has_pricing"):
            st.success("✅ נמצאו עדכוני S-1/A — ייתכן עדכון תמחור!")
            if TELEGRAM_CONFIGURED:
                msg = build_alert_message("SPACEX_S1", spacex)
                send_telegram(msg)
        else:
            st.info("📋 S-1 מוגש — עדיין ממתין לתמחור סופי (מחיר טווח טרם פורסם)")

    if spacex.get("all_s1"):
        with st.expander("כל הגשות S-1"):
            df_s1 = pd.DataFrame([{
                "סוג": f["form"],
                "תאריך": f["date"],
                "Accession": f["accession"],
            } for f in spacex["all_s1"]])
            st.dataframe(df_s1, use_container_width=True, hide_index=True)

    st.caption(f"🔗 [מעקב ישיר ב-SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001181412&type=S-1&dateb=&owner=include&count=10)")

st.divider()

# ══════════════════════════════════════════════════════════
# SECTION 3: TESLA SEC FILINGS
# ══════════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["👤 Form 4 — Insider Activity", "📢 8-K — Material Events"])

with tab1:
    days_f4 = st.select_slider("טווח ימים — Form 4", options=[3, 7, 14, 30], value=14, key="f4_days")

    with st.spinner(f"שולף Form 4 עבור Tesla ({days_f4} ימים)..."):
        insider_filings = load_insider(days_f4)

    if not insider_filings:
        st.info(f"לא נמצאו דיווחי Form 4 ל-{days_f4} הימים האחרונים")
        st.caption("[חפש ישירות ב-SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001318605&type=4)")
    else:
        st.success(f"נמצאו {len(insider_filings)} דיווחים")
        for f in insider_filings:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{f['company']} — {f['form']}**")
                    st.caption(f"Accession: {f['accession']}")
                with c2:
                    st.caption(f"📅 {f['date']}")
                with c3:
                    st.markdown(f"[פתח]({f['edgar_url']})")

                if TELEGRAM_CONFIGURED:
                    if st.button(f"📱 שלח התראה", key=f"alert_{f['accession']}"):
                        msg = build_alert_message("SEC_FILING", f)
                        if send_telegram(msg):
                            st.success("נשלח!")

with tab2:
    days_8k = st.select_slider("טווח ימים — 8-K", options=[7, 14, 30, 60], value=30, key="8k_days")

    with st.spinner(f"שולף 8-K עבור Tesla ({days_8k} ימים)..."):
        events_8k = load_8k(days_8k)

    if not events_8k:
        st.info(f"לא נמצאו אירועים מהותיים (8-K) ב-{days_8k} הימים האחרונים")
        st.caption("[חפש ישירות ב-SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001318605&type=8-K)")
    else:
        st.warning(f"⚠️ נמצאו {len(events_8k)} אירועים מהותיים — בדוק!")
        for f in events_8k:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{f['form']}** — {f['company']}")
                c1.caption(f"Accession: {f['accession']}")
                c2.caption(f"📅 {f['date']}")
                c3.markdown(f"[פתח]({f['edgar_url']})")

st.divider()

# ══════════════════════════════════════════════════════════
# SECTION 4: TELEGRAM SETUP
# ══════════════════════════════════════════════════════════
st.subheader("📱 הגדרת התראות Telegram")

if not TELEGRAM_CONFIGURED:
    with st.container(border=True):
        st.markdown("#### 3 צעדים להתראות אוטומטיות")
        st.markdown("""
**צעד 1 — צור Bot:**
1. פתח Telegram וחפש **@BotFather**
2. שלח `/newbot`
3. תן שם לbot (למשל: `MyStockAlerts`)
4. קבל **Bot Token** (נראה כך: `123456789:ABCdef...`)

**צעד 2 — קבל את ה-Chat ID שלך:**
1. שלח הודעה ל-bot שיצרת
2. פתח בדפדפן: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. מצא את `"chat":{"id":...}` — זה ה-Chat ID שלך

**צעד 3 — הכנס לקובץ:**
""")
        st.code("""# בקובץ C:\\StockApp\\src\\tesla_monitor.py
TELEGRAM_BOT_TOKEN = "123456789:ABCdef..."
TELEGRAM_CHAT_ID   = "987654321"  """)

        st.markdown("**בדיקה — שלח הודעת test:**")
        if st.button("📤 שלח הודעת Test", type="primary"):
            from src.tesla_monitor import send_telegram
            ok = send_telegram("🧪 <b>Test מוצלח!</b>\nהמערכת מחוברת לחשבון שלך ✅")
            if ok:
                st.success("✅ הודעה נשלחה בהצלחה ל-Telegram!")
            else:
                st.error("❌ שגיאה — בדוק שה-Token וה-Chat ID נכונים")
else:
    st.success("✅ Telegram מחובר ופעיל")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 שלח Test"):
            ok = send_telegram("🧪 <b>Test מוצלח!</b>\nהמערכת פעילה ✅")
            st.success("נשלח!") if ok else st.error("שגיאה")
    with col2:
        if st.button("🚀 שלח סיכום Tesla עכשיו"):
            p = load_tsla_price()
            v = load_volume()
            s = load_spacex()
            msg = (
                f"📊 <b>Tesla & SpaceX — סיכום</b>\n\n"
                f"$TSLA: ${p.get('price',0):,.2f} ({p.get('change_pct',0):+.2f}%)\n"
                f"ווליום: {v.get('spike_label','')}\n\n"
                f"🚀 SpaceX: {s.get('status','')}\n"
                f"⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}"
            )
            ok = send_telegram(msg)
            st.success("נשלח!") if ok else st.error("שגיאה")

st.caption("מקורות: SEC EDGAR | Twelve Data | Yahoo Finance | Telegram Bot API")
