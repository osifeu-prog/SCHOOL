#!/usr/bin/env python3
"""
הגדרות מערכת - Crypto-Class
"""

import os
from pathlib import Path

# נתיבים
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'

# צור תיקיות אם לא קיימות
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# הגדרות בוט
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '').rstrip('/')
PORT = int(os.environ.get('PORT', 5000))

# הגדרות מורה
TEACHER_PASSWORD = os.environ.get('TEACHER_PASSWORD', 'admin123')
SECRET_KEY = os.environ.get('SECRET_KEY', 'crypto-class-secret-key-2026-change-this')

# הגדרות מסד נתונים
DATABASE_URL = f"sqlite:///{DATA_DIR / 'attendance.db'}"

# הגדרות מערכת
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
USE_POLLING = os.environ.get('USE_POLLING', 'false').lower() == 'true'
ADMIN_IDS = [int(x) for x in os.environ.get('ADMIN_IDS', '224223270').split(',') if x]

# הגדרות אפליקציה
APP_NAME = "Crypto-Class"
APP_VERSION = "2.2.0"
APP_DESCRIPTION = "מערכת ניהול נוכחות ומשימות מבוססת טוקנים"
