#!/usr/bin/env python3
"""
Crypto-Class - מערכת מלאה משולבת
גרסה 2.4.0 - מבוסס python-telegram-bot עם asyncio תקין
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# הוסף את התיקיות הנדרשות ל-PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('crypto_class.log')
    ]
)
logger = logging.getLogger(__name__)

# ========== הגדרות מערכת ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN לא מוגדר!")
    sys.exit(1)

PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip('/')
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin123")
SECRET_KEY = os.environ.get("SECRET_KEY", "crypto-class-secret-key-2026-change-this")

# ========== יבוא מודולים פנימיים ==========
try:
    from database.db import Session, init_database, ensure_database_initialized
    from database.queries import (
        get_user, register_user, checkin_user, get_balance,
        get_top_users, get_system_stats, get_activity_count,
        get_total_referrals, get_referred_users, get_all_users,
        get_checkin_data, get_today_stats, get_streak_stats,
        get_activity_stats, get_api_stats
    )
    logger.info("✅ מודולי מסד נתונים נטענו")
except ImportError as e:
    logger.error(f"❌ שגיאה בטעינת מודולי מסד נתונים: {e}")
    sys.exit(1)

# ========== יצירת Flask app ==========
flask_app = Flask(__name__)
flask_app.secret_key = SECRET_KEY

# ========== אתחול מסד נתונים ==========
def initialize_database():
    """אתחול מסד הנתונים בעת הפעלה"""
    try:
        ensure_database_initialized()
        logger.info("✅ מסד נתונים אותחל")
    except Exception as e:
        logger.error(f"❌ שגיאה באתחול מסד נתונים: {e}")

# ========== יבוא פקודות ==========
try:
    # יבוא פקודות מקובץ commands.py
    from bot.commands import (
        start, checkin, balance, referral, my_referrals,
        leaderboard, level, contact, help_command, website
    )
    logger.info("✅ פקודות הבוט נטענו")
except ImportError as e:
    logger.error(f"❌ שגיאה ביבוא פקודות: {e}")
    sys.exit(1)

# ========== הגדרת handlers ל-PTB ==========
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפקודת /start"""
    await start(update, context)

async def checkin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפקודת /checkin"""
    await checkin(update, context)

async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפקודת /balance"""
    await balance(update, context)

async def referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפקודת /referral"""
    await referral(update, context)

async def my_referrals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפקודת /my_referrals"""
    await my_referrals(update, context)

async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפקודת /leaderboard"""
    await leaderboard(update, context)

async def level_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפקודת /level"""
    await level(update, context)

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפקודת /contact"""
    await contact(update, context)

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפקודת /help"""
    await help_command(update, context)

async def website_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפקודת /website"""
    await website(update, context)

# ========== פונקציות תמיכה ==========
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בשגיאות"""
    logger.error(f"שגיאה: {context.error}")
    try:
        await update.message.reply_text("❌ אירעה שגיאה. אנא נסה שוב מאוחר יותר.")
    except:
        pass

# ========== אתחול הבוט ==========
async def setup_bot():
    """הגדרת הבוט והוספת handlers"""
    try:
        # יצירת Application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # הוספת handlers לפקודות
        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CommandHandler("checkin", checkin_handler))
        application.add_handler(CommandHandler("balance", balance_handler))
        application.add_handler(CommandHandler("referral", referral_handler))
        application.add_handler(CommandHandler("my_referrals", my_referrals_handler))
        application.add_handler(CommandHandler("leaderboard", leaderboard_handler))
        application.add_handler(CommandHandler("level", level_handler))
        application.add_handler(CommandHandler("contact", contact_handler))
        application.add_handler(CommandHandler("help", help_handler))
        application.add_handler(CommandHandler("website", website_handler))
        
        # טיפול בשגיאות
        application.add_error_handler(error_handler)
        
        logger.info("✅ הבוט אותחל עם כל הפקודות")
        return application
    except Exception as e:
        logger.error(f"❌ שגיאה באתחול הבוט: {e}")
        return None

# ========== הרצת הבוט ==========
async def run_bot():
    """הרצת הבוט בפולינג"""
    try:
        application = await setup_bot()
        if application:
            logger.info("🤖 מפעיל בוט בפולינג...")
            await application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"❌ שגיאה בהרצת בוט: {e}")

# ========== דפי אתר ==========
@flask_app.route('/')
def index():
    """דף הבית"""
    try:
        stats = get_system_stats()
        bot_username = "CryptoClassBot"
        
        # קבל נתונים נוספים
        today_stats = get_today_stats()
        streak_stats = get_streak_stats()
        activity_stats = get_activity_stats()
        
        return render_template('index.html', 
                             stats=stats,
                             today_stats=today_stats,
                             streak_stats=streak_stats,
                             activity_stats=activity_stats,
                             bot_username=bot_username,
                             now=datetime.now)
    except Exception as e:
        logger.error(f"❌ שגיאה בטעינת דף הבית: {e}")
        return render_template('error.html', error="שגיאה בטעינת הדף")

@flask_app.route('/stats')
def stats_page():
    """דף סטטיסטיקות"""
    try:
        stats = get_system_stats()
        top_users = get_top_users(10, 'tokens')
        
        def intcomma(value):
            try:
                return f"{int(value):,}"
            except:
                return str(value)
        
        return render_template('stats.html', 
                             stats=stats,
                             top_users=top_users,
                             intcomma=intcomma,
                             now=datetime.now)
    except Exception as e:
        logger.error(f"❌ שגיאה בטעינת סטטיסטיקות: {e}")
        return render_template('error.html', error="שגיאה בטעינת סטטיסטיקות")

@flask_app.route('/health')
def health_check():
    """בדיקת בריאות המערכת"""
    try:
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "bot": "active" if BOT_TOKEN else "inactive",
            "version": "2.4.0",
            "features": ["web", "bot", "database"]
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

# ========== הרצת המערכת ==========
def run_flask():
    """הרצת שרת Flask"""
    flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

async def main():
    """הרצה ראשית של כל המערכת"""
    # אתחול מסד נתונים
    initialize_database()
    
    # הפעלת הבוט בטאסק נפרד
    bot_task = asyncio.create_task(run_bot())
    
    # הפעלת Flask (בבלוקינג, אז צריך thread נפרד)
    import threading
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info(f"🚀 המערכת הופעלה!")
    logger.info(f"🌐 שרת Flask רץ על פורט {PORT}")
    logger.info(f"🤖 הבוט רץ בפולינג")
    
    # המתן לבוט (ה-Flask רץ ב-thread נפרד)
    try:
        await bot_task
    except KeyboardInterrupt:
        logger.info("🛑 קבלת SIGINT - סיום תהליך...")

if __name__ == '__main__':
    try:
        # הפעל את המערכת הראשית
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 סיום תהליך...")
    except Exception as e:
        logger.error(f"❌ שגיאה קריטית: {e}")
