# 🌐 PBK Stock — פריסה לענן (גישה מכל מקום)

---

## שלב 1 — GitHub

### 1.1 פתח חשבון
כנס ל: **https://github.com** → Sign Up (חינמי)

### 1.2 צור Repository חדש
1. לחץ **New repository**
2. שם: `pbk-stock-alerts`
3. **Private** (חשוב! לא Public)
4. לחץ **Create repository**

### 1.3 העלה את הקבצים
לאחר יצירת ה-repo, לחץ **uploading an existing file**:

העלה את כל הקבצים מהתיקייה `PBK_CLOUD` **חוץ מ:**
- ❌ `.streamlit/secrets.toml` — לא להעלות!
- ❌ `monitor_state.json`
- ❌ קבצי `.bat`

**✅ להעלות:**
- `dashboard.py`
- `dashboard_main.py`
- `requirements.txt`
- תיקיית `src/` כולה
- תיקיית `pages/` כולה
- `.streamlit/config.toml` (בלבד — לא secrets.toml)

---

## שלב 2 — Streamlit Cloud

### 2.1 פתח חשבון
כנס ל: **https://streamlit.io/cloud** → Sign up with GitHub

### 2.2 צור App חדש
1. לחץ **New app**
2. בחר את ה-repo: `pbk-stock-alerts`
3. Branch: `main`
4. Main file path: `dashboard.py`
5. לחץ **Deploy**

### 2.3 הוסף Secrets (המפתחות הסודיים)
בדף ה-App → לחץ **Settings** → **Secrets**

הכנס בדיוק את הטקסט הבא:

```toml
[api_keys]
twelve_data = "93d58590918649668bac71e85545bd56"
finnhub     = "d8fhgipr01qn443a08v0d8fhgipr01qn443a08vg"

[telegram]
bot_token = "8905269757:AAFPL0GYJ_NMyHIG2Qr9WqxWAQ6dPTWTY3A"
chat_ids  = ["328769387", "970308662"]
```

לחץ **Save** → **Reboot app**

---

## שלב 3 — קבל את ה-URL שלך

לאחר הפריסה תקבל כתובת כזו:
```
https://pbk-stock-alerts-XXXXX.streamlit.app
```

**זו הכתובת הקבועה שלך** — גלויה רק למי שיש לו אותה.

---

## הגדרת סיסמה (אופציונלי אך מומלץ)

ב-Secrets הוסף:
```toml
[auth]
password = "הסיסמה שלך"
```

---

## סיכום

| מה | איפה |
|----|------|
| קוד (ללא סודות) | GitHub Private Repo |
| מפתחות API | Streamlit Secrets (מוצפן) |
| האתר | streamlit.app URL |
| גישה | כל מכשיר, כל מקום |
| עלות | חינם |
