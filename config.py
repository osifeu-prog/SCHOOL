#!/usr/bin/env python3
"""
קובץ הגדרות מערכת Crypto-Class
"""

import os
from datetime import datetime

# ========== הגדרות בסיסיות ==========

# שם המערכת
APP_NAME = "Crypto-Class"
APP_VERSION = "2.3.0"
APP_AUTHOR = "Osif Unger"

# נתיבים
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# וודא שהתיקיות קיימות
for directory in [DATA_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# ========== הגדרות מסד נתונים ==========

# נתיב למסד הנתונים
DB_PATH = os.path.join(DATA_DIR, 'attendance.db')

# הגדרות חיבור למסד הנתונים
DATABASE_CONFIG = {
    'url': f'sqlite:///{DB_PATH}',
    'echo': False,
    'pool_pre_ping': True,
    'pool_recycle': 3600
}

# ========== הגדרות בוט טלגרם ==========

# טוקן הבוט - ייקח מ-environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# הגדרות Webhook
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip('/')
PORT = int(os.environ.get("PORT", 5000))

# מצב Debug
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# ========== הגדרות אבטחה ==========

# סיסמת מורים
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin123")

# מפתח סודי ל-Flask
SECRET_KEY = os.environ.get("SECRET_KEY", "crypto-class-secret-key-2026-change-this")

# מזהה אדמין ראשי (אוסיף אונגר)
ADMIN_IDS = [224223270]

# ========== הגדרות מערכת ==========

# שימוש בפולינג (עבור פיתוח מקומי)
USE_POLLING = os.environ.get("USE_POLLING", "false").lower() == "true"

# זמן פעולה מקסימלי (בשניות)
TIMEOUT = 120

# מספר עובדים
WORKERS = 2

# מספר threads
THREADS = 4

# ========== הגדרות כלכלת טוקנים ==========

# בונוסים
CHECKIN_BASE_TOKENS = 1
CHECKIN_STREAK_BONUS = {
    3: 1,    # 3 ימים רצופים
    7: 3,    # 7 ימים רצופים
    14: 5,   # 14 ימים רצופים
    30: 10   # 30 ימים רצופים
}

# בונוס רמה
LEVEL_BONUS_DIVISOR = 3  # כל X רמות בונוס נוסף

# בונוסי הרשמה
REGISTRATION_BONUS = 10  # טוקנים למשתמש חדש
REFERRAL_BONUS_REFERRER = 10  # טוקנים למזמין
REFERRAL_BONUS_REFERRED = 5   # טוקנים למוזמן

# ========== הגדרות משימות ==========

# משימות ברירת מחדל
DEFAULT_TASKS = [
    {
        "name": "צ'ק-אין יומי",
        "description": "התחבר כל יום וקבל טוקן",
        "task_type": "class",
        "frequency": "daily",
        "tokens_reward": 1,
        "exp_reward": 10,
        "is_active": True
    },
    {
        "name": "תרומה לפורום",
        "description": "פרסם תשובה או שאלה בפורום הקורס",
        "task_type": "forum",
        "frequency": "daily",
        "tokens_reward": 3,
        "exp_reward": 25,
        "requires_proof": True,
        "is_active": True
    },
    {
        "name": "סיוע לתלמיד",
        "description": "עזור לתלמיד אחר בשאלה או בעיה",
        "task_type": "help",
        "frequency": "daily",
        "tokens_reward": 5,
        "exp_reward": 50,
        "requires_proof": True,
        "is_active": True
    },
    {
        "name": "הפניה של חבר",
        "description": "הזמן חבר חדש למערכת",
        "task_type": "referral",
        "frequency": "one_time",
        "tokens_reward": 10,
        "exp_reward": 100,
        "is_active": True
    }
]

# ========== פונקציות עזר ==========

def get_app_info():
    """קבלת מידע על המערכת"""
    return {
        'name': APP_NAME,
        'version': APP_VERSION,
        'author': APP_AUTHOR,
        'start_time': datetime.now().isoformat(),
        'debug': DEBUG,
        'database_path': DB_PATH,
        'webhook_url': WEBHOOK_URL,
        'port': PORT
    }

def validate_config():
    """בדיקת תקינות ההגדרות"""
    errors = []
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN לא הוגדר")
    
    if not WEBHOOK_URL and not USE_POLLING:
        errors.append("WEBHOOK_URL לא הוגדר וגם USE_POLLING לא מופעל")
    
    if not SECRET_KEY or SECRET_KEY == "crypto-class-secret-key-2026-change-this":
        errors.append("SECRET_KEY לא הוגדר או שהוא ברירת מחדל")
    
    return errors

# ========== בדיקת תקינות בעת טעינה ==========

if __name__ == "__main__":
    print(f"🔧 {APP_NAME} v{APP_VERSION}")
    print(f"📁 נתיב בסיס: {BASE_DIR}")
    print(f"💾 נתיב מסד נתונים: {DB_PATH}")
    
    errors = validate_config()
    if errors:
        print("❌ שגיאות בהגדרות:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("✅ כל ההגדרות תקינות")
    
    print(f"\n📊 מידע מערכת:")
    info = get_app_info()
    for key, value in info.items():
        print(f"   • {key}: {value}")
