import streamlit as st
import pandas as pd
from datetime import datetime
import time
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rtl_utils import inject_rtl
from src.tesla_monitor import (
    get_tesla_price, get_volume_spike,
    get_tesla_insider_activity, get_tesla_material_events,
    check_spacex_s1, send_telegram, build_alert_message,
    TELEGRAM_BOT_TOKEN
)

try:
    from src.news_tesla import fetch_all_tesla_news
except ImportError:
    def fetch_all_tesla_news(**kw): return []

inject_rtl()

TELEGRAM_CONFIGURED = "ENTER" not in TELEGRAM_BOT_TOKEN

st.title("🚀 Tesla & SpaceX — סוכן מעקב")
st.caption(f"עדכון: {datetime.now().strftime('%H:%M:%S')} | SEC EDGAR | חדשות בזמן אמת | Telegram")

with st.container(border=True):
    col_join, col_info = st.columns([1, 3])
    with col_join:
        st.link_button("📱 הצטרף להתראות Telegram",
                       "https://t.me/PBKStockAlertsBot",
                       type="primary", use_container_width=True)
    with col_info:
        st.markdown("**קבל התראות על:** Volume Spike | SpaceX S-1 | Insider Form 4 | 8-K Events")

if TELEGRAM_CONFIGURED:
    st.success("✅ Telegram מחובר — תקבל התראות אוטומטיות")

col_ref, col_auto, col_time = st.columns([1, 2, 1])
with col_ref:
    if st.button("🔄 רענן"):
        st.cache_data.clear()
        st.rerun()
with col_auto:
    auto_refresh = st.toggle("רענון אוטומטי כל 5 דקות", value=False)
with col_time:
    st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")

if auto_refresh:
    time.sleep(300)
    st.rerun()

st.divider()

@st.cache_data(ttl=60,   show_spinner=False)
def load_price():        return get_tesla_price()
@st.cache_data(ttl=60,   show_spinner=False)
def load_volume():       return get_volume_spike()
@st.cache_data(ttl=300,  show_spinner=False)
def load_spacex():       return check_spacex_s1()
@st.cache_data(ttl=180,  show_spinner=False)
def load_news():         return fetch_all_tesla_news(limit_per_source=6)
@st.cache_data(ttl=300,  show_spinner=False)
def load_insider(days):  return get_tesla_insider_activity(days)
@st.cache_data(ttl=300,  show_spinner=False)
def load_8k(days):       return get_tesla_material_events(days)

col_data, col_news, col_signals = st.columns([1, 2, 1])

with col_data:
    st.markdown("### 📊 נתונים חיים")
    with st.spinner("..."):
        price = load_price()
        vol   = load_volume()

    if price:
        pct = price.get("change_pct", 0)
        color = "#c0392b" if pct > 0 else "#27ae60"
        st.markdown(f"""
<div style="text-align:center;padding:12px;border-radius:10px;border:2px solid {color}22;background:{color}08">
  <div style="font-size:13px;color:#888">$TSLA</div>
  <div style="font-size:28px;font-weight:900">${price.get('price',0):,.2f}</div>
  <div style="font-size:18px;font-weight:700;color:{color}">{'+' if pct>0 else ''}{pct:.2f}%</div>
  <div style="font-size:11px;color:#888;margin-top:4px">{price.get('source','')}</div>
</div>
""", unsafe_allow_html=True)

    if vol:
        spike_color = "#c0392b" if vol.get("is_spike") else "#27ae60"
        st.markdown(f"""
<div style="margin-top:8px;padding:10px;border-radius:8px;background:{spike_color}11;border:1px solid {spike_color}44;text-align:center">
  <div style="font-size:12px;font-weight:700;color:{spike_color}">{vol.get('signal','')}</div>
  <div style="font-size:11px;color:#888">ווליום: {vol.get('today_volume',0):,}</div>
  <div style="font-size:11px;color:#888">{vol.get('spike_label','')}</div>
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🚀 SpaceX S-1")
    with st.spinner("..."):
        spacex = load_spacex()

    status = spacex.get("status", "—")
    latest = spacex.get("latest_filing", {})
    s1_color = "#e67e22" if "ממתין" in status else "#27ae60"
    st.markdown(f"""
<div style="padding:10px;border-radius:8px;background:{s1_color}11;border:1px solid {s1_color}44">
  <div style="font-size:12px;font-weight:700;color:{s1_color}">{status}</div>
  {'<div style="font-size:11px;color:#888">עדכון: ' + latest.get("date","") + '</div>' if latest else ''}
  <div style="font-size:11px;margin-top:6px"><a href="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001181412&type=S-1" target="_blank">🔗 SEC EDGAR</a></div>
</div>
""", unsafe_allow_html=True)

    if spacex.get("has_pricing"):
        st.error("🚨 עדכון תמחור S-1 זוהה!")
        if TELEGRAM_CONFIGURED:
            msg = build_alert_message("SPACEX_S1", spacex)
            send_telegram(msg)

with col_news:
    st.markdown("### 📰 חדשות בזמן אמת")
    st.caption("Tesla | SpaceX | xAI | Elon Musk — ממוינות לפי חשיבות")

    with st.spinner("טוען חדשות..."):
        news = load_news()

    if not news:
        st.warning("לא ניתן לטעון חדשות כרגע")
    else:
        tags = ["הכל", "TSLA", "SPCX", "xAI", "MUSK"]
        selected_tag = st.pills("סנן לפי נושא", tags, default="הכל")
        filtered = news if selected_tag == "הכל" else [n for n in news if n["tag"] == selected_tag]

        for item in filtered[:15]:
            signal = item["signal"]
            border = "#c0392b" if "דחוף" in signal else "#f39c12" if "IPO" in signal else "#2980b9" if "Insider" in signal else "#27ae60" if "חיובי" in signal else "#e0e0e0"
            bg     = "#fff8f8" if "דחוף" in signal else "#fffdf0" if "IPO" in signal else "#f0f8ff" if "Insider" in signal else "#f9fff9" if "חיובי" in signal else "#fafafa"
            with st.container():
                st.markdown(f"""
<div style="border-left:4px solid {border};border-radius:0 8px 8px 0;padding:10px 14px;margin:6px 0;background:{bg}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <span style="font-size:11px;background:{border}22;padding:2px 6px;border-radius:10px;color:{border};font-weight:600">{signal}</span>
    <span style="font-size:10px;color:#aaa">{item['date']}</span>
  </div>
  <div style="font-size:13px;font-weight:600;margin:5px 0;color:#1a1a2e">
    <a href="{item['link']}" target="_blank" style="color:#1a1a2e;text-decoration:none">{item['title']}</a>
  </div>
  <div style="font-size:11px;color:#666">{item['desc']}</div>
  <div style="font-size:10px;color:#bbb;margin-top:4px">{item['source']}</div>
</div>
""", unsafe_allow_html=True)

with col_signals:
    st.markdown("### 🚨 סיגנלים")

    st.markdown("**👤 Form 4 Insider**")
    with st.spinner("..."):
        insiders = load_insider(14)
    if insiders:
        for f in insiders[:3]:
            st.success(f"📋 {f['form']} | {f['date'][:10]}")
    else:
        st.caption("אין פעילות insider בשבועיים")

    st.divider()
    st.markdown("**📢 8-K Events**")
    with st.spinner("..."):
        events = load_8k(30)
    if events:
        for f in events[:3]:
            st.warning(f"⚠️ {f['form']} | {f['date'][:10]}")
    else:
        st.caption("אין אירועים מהותיים ב-30 יום")

    st.divider()
    st.markdown("**🔐 כלי מנהל**")
    admin_code = st.text_input("קוד מנהל:", type="password", key="admin_code_main")

    if admin_code == "2106":
        if st.button("📤 שלח Test", use_container_width=True):
            ok = send_telegram("🧪 <b>Test!</b>\nהמערכת פעילה ✅")
            st.success("נשלח!") if ok else st.error("שגיאה")
        if st.button("🚀 סיכום Tesla", use_container_width=True):
            p = load_price()
            v = load_volume()
            s = load_spacex()
            n = load_news()
            top_news = "\n".join([f"• {item['title'][:60]}" for item in n[:3]])
            msg = (
                f"📊 <b>Tesla & SpaceX — סיכום</b>\n\n"
                f"$TSLA: ${p.get('price',0):,.2f} ({p.get('change_pct',0):+.2f}%)\n"
                f"ווליום: {v.get('spike_label','')}\n\n"
                f"🚀 SpaceX: {s.get('status','')}\n\n"
                f"📰 חדשות:\n{top_news}\n\n"
                f"⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}"
            )
            ok = send_telegram(msg)
            st.success("נשלח!") if ok else st.error("שגיאה")
    elif admin_code:
        st.error("קוד שגוי")

    st.divider()
    with st.expander("➕ הוסף מנוי"):
        new_id = st.text_input("Chat ID:", key="new_sub_id")
        new_name = st.text_input("שם:", key="new_sub_name")
        if st.button("הוסף"):
            if new_id and new_id.isdigit():
                import requests as req
                welcome = f"🎉 <b>ברוך הבא ל-PBK Stock Alerts!</b>\n\n🌐 https://pbk-stock-alerts.streamlit.app"
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                r = req.post(url, json={"chat_id": new_id, "text": welcome, "parse_mode": "HTML"}, timeout=8)
                st.success(f"✅ נשלח ל-{new_name or new_id}") if r.status_code == 200 else st.error("שגיאה")
            else:
                st.warning("Chat ID לא תקין")

st.divider()
st.caption("מקורות: SEC EDGAR | Google News RSS | Twelve Data | Yahoo Finance | אינו ייעוץ השקעות")
