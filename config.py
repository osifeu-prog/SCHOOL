# config.py
import os

class Config:
    # טוקן הבוט
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # הגדרות Webhook
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip('/')
    PORT = int(os.environ.get("PORT", 5000))
    
    # הגדרות מסד נתונים
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data/attendance.db")
    
    # הגדרות מורים
    TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin123")
    TEACHER_SECRET = os.environ.get("TEACHER_SECRET", "change-this-secret-key")
    TEACHER_PORT = int(os.environ.get("TEACHER_PORT", 5001))
    
    # הגדרות כללי
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
