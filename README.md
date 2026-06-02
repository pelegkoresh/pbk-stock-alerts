# PBK Stock Alerts — מערכת ניטור שוק מוסדי

---

## הפעלה מהירה

**לחץ פעמיים על:**
```
START.bat
```
המערכת תיפתח אוטומטית בדפדפן על `http://localhost:8501`

---

## מה המערכת עושה

מנטרת בזמן אמת את המקורות הגדולים בעולם ושולחת התראות ל-Telegram:

| מקור | מה היא בודקת | תדירות |
|------|-------------|--------|
| 📊 TSLA Volume | ווליום חריג (פי 2+) | כל 30 שניות |
| 📈 TSLA מחיר | תנועה מעל 3% | כל 30 שניות |
| 🚀 SpaceX S-1 | כל עדכון ב-SEC | כל 30 שניות |
| 👤 Form 4 | Insider buying/selling | כל 30 שניות |
| 📢 8-K | אירועים מהותיים | כל 30 שניות |

---

## 13 דפי המערכת

| דף | תוכן |
|----|------|
| 🐋 Whale Tracker | Top 20 מניות לפי ווליום מוסדי |
| 🌍 סחורות עולמיות | מפת ייצור + עונות |
| 📈 מסחר עונתי | הסחורה הכי חמה לכל חודש |
| 🔥 סחורות חיות Top 50 | מחיר + ווליום + % שינוי |
| 📡 סחורות חי | סיגנל עונתי + מחיר חי |
| 🪙 קריפטו | CoinGecko Top 50 + מוסדיים |
| 💱 Forex | 18 זוגות + פוזיציות מוסדיות |
| 🔁 פעולות חוזרות | מוסד שקונה אותו דבר כל שנה |
| 🎯 ציון סחורות | דירוג 0-100 מולטי-קריטריון |
| 💡 ניתוח השקעה | 7 סיגנלים + המלצה קנה/מכור |
| 🚨 פקודות מוסדיות | Form 4 Insider + 13D/G |
| 🌡️ סיגנלים גלובליים | Fear & Greed + Short Interest |
| 🚀 Tesla & SpaceX | מעקב ייעודי + Telegram |

---

## מקורות מידע

| מקור | מה נותן | עלות |
|------|---------|------|
| SEC EDGAR | 13F, Form 4, 8-K, S-1 | חינם |
| CFTC | פוזיציות קרנות בסחורות | חינם |
| FINRA | Short Interest | חינם |
| Yahoo Finance | מחירים, Forex, סחורות | חינם |
| CoinGecko | קריפטו Top 100 | חינם |
| Alternative.me | Fear & Greed Index | חינם |
| Google News RSS | חדשות מוסדיים | חינם |
| Twelve Data | RSI + מחירים מדויקים | Key מוגדר |
| Finnhub | Sentiment + Earnings | Key מוגדר |
| Telegram Bot | התראות אוטומטיות | חינם |

---

## Telegram Bot

**Bot:** @PBKStockAlertsBot
**לינק:** https://t.me/PBKStockAlertsBot

**מנויים:**
- Peleg Koresh: 328769387
- Dolev Koresh: 970308662

**הוספת מנוי חדש:**
1. שלח לו: https://t.me/PBKStockAlertsBot
2. הוא שולח Start
3. פתח: https://api.telegram.org/bot8905269757:AAFPL0GYJ_NMyHIG2Qr9WqxWAQ6dPTWTY3A/getUpdates
4. מצא Chat ID שלו
5. פתח `src\tesla_monitor.py` → הוסף ל-TELEGRAM_CHAT_IDS

---

## API Keys

| שירות | Key |
|-------|-----|
| Twelve Data | 93d58590918649668bac71e85545bd56 |
| Finnhub | d8fhgipr01qn443a08v0d8fhgipr01qn443a08vg |
| Telegram Bot | 8905269757:AAFPL0GYJ_NMyHIG2Qr9WqxWAQ6dPTWTY3A |

---

## קבצי ההפעלה

| קובץ | פעולה |
|------|-------|
| `START.bat` | פותח האתר + המנטור |
| `STOP.bat` | עוצר הכל |
| `SEND_MESSAGE.bat` | שולח הודעה ידנית ל-Telegram |
| `monitor.py` | מנטור רקע (כל 30 שניות) |
| `send.py` | שליחת הודעה מ-PowerShell |

---

## פתרון בעיות

**האתר לא נפתח:**
```
pip install -r requirements.txt
python -m streamlit run dashboard.py
```

**Telegram לא עובד:**
```
python -c "from src.tesla_monitor import send_telegram; print(send_telegram('test'))"
```

**המנטור קרס — נקה מצב:**
מחק את הקובץ `monitor_state.json` והרץ שוב.

---

*PBK Stock Alerts v1.0 | מקורות: SEC EDGAR, FINRA, CFTC, Twelve Data, CoinGecko, Yahoo Finance, Finnhub*
*המערכת לצרכי מחקר בלבד — אינה ייעוץ השקעות*
