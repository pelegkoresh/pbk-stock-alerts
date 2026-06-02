# 📖 מדריך שימוש — PBKStockAlerts

---

## 🚀 פתיחת האתר

```powershell
cd C:\StockAppBOT\final
python -m streamlit run dashboard.py
```

הדפדפן נפתח אוטומטית על: **http://localhost:8501**

---

## 🔔 הפעלת המנטור האוטומטי

המנטור בודק כל 30 שניות ושולח התראות Telegram:

```powershell
cd C:\StockAppBOT\final
python monitor.py
```

**מה המנטור בודק:**

| מקור | תנאי להתראה |
|------|-------------|
| 📊 TSLA Volume | ווליום > פי 2 מהממוצע |
| 📈 TSLA מחיר | תנועה > 3% |
| 🚀 SpaceX S-1 | כל עדכון חדש ב-SEC |
| 👤 Form 4 | כל Insider שקנה/מכר |
| 📢 8-K | כל אירוע מהותי |

**לעצירה:** Ctrl+C

---

## 💬 שליחת הודעה ידנית דרך הבוט

```powershell
cd C:\StockAppBOT\final
python send.py
```

בחר 1 לכולם / 2 רק לעצמך → כתוב הודעה → Enter

---

## 👤 הוספת מנוי חדש לבוט

**שלב 1** — שלח לו: `https://t.me/PBKStockAlertsBot`

**שלב 2** — הוא שולח Start + הודעה כלשהי

**שלב 3** — פתח בדפדפן:
```
https://api.telegram.org/bot8905269757:AAFPL0GYJ_NMyHIG2Qr9WqxWAQ6dPTWTY3A/getUpdates
```
מצא את `"chat":{"id":XXXXXXX}` — זה ה-Chat ID שלו

**שלב 4** — פתח `src\tesla_monitor.py` והוסף לרשימה:
```python
TELEGRAM_CHAT_IDS = [
    "328769387",   # Peleg
    "970308662",   # Dolev
    "XXXXXXXXX",   # השם החדש
]
```

**שלב 5** — שלח לו הודעת ברוך הבא:
```powershell
python -c "from src.tesla_monitor import add_subscriber; add_subscriber('XXXXXXXXX')"
```

---

## 📱 הבוט בטלגרם

**לינק:** https://t.me/PBKStockAlertsBot

**Bot Token:** `8905269757:AAFPL0GYJ_NMyHIG2Qr9WqxWAQ6dPTWTY3A`

**Chat IDs:**
- Peleg: `328769387`
- Dolev: `970308662`

---

## 🗂️ מבנה הקבצים

```
C:\StockAppBOT\final\
├── dashboard.py          ← האתר הראשי
├── monitor.py            ← מנטור אוטומטי (30 שניות)
├── send.py               ← שליחת הודעה ידנית
├── monitor_state.json    ← נוצר אוטומטי — מצב המנטור
├── src\
│   ├── tesla_monitor.py  ← Telegram + SEC + TSLA
│   ├── sec_edgar.py      ← מחבר SEC EDGAR
│   ├── market_signals.py ← Fear & Greed + 13D/G
│   ├── insider_tracker.py← Form 4 tracker
│   └── ...               ← שאר המודולים
└── pages\
    ├── p12_tesla.py      ← דף Tesla & SpaceX
    └── ...               ← שאר הדפים
```

---

## ⚡ הרצה אוטומטית עם Windows

לפתיחה אוטומטית של **האתר** עם הפעלת Windows:

1. צור קובץ `start_dashboard.bat` בתיקייה:
```
@echo off
cd C:\StockAppBOT\final
python -m streamlit run dashboard.py
```

2. לחץ **Win+R** → כתוב `shell:startup` → גרור את הקובץ לתוך התיקייה

לפתיחה אוטומטית של **המנטור** עם הפעלת Windows:

1. צור קובץ `start_monitor.bat`:
```
@echo off
cd C:\StockAppBOT\final
python monitor.py
```

2. גרור גם אותו ל-`shell:startup`

---

## 🌐 מקורות המידע שהמערכת בודקת

| מקור | מה הוא נותן | עלות |
|------|------------|------|
| SEC EDGAR 13F | אחזקות מוסדיות רבעוניות | חינם |
| SEC Form 4 | Insider buying/selling | חינם |
| SEC Form 13D/G | כניסת 5%+ | חינם |
| CFTC COT | פוזיציות קרנות בסחורות | חינם |
| FINRA | Short Interest | חינם |
| CoinGecko | קריפטו Top 100 | חינם |
| Yahoo Finance | מחירים + Forex + סחורות | חינם |
| Twelve Data | RSI + מחירים מדויקים | Key קיים |
| Google News RSS | חדשות מוסדיים | חינם |
| Alternative.me | Fear & Greed Index | חינם |
| Telegram Bot API | התראות | חינם |

---

## 🆘 פתרון בעיות נפוצות

**האתר לא נפתח:**
```powershell
pip install -r requirements.txt
```

**Telegram לא עובד:**
```powershell
python -c "from src.tesla_monitor import send_telegram; print(send_telegram('test'))"
```

**המנטור קורס:**
בדוק את קובץ `monitor_state.json` — מחק אותו ונסה שוב.

---

*מקורות: SEC EDGAR | FINRA | CFTC | Twelve Data | CoinGecko | Yahoo Finance*
*המערכת לצרכי מחקר בלבד — אינה ייעוץ השקעות*
