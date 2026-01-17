#!/usr/bin/env python3
"""
Crypto-Class - מערכת מלאה משולבת
גרסה 2.5.0 - מבוסס webhook עם Flask ו-python-telegram-bot
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

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
    from database.db import ensure_database_initialized
    from database.queries import (
        get_top_users, get_system_stats, get_today_stats,
        get_streak_stats, get_activity_stats
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

# ========== הגדרת הבוט וה-Application ==========
# יצירת Application עבור הבוט
application = Application.builder().token(BOT_TOKEN).build()

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
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בשגיאות"""
    logger.error(f"שגיאה: {context.error}")
    try:
        await update.message.reply_text("❌ אירעה שגיאה. אנא נסה שוב מאוחר יותר.")
    except:
        pass

application.add_error_handler(error_handler)

# ========== הגדרת Webhook ב-Flask ==========
@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    """טיפול בבקשות webhook מטלגרם"""
    try:
        # קבלת העדכון מטלגרם
        update = Update.de_json(await request.get_json(), application.bot)
        
        # עיבוד העדכון
        await application.process_update(update)
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"❌ שגיאה בעיבוד webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@flask_app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    """הגדרת webhook לבוט"""
    try:
        if not WEBHOOK_URL:
            return jsonify({
                "status": "info",
                "message": "WEBHOOK_URL לא מוגדר. הגדר משתנה סביבה זה כדי להפעיל webhook.",
                "mode": "polling"
            })
        
        webhook_url = f"{WEBHOOK_URL}/webhook"
        
        # הגדר את ה-webhook
        from telegram.error import TelegramError
        try:
            # נסה להגדיר webhook
            application.bot.set_webhook(url=webhook_url)
            return jsonify({
                "status": "success",
                "message": "Webhook הוגדר בהצלחה",
                "webhook_url": webhook_url
            })
        except TelegramError as e:
            logger.error(f"❌ שגיאה בהגדרת webhook: {e}")
            return jsonify({
                "status": "error",
                "message": f"שגיאה בהגדרת webhook: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"❌ שגיאה בהגדרת webhook: {e}")
        return jsonify({"error": str(e)}), 500

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
        # בדיקת חיבור למסד נתונים (דוגמה)
        from database.db import Session
        session = Session()
        session.execute("SELECT 1")
        session.close()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "bot": "active",
            "webhook": bool(WEBHOOK_URL),
            "version": "2.5.0",
            "features": ["web", "bot", "database", "webhook"]
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@flask_app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    """כניסת מורה"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if password == TEACHER_PASSWORD:
            session['teacher_logged_in'] = True
            session['teacher_login_time'] = datetime.now().isoformat()
            return redirect(url_for('teacher_dashboard'))
        else:
            return render_template('teacher/teacher_login.html', 
                                 error="סיסמה שגויה")
    
    return render_template('teacher/teacher_login.html')

@flask_app.route('/teacher')
def teacher_dashboard():
    """דשבורד מורה"""
    if not session.get('teacher_logged_in'):
        return redirect(url_for('teacher_login'))
    
    try:
        stats = get_system_stats()
        top_users = get_top_users(10, 'tokens')
        
        def intcomma(value):
            try:
                return f"{int(value):,}"
            except:
                return str(value)
        
        return render_template('teacher/teacher_dashboard.html',
                             stats=stats,
                             top_users=top_users,
                             intcomma=intcomma)
    except Exception as e:
        logger.error(f"❌ שגיאה בטעינת דשבורד מורה: {e}")
        return render_template('error.html', error="שגיאה בטעינת הדשבורד")

@flask_app.route('/teacher/logout')
def teacher_logout():
    """יציאת מורה"""
    session.pop('teacher_logged_in', None)
    return redirect(url_for('index'))

# ========== הרצת המערכת ==========
def main():
    """הרצה ראשית של כל המערכת"""
    # אתחול מסד נתונים
    initialize_database()
    
    # אם יש WEBHOOK_URL, נגדיר webhook, אחרת נשתמש בפולינג (לפיתוח מקומי)
    if WEBHOOK_URL:
        logger.info(f"🌐 מגדיר webhook: {WEBHOOK_URL}/webhook")
        
        # הגדר את ה-webhook
        try:
            webhook_url = f"{WEBHOOK_URL}/webhook"
            application.bot.set_webhook(url=webhook_url)
            logger.info(f"✅ Webhook הוגדר: {webhook_url}")
        except Exception as e:
            logger.error(f"❌ שגיאה בהגדרת webhook: {e}")
    else:
        logger.warning("⚠️ WEBHOOK_URL לא מוגדר, הבוט ירוץ בפולינג (לא מומלץ ב-production).")
    
    # הפעלת שרת Flask
    logger.info(f"🚀 מפעיל שרת Flask על פורט {PORT}")
    logger.info(f"📊 בריאות מערכת: {WEBHOOK_URL or 'http://localhost:' + str(PORT)}/health")
    
    flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
