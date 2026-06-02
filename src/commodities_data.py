COMMODITIES = {
    "crude_oil": {
        "name": "נפט גולמי",
        "emoji": "🛢️",
        "unit": "חביות/יום",
        "season_note": "מחיר עולה בחורף (ביקוש חימום) ובקיץ (נסיעות)",
        "price_seasons": [
            {"months": [12,1,2], "trend": "עולה", "reason": "ביקוש חימום גבוה"},
            {"months": [6,7,8], "trend": "עולה", "reason": "עונת נסיעות — דלק"},
            {"months": [3,4,5], "trend": "יורד", "reason": "בין עונות — ביקוש נמוך"},
            {"months": [9,10,11], "trend": "יציב", "reason": "מעבר לעונת חימום"},
        ],
        "producers": [
            {"country": "ארה\"ב", "flag": "🇺🇸", "share_pct": 20, "season_start": "כל השנה", "peak_months": "ינואר-מרץ", "notes": "שייל אויל — ייצור יציב כל השנה"},
            {"country": "סעודיה", "flag": "🇸🇦", "share_pct": 12, "season_start": "כל השנה", "peak_months": "אפריל-יוני", "notes": "OPEC — מגדילה ייצור לפני הקיץ"},
            {"country": "רוסיה", "flag": "🇷🇺", "share_pct": 11, "season_start": "כל השנה", "peak_months": "ינואר-מרץ", "notes": "ייצור עולה בחורף לצורכי חימום"},
            {"country": "קנדה", "flag": "🇨🇦", "share_pct": 6, "season_start": "כל השנה", "peak_months": "מרץ-מאי", "notes": "חולות זפת — ייצור אינטנסיבי באביב"},
            {"country": "עיראק", "flag": "🇮🇶", "share_pct": 5, "season_start": "כל השנה", "peak_months": "פברואר-אפריל", "notes": "OPEC — ייצור יציב"},
            {"country": "אחרות", "flag": "🌍", "share_pct": 46, "season_start": "משתנה", "peak_months": "משתנה", "notes": "UAE, כווית, ניגריה ועוד"},
        ],
    },
    "natural_gas": {
        "name": "גז טבעי",
        "emoji": "🔥",
        "unit": "BCF/יום",
        "season_note": "מחיר גבוה בחורף (חימום) ובקיץ (מיזוג אוויר)",
        "price_seasons": [
            {"months": [12,1,2], "trend": "עולה חד", "reason": "חימום — ביקוש שיא"},
            {"months": [6,7,8], "trend": "עולה", "reason": "מיזוג אוויר"},
            {"months": [3,4,5], "trend": "יורד", "reason": "אביב — ביקוש נמוך"},
            {"months": [9,10,11], "trend": "יורד-יציב", "reason": "מילוי מאגרים לחורף"},
        ],
        "producers": [
            {"country": "ארה\"ב", "flag": "🇺🇸", "share_pct": 24, "season_start": "כל השנה", "peak_months": "נובמבר-פברואר", "notes": "מייצא LNG — ייצור שיא בחורף"},
            {"country": "רוסיה", "flag": "🇷🇺", "share_pct": 17, "season_start": "כל השנה", "peak_months": "דצמבר-פברואר", "notes": "מספקת לאירופה — עולה בחורף"},
            {"country": "איראן", "flag": "🇮🇷", "share_pct": 7, "season_start": "כל השנה", "peak_months": "ינואר-מרץ", "notes": "ביקוש פנימי גבוה"},
            {"country": "קטר", "flag": "🇶🇦", "share_pct": 6, "season_start": "כל השנה", "peak_months": "כל השנה", "notes": "LNG — יצוא עקבי"},
            {"country": "קנדה", "flag": "🇨🇦", "share_pct": 4, "season_start": "כל השנה", "peak_months": "ינואר-מרץ", "notes": "מחוז אלברטה — חורף"},
            {"country": "אחרות", "flag": "🌍", "share_pct": 42, "season_start": "משתנה", "peak_months": "משתנה", "notes": "אוסטרליה, נורבגיה ועוד"},
        ],
    },
    "coffee": {
        "name": "קפה",
        "emoji": "☕",
        "unit": "שקים של 60 ק\"ג",
        "season_note": "מחיר עולה בספטמבר-נובמבר (לפני קציר ברזיל) ויורד לאחר הקציר",
        "price_seasons": [
            {"months": [9,10,11], "trend": "עולה", "reason": "לפני קציר ברזיל — אי-וודאות"},
            {"months": [4,5,6], "trend": "יורד", "reason": "קציר ברזיל — היצע גדול"},
            {"months": [12,1,2], "trend": "יציב", "reason": "קציר קולומביה"},
            {"months": [7,8], "trend": "משתנה", "reason": "תלוי מזג האוויר בברזיל"},
        ],
        "producers": [
            {"country": "ברזיל", "flag": "🇧🇷", "share_pct": 38, "season_start": "אפריל-מאי", "peak_months": "יוני-אוגוסט", "notes": "קציר ראשי אפריל-יוני, שנה מלאה"},
            {"country": "וייטנאם", "flag": "🇻🇳", "share_pct": 18, "season_start": "אוקטובר", "peak_months": "נובמבר-ינואר", "notes": "רובוסטה — קציר חורף"},
            {"country": "קולומביה", "flag": "🇨🇴", "share_pct": 9, "season_start": "אוקטובר", "peak_months": "נובמבר-פברואר", "notes": "ערביקה מובחר — קציר עיקרי חורף"},
            {"country": "אינדונזיה", "flag": "🇮🇩", "share_pct": 7, "season_start": "יולי", "peak_months": "יולי-ספטמבר", "notes": "סומטרה וג'אווה — קיץ"},
            {"country": "אתיופיה", "flag": "🇪🇹", "share_pct": 5, "season_start": "נובמבר", "peak_months": "נובמבר-ינואר", "notes": "קפה יוקרתי — חורף"},
            {"country": "אחרות", "flag": "🌍", "share_pct": 23, "season_start": "משתנה", "peak_months": "משתנה", "notes": "הונדורס, הודו, אוגנדה ועוד"},
        ],
    },
    "corn": {
        "name": "תירס",
        "emoji": "🌽",
        "unit": "בושלים",
        "season_note": "מחיר עולה מרץ-יוני (לפני קציר ארה\"ב) ויורד בקציר",
        "price_seasons": [
            {"months": [3,4,5,6], "trend": "עולה", "reason": "עונת זריעה — אי-וודאות יבול"},
            {"months": [9,10,11], "trend": "יורד", "reason": "קציר ארה\"ב — היצע שיא"},
            {"months": [12,1,2], "trend": "יציב", "reason": "קציר דרום אמריקה מתקרב"},
            {"months": [7,8], "trend": "תנודתי", "reason": "תלוי גשמים ומזג אוויר"},
        ],
        "producers": [
            {"country": "ארה\"ב", "flag": "🇺🇸", "share_pct": 32, "season_start": "אפריל-מאי", "peak_months": "ספטמבר-נובמבר", "notes": "Corn Belt — קציר ספטמבר"},
            {"country": "סין", "flag": "🇨🇳", "share_pct": 23, "season_start": "אפריל", "peak_months": "ספטמבר-אוקטובר", "notes": "רוב לצריכה פנימית"},
            {"country": "ברזיל", "flag": "🇧🇷", "share_pct": 10, "season_start": "ינואר", "peak_months": "מרץ-מאי", "notes": "קציר שני — סאפרינהה, מרץ-יוני"},
            {"country": "ארגנטינה", "flag": "🇦🇷", "share_pct": 5, "season_start": "פברואר", "peak_months": "מרץ-אפריל", "notes": "פמפס — קציר אביב"},
            {"country": "אוקראינה", "flag": "🇺🇦", "share_pct": 4, "season_start": "אפריל", "peak_months": "ספטמבר-אוקטובר", "notes": "לחם של אירופה"},
            {"country": "אחרות", "flag": "🌍", "share_pct": 26, "season_start": "משתנה", "peak_months": "משתנה", "notes": "מקסיקו, הודו ועוד"},
        ],
    },
    "soybeans": {
        "name": "סויה",
        "emoji": "🫘",
        "unit": "בושלים",
        "season_note": "מחיר עולה מאי-יולי (זריעה ארה\"ב) ויורד בקציר ברזיל",
        "price_seasons": [
            {"months": [5,6,7], "trend": "עולה", "reason": "עונת זריעה ארה\"ב — חשש בצורת"},
            {"months": [1,2,3], "trend": "יורד", "reason": "קציר ברזיל — היצע גדול"},
            {"months": [9,10,11], "trend": "יורד", "reason": "קציר ארה\"ב"},
            {"months": [4,8,12], "trend": "יציב", "reason": "בין עונות"},
        ],
        "producers": [
            {"country": "ברזיל", "flag": "🇧🇷", "share_pct": 37, "season_start": "ספטמבר-אוקטובר", "peak_months": "פברואר-אפריל", "notes": "יצרן #1 בעולם — קציר ינואר-מרץ"},
            {"country": "ארה\"ב", "flag": "🇺🇸", "share_pct": 31, "season_start": "מאי-יוני", "peak_months": "ספטמבר-נובמבר", "notes": "Midwest — קציר ספטמבר"},
            {"country": "ארגנטינה", "flag": "🇦🇷", "share_pct": 14, "season_start": "נובמבר", "peak_months": "מרץ-מאי", "notes": "קציר עיקרי אפריל-מאי"},
            {"country": "סין", "flag": "🇨🇳", "share_pct": 4, "season_start": "מאי", "peak_months": "ספטמבר-אוקטובר", "notes": "מייבאת הרבה יותר ממה שמייצרת"},
            {"country": "פרגוואי", "flag": "🇵🇾", "share_pct": 2, "season_start": "אוקטובר", "peak_months": "מרץ-אפריל", "notes": "קציר אביב"},
            {"country": "אחרות", "flag": "🌍", "share_pct": 12, "season_start": "משתנה", "peak_months": "משתנה", "notes": "קנדה, הודו ועוד"},
        ],
    },
}

MONTHS_HE = {
    1:"ינואר", 2:"פברואר", 3:"מרץ", 4:"אפריל",
    5:"מאי", 6:"יוני", 7:"יולי", 8:"אוגוסט",
    9:"ספטמבר", 10:"אוקטובר", 11:"נובמבר", 12:"דצמבר"
}

TREND_COLOR = {
    "עולה חד": "#c0392b",
    "עולה": "#e67e22",
    "יורד": "#27ae60",
    "יציב": "#2980b9",
    "יורד-יציב": "#1abc9c",
    "תנודתי": "#8e44ad",
    "משתנה": "#7f8c8d",
}

SEASONAL_MOVES = {
    "crude_oil": {
        "name": "נפט גולמי", "emoji": "🛢️",
        "monthly": {
            1:  {"avg_move": +4.2, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "חורף אמריקאי-אירופאי — ביקוש חימום שיא"},
            2:  {"avg_move": +2.1, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "המשך עונת חימום"},
            3:  {"avg_move": -1.5, "demand": "יורד", "supply": "עולה",   "hot": False, "reason": "סוף חורף — OPEC מגדיל ייצור"},
            4:  {"avg_move": +1.8, "demand": "בינוני","supply": "בינוני","hot": False, "reason": "התחלת עונת נסיעות"},
            5:  {"avg_move": +3.1, "demand": "עולה", "supply": "בינוני", "hot": True,  "reason": "לפני הקיץ — ביקוש דלק עולה"},
            6:  {"avg_move": +2.8, "demand": "גבוה", "supply": "גבוה",   "hot": True,  "reason": "שיא עונת נסיעות קיץ"},
            7:  {"avg_move": +1.2, "demand": "גבוה", "supply": "גבוה",   "hot": False, "reason": "אמצע קיץ — מאוזן"},
            8:  {"avg_move": -0.8, "demand": "יורד", "supply": "גבוה",   "hot": False, "reason": "סוף קיץ — ביקוש מתמתן"},
            9:  {"avg_move": -2.1, "demand": "יורד", "supply": "גבוה",   "hot": False, "reason": "אחרי הקיץ — חולשה עונתית"},
            10: {"avg_move": +1.5, "demand": "עולה", "supply": "יורד",   "hot": False, "reason": "OPEC קוצץ לפני החורף"},
            11: {"avg_move": +3.5, "demand": "עולה", "supply": "יורד",   "hot": True,  "reason": "ציפייה לחורף — קנייה מוקדמת"},
            12: {"avg_move": +4.8, "demand": "שיא",  "supply": "נמוך",   "hot": True,  "reason": "חורף + חגים — שיא שנתי"},
        }
    },
    "natural_gas": {
        "name": "גז טבעי", "emoji": "🔥",
        "monthly": {
            1:  {"avg_move": +7.5, "demand": "שיא",  "supply": "נמוך",   "hot": True,  "reason": "קור שיא — ביקוש חימום גבוה ביותר"},
            2:  {"avg_move": +4.2, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "עדיין חורף — מאגרים מתרוקנים"},
            3:  {"avg_move": -5.1, "demand": "יורד", "supply": "עולה",   "hot": False, "reason": "סוף חורף — ירידה חדה"},
            4:  {"avg_move": -3.8, "demand": "נמוך", "supply": "גבוה",   "hot": False, "reason": "אביב — חולשה עונתית"},
            5:  {"avg_move": -1.2, "demand": "נמוך", "supply": "גבוה",   "hot": False, "reason": "עדיין חלש"},
            6:  {"avg_move": +3.5, "demand": "עולה", "supply": "בינוני", "hot": True,  "reason": "מיזוג אוויר — קיץ מתחיל"},
            7:  {"avg_move": +5.2, "demand": "גבוה", "supply": "בינוני", "hot": True,  "reason": "שיא חום קיץ — ביקוש מיזוג שיא"},
            8:  {"avg_move": +3.1, "demand": "גבוה", "supply": "בינוני", "hot": True,  "reason": "קיץ חם — מאגרים נמוכים"},
            9:  {"avg_move": -1.5, "demand": "יורד", "supply": "עולה",   "hot": False, "reason": "סוף קיץ — מילוי מאגרים"},
            10: {"avg_move": +2.8, "demand": "עולה", "supply": "יורד",   "hot": False, "reason": "ציפייה לחורף"},
            11: {"avg_move": +5.8, "demand": "עולה", "supply": "יורד",   "hot": True,  "reason": "תחילת חורף — עלייה חדה"},
            12: {"avg_move": +6.5, "demand": "שיא",  "supply": "נמוך",   "hot": True,  "reason": "קור שיא — שיא שנתי שני"},
        }
    },
    "coffee": {
        "name": "קפה", "emoji": "☕",
        "monthly": {
            1:  {"avg_move": -1.8, "demand": "בינוני","supply": "גבוה",  "hot": False, "reason": "קציר קולומביה — היצע גדול"},
            2:  {"avg_move": -2.5, "demand": "בינוני","supply": "גבוה",  "hot": False, "reason": "שיא קציר דרום אמריקה"},
            3:  {"avg_move": -1.2, "demand": "בינוני","supply": "גבוה",  "hot": False, "reason": "המשך קציר ברזיל"},
            4:  {"avg_move": +1.5, "demand": "עולה", "supply": "יורד",   "hot": False, "reason": "סוף קציר — מלאים יורדים"},
            5:  {"avg_move": +3.2, "demand": "גבוה", "supply": "יורד",   "hot": True,  "reason": "תחילת עונת זריעה — אי-וודאות"},
            6:  {"avg_move": +4.8, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "חשש כפור ברזיל — שיא תנודתיות"},
            7:  {"avg_move": +5.5, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "עונת כפור ברזיל — מחיר קופץ"},
            8:  {"avg_move": +3.1, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "המשך אי-וודאות יבול"},
            9:  {"avg_move": +2.8, "demand": "עולה", "supply": "נמוך",   "hot": True,  "reason": "לפני קציר — ספקולציה"},
            10: {"avg_move": -1.5, "demand": "בינוני","supply": "עולה",  "hot": False, "reason": "תחילת קציר וייטנאם"},
            11: {"avg_move": -2.1, "demand": "בינוני","supply": "גבוה",  "hot": False, "reason": "קציר וייטנאם בשיא"},
            12: {"avg_move": -1.8, "demand": "גבוה", "supply": "גבוה",   "hot": False, "reason": "חגים — ביקוש עולה אך היצע גם"},
        }
    },
    "corn": {
        "name": "תירס", "emoji": "🌽",
        "monthly": {
            1:  {"avg_move": +1.2, "demand": "בינוני","supply": "בינוני","hot": False, "reason": "יציב — לפני עונת ברזיל"},
            2:  {"avg_move": +0.8, "demand": "בינוני","supply": "בינוני","hot": False, "reason": "שקט עונתי"},
            3:  {"avg_move": +3.5, "demand": "עולה", "supply": "יורד",   "hot": True,  "reason": "לפני עונת זריעה ארה\"ב — קנייה מוקדמת"},
            4:  {"avg_move": +4.2, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "עונת זריעה — שיא תנודתיות"},
            5:  {"avg_move": +5.1, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "זריעה ארה\"ב — מחירים גבוהים"},
            6:  {"avg_move": +3.8, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "גידול — בצורת = עלייה חדה"},
            7:  {"avg_move": -1.5, "demand": "בינוני","supply": "עולה",  "hot": False, "reason": "יבול טוב — ירידה"},
            8:  {"avg_move": -2.8, "demand": "יורד", "supply": "גבוה",   "hot": False, "reason": "לפני קציר — מכירות מוקדמות"},
            9:  {"avg_move": -4.5, "demand": "יורד", "supply": "שיא",    "hot": False, "reason": "קציר ארה\"ב — שיא היצע"},
            10: {"avg_move": -3.1, "demand": "יורד", "supply": "גבוה",   "hot": False, "reason": "המשך קציר"},
            11: {"avg_move": -1.2, "demand": "עולה", "supply": "יורד",   "hot": False, "reason": "סוף קציר — מתאזן"},
            12: {"avg_move": +1.8, "demand": "עולה", "supply": "יורד",   "hot": False, "reason": "ציפייה לעונה הבאה"},
        }
    },
    "soybeans": {
        "name": "סויה", "emoji": "🫘",
        "monthly": {
            1:  {"avg_move": -2.1, "demand": "בינוני","supply": "גבוה",  "hot": False, "reason": "קציר ברזיל בשיא — לחץ מחיר"},
            2:  {"avg_move": -3.5, "demand": "בינוני","supply": "שיא",   "hot": False, "reason": "שיא קציר ברזיל + ארגנטינה"},
            3:  {"avg_move": -2.8, "demand": "גבוה", "supply": "גבוה",   "hot": False, "reason": "סין קונה — אבל היצע גדול"},
            4:  {"avg_move": +1.5, "demand": "עולה", "supply": "יורד",   "hot": False, "reason": "סוף קציר דרום אמריקה"},
            5:  {"avg_move": +4.8, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "זריעה ארה\"ב — ציפיות ביקוש סין"},
            6:  {"avg_move": +5.5, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "שיא עונת זריעה — תנודתיות מקסימלית"},
            7:  {"avg_move": +4.2, "demand": "גבוה", "supply": "נמוך",   "hot": True,  "reason": "גידול ארה\"ב — חשש בצורת"},
            8:  {"avg_move": +2.1, "demand": "גבוה", "supply": "עולה",   "hot": False, "reason": "יבול טוב — מתמתן"},
            9:  {"avg_move": -2.5, "demand": "יורד", "supply": "גבוה",   "hot": False, "reason": "קציר ארה\"ב מתחיל"},
            10: {"avg_move": -3.8, "demand": "יורד", "supply": "שיא",    "hot": False, "reason": "שיא קציר ארה\"ב"},
            11: {"avg_move": -1.5, "demand": "עולה", "supply": "יורד",   "hot": False, "reason": "סין חוזרת לקנות"},
            12: {"avg_move": +1.2, "demand": "עולה", "supply": "יורד",   "hot": False, "reason": "ציפייה לעונה ברזיל"},
        }
    },
}

DEMAND_COLOR = {"שיא": "#c0392b", "גבוה": "#e67e22", "עולה": "#f39c12",
                "בינוני": "#2980b9", "יורד": "#27ae60", "נמוך": "#1abc9c"}
SUPPLY_COLOR = {"שיא": "#27ae60", "גבוה": "#2ecc71", "עולה": "#1abc9c",
                "בינוני": "#2980b9", "יורד": "#e67e22", "נמוך": "#c0392b"}
