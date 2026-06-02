"""
==============================================
  PBKStockAlerts — מנטור רקע אוטומטי
  בודק כל 30 שניות ושולח התראות Telegram
==============================================
הרצה: python monitor.py
עצירה: Ctrl+C
"""
import sys, time, json, os
from datetime import datetime

sys.path.insert(0, '.')
from src.tesla_monitor import (
    send_telegram, get_tesla_price, get_volume_spike,
    check_spacex_s1, get_tesla_insider_activity,
    get_tesla_material_events, build_alert_message,
    TELEGRAM_CHAT_IDS
)

# קובץ מצב — שומר מה כבר שלחנו כדי לא לחזור על עצמנו
STATE_FILE = "monitor_state.json"
CHECK_INTERVAL = 30  # שניות

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE))
        except Exception:
            pass
    return {
        "last_spacex_date": "",
        "last_insider_accessions": [],
        "last_8k_accessions": [],
        "last_volume_spike_time": "",
        "last_price": 0,
    }

def save_state(state: dict):
    json.dump(state, open(STATE_FILE, "w"), indent=2)

def log(msg: str):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")

def check_all(state: dict) -> dict:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    alerts_sent = 0

    # ── 1. Tesla Volume Spike ─────────────────────────────
    try:
        vol = get_volume_spike()
        if vol and vol.get("is_spike"):
            last_spike = state.get("last_volume_spike_time", "")
            # שלח רק אם לא שלחנו ב-30 דקות האחרונות
            if last_spike != datetime.now().strftime("%Y-%m-%d %H"):
                price = get_tesla_price()
                msg = build_alert_message("VOLUME_SPIKE", {
                    **vol, "price": price.get("price", 0)
                })
                send_telegram(msg)
                state["last_volume_spike_time"] = datetime.now().strftime("%Y-%m-%d %H")
                log(f"🚨 TSLA Volume Spike! פי {vol['spike_ratio']} — התראה נשלחה")
                alerts_sent += 1
            else:
                log(f"⚡ Volume Spike זוהה אך כבר נשלח ב-{last_spike}")
        else:
            sig = vol.get("signal", "—") if vol else "—"
            log(f"📊 TSLA Volume: {sig}")
    except Exception as e:
        log(f"❌ Volume check error: {e}")

    # ── 2. SpaceX S-1 Update ─────────────────────────────
    try:
        spacex = check_spacex_s1()
        latest = spacex.get("latest_filing", {})
        latest_date = latest.get("date", "")

        if latest_date and latest_date != state.get("last_spacex_date", ""):
            msg = build_alert_message("SPACEX_S1", spacex)
            send_telegram(msg)
            state["last_spacex_date"] = latest_date
            log(f"🚀 SpaceX עדכון חדש: {latest_date} — התראה נשלחה")
            alerts_sent += 1
        else:
            log(f"🚀 SpaceX: {spacex.get('status', '—')} (אין עדכון)")
    except Exception as e:
        log(f"❌ SpaceX check error: {e}")

    # ── 3. Tesla Form 4 — Insider ─────────────────────────
    try:
        insiders = get_tesla_insider_activity(days_back=3)
        known = state.get("last_insider_accessions", [])
        new_insiders = [f for f in insiders if f["accession"] not in known]

        if new_insiders:
            for f in new_insiders:
                msg = build_alert_message("SEC_FILING", f)
                send_telegram(msg)
                known.append(f["accession"])
                log(f"👤 Form 4 חדש: {f['company']} {f['date']} — התראה נשלחה")
                alerts_sent += 1
            state["last_insider_accessions"] = known[-50:]  # שמור 50 אחרונים
        else:
            log(f"👤 Form 4: אין חדש ב-3 ימים האחרונים")
    except Exception as e:
        log(f"❌ Insider check error: {e}")

    # ── 4. Tesla 8-K — Material Events ───────────────────
    try:
        events = get_tesla_material_events(days_back=3)
        known8k = state.get("last_8k_accessions", [])
        new_events = [f for f in events if f["accession"] not in known8k]

        if new_events:
            for f in new_events:
                msg = (
                    f"📢 <b>[TESLA 8-K — אירוע מהותי]</b>\n"
                    f"📋 סוג: <b>{f['form']}</b>\n"
                    f"📅 תאריך: {f['date']}\n"
                    f"🔗 <a href='{f['edgar_url']}'>פתח ב-SEC EDGAR</a>\n"
                    f"⏰ {now_str}"
                )
                send_telegram(msg)
                known8k.append(f["accession"])
                log(f"📢 8-K חדש: {f['date']} — התראה נשלחה")
                alerts_sent += 1
            state["last_8k_accessions"] = known8k[-50:]
        else:
            log(f"📢 8-K: אין אירועים מהותיים חדשים")
    except Exception as e:
        log(f"❌ 8-K check error: {e}")

    # ── 5. Tesla Price Change > 3% ────────────────────────
    try:
        price_data = get_tesla_price()
        pct = abs(price_data.get("change_pct", 0))
        price = price_data.get("price", 0)
        last_price = state.get("last_price", 0)

        if pct > 3 and price > 0:
            # שלח רק אם לא שלחנו על אותו מחיר
            if abs(price - last_price) > 5:
                sign = "📈" if price_data.get("change_pct", 0) > 0 else "📉"
                msg = (
                    f"{sign} <b>[TSLA תנועה גדולה]</b>\n"
                    f"💰 מחיר: ${price:,.2f}\n"
                    f"📊 שינוי: {price_data.get('change_pct', 0):+.2f}%\n"
                    f"⏰ {now_str}"
                )
                send_telegram(msg)
                state["last_price"] = price
                log(f"{sign} TSLA תנועה של {pct:.1f}% — התראה נשלחה")
                alerts_sent += 1
        else:
            log(f"💰 TSLA: ${price:,.2f} ({price_data.get('change_pct',0):+.2f}%)")
    except Exception as e:
        log(f"❌ Price check error: {e}")

    if alerts_sent == 0:
        log(f"✅ כל הבדיקות תקינות — אין עדכונים חדשים")

    return state

# ── Main loop ─────────────────────────────────────────────
def main():
    print()
    print("=" * 55)
    print("  PBKStockAlerts — מנטור רקע פעיל")
    print(f"  מנויים: {len(TELEGRAM_CHAT_IDS)}")
    print(f"  מרווח בדיקה: כל {CHECK_INTERVAL} שניות")
    print("  עצירה: Ctrl+C")
    print("=" * 55)
    print()

    # שלח הודעת פתיחה
    send_telegram(
        f"🟢 <b>מנטור הופעל</b>\n"
        f"בודק כל {CHECK_INTERVAL} שניות:\n"
        f"📊 TSLA Volume Spike\n"
        f"📈 TSLA תנועה >3%\n"
        f"🚀 SpaceX S-1 עדכונים\n"
        f"👤 Form 4 Insider\n"
        f"📢 8-K Material Events\n"
        f"⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}"
    )
    log("הודעת פתיחה נשלחה ל-Telegram")

    state = load_state()
    cycle = 0

    while True:
        try:
            cycle += 1
            print()
            log(f"━━━ מחזור #{cycle} ━━━")
            state = check_all(state)
            save_state(state)
            log(f"המתנה {CHECK_INTERVAL} שניות...")
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print()
            log("עוצר מנטור...")
            send_telegram(
                f"🔴 <b>מנטור עצר</b>\n"
                f"⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}"
            )
            print("✅ נשלחה הודעת עצירה. להתראות!")
            break
        except Exception as e:
            log(f"שגיאה כללית: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
