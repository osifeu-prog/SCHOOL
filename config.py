"""
הגדרות מערכת Crypto-Class
"""

import os

class Config:
    """הגדרות בסיסיות"""
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip('/')
    TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin123")
    SECRET_KEY = os.environ.get("SECRET_KEY", "crypto-class-secret-key-2026")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///crypto_class.db")
    USE_POLLING = os.environ.get("USE_POLLING", "false").lower() == "true"
    
    @classmethod
    def validate(cls):
        """בדיקת תקינות ההגדרות"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN לא מוגדר")
        
        if not cls.WEBHOOK_URL:
            errors.append("WEBHOOK_URL לא מוגדר (מומלץ ב-production)")
        
        if errors:
            raise ValueError("שגיאות בהגדרות: " + ", ".join(errors))
        
        return True
