"""
secrets_loader.py
=================
טוען מפתחות API בצורה בטוחה:
- בענן: מ-Streamlit Secrets (מוצפן)
- מקומי: מהקבצים ישירות
"""
import os

def get_secret(section: str, key: str, fallback: str = "") -> str:
    """טוען מפתח — קודם מנסה Streamlit Secrets, אחר כך fallback."""
    try:
        import streamlit as st
        val = st.secrets.get(section, {}).get(key, "")
        if val:
            return val
    except Exception:
        pass
    return fallback

def get_telegram_chat_ids() -> list:
    """מחזיר רשימת Chat IDs."""
    try:
        import streamlit as st
        ids = st.secrets.get("telegram", {}).get("chat_ids", [])
        if ids:
            return [str(i) for i in ids]
    except Exception:
        pass
    return ["328769387", "970308662"]

# ── Shortcuts ─────────────────────────────────────────────
TWELVE_KEY         = get_secret("api_keys", "twelve_data",  "93d58590918649668bac71e85545bd56")
FINNHUB_KEY        = get_secret("api_keys", "finnhub",      "d8fhgipr01qn443a08v0d8fhgipr01qn443a08vg")
TELEGRAM_BOT_TOKEN = get_secret("telegram", "bot_token",    "8905269757:AAFPL0GYJ_NMyHIG2Qr9WqxWAQ6dPTWTY3A")
TELEGRAM_CHAT_IDS  = get_telegram_chat_ids()
