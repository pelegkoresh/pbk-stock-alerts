"""
==============================================
  PBKStockAlerts — שליחת הודעות ידניות
==============================================
הרצה: python send.py
"""
import sys
sys.path.insert(0, '.')
from src.tesla_monitor import send_telegram, TELEGRAM_CHAT_IDS

print("=" * 50)
print("  PBKStockAlerts — שליחת הודעה")
print(f"  מנויים: {len(TELEGRAM_CHAT_IDS)} אנשים")
print("=" * 50)
print()
print("אפשרויות:")
print("  1 — שלח לכולם")
print("  2 — שלח רק לי (Peleg)")
print("  3 — יציאה")
print()

choice = input("בחר (1/2/3): ").strip()

if choice == "3":
    print("יציאה.")
    sys.exit()

msg = input("\nכתוב את ההודעה: ").strip()
if not msg:
    print("הודעה ריקה — יציאה.")
    sys.exit()

if choice == "2":
    ok = send_telegram(msg, chat_id="328769387")
else:
    ok = send_telegram(msg)

print("\n✅ נשלח בהצלחה!" if ok else "\n❌ שגיאה — בדוק חיבור אינטרנט")
