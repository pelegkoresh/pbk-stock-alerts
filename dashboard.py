import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

pg = st.navigation([
    st.Page("dashboard_main.py",             title="🐋 Whale Tracker",          icon="🐋", default=True),
    st.Page("pages/p1_world.py",             title="🌍 סחורות עולמיות",          icon="🌍"),
    st.Page("pages/p2_seasonal.py",          title="📈 מסחר עונתי",              icon="📈"),
    st.Page("pages/p6_live_commodities.py",  title="🔥 סחורות חיות Top 50",      icon="🔥"),
    st.Page("pages/p3_live.py",              title="📡 סחורות חי",               icon="📡"),
    st.Page("pages/p7_crypto.py",            title="🪙 קריפטו",                  icon="🪙"),
    st.Page("pages/p8_forex.py",             title="💱 Forex",                   icon="💱"),
    st.Page("pages/p4_recurring.py",         title="🔁 פעולות חוזרות",            icon="🔁"),
    st.Page("pages/p5_hot.py",               title="🎯 ציון סחורות",             icon="🎯"),
    st.Page("pages/p9_analysis.py",          title="💡 ניתוח השקעה",             icon="💡"),
    st.Page("pages/p10_insider.py",          title="🚨 פקודות מוסדיות",           icon="🚨"),
    st.Page("pages/p11_signals.py",          title="🌡️ סיגנלים גלובליים",        icon="🌡"),
    st.Page("pages/p12_tesla.py",            title="🚀 Tesla & SpaceX",          icon="🚀"),
])
pg.run()
