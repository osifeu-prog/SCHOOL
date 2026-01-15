#!/usr/bin/env python3
"""
Crypto-Class - מערכת מלאה משולבת
גרסה משודרגת עם אינטגרציה מלאה
"""

import os
import sys
import logging
import threading
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify, render_template
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot import asyncio_helper

# הוסף את התיקיות הנדרשות ל-PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secure-key")

# אתחול הבוט
try:
    bot = AsyncTeleBot(BOT_TOKEN)
    logger.info(f"✅ בוט אותחל עם טוקן: {BOT_TOKEN[:10]}...")
except Exception as e:
    logger.error(f"❌ שגיאה באתחול הבוט: {e}")
    sys.exit(1)

# ========== יבוא מודולים פנימיים ==========
try:
    from database.db import Session, init_database, ensure_database_initialized
    from database.queries import (
        get_user, register_user, checkin_user, get_balance,
        get_top_users, get_system_stats, get_activity_count,
        get_total_referrals, get_referred_users
    )
    from bot import commands_sync as commands
    from bot import admin_commands
    logger.info("✅ מודולים נטענו בהצלחה")
except ImportError as e:
    logger.error(f"❌ שגיאה בטעינת מודולים: {e}")
    sys.exit(1)

# ========== יצירת Flask app ==========
flask_app = Flask(__name__)
flask_app.secret_key = SECRET_KEY

# ========== אתחול מסד נתונים ==========
@flask_app.before_first_request
def initialize_database():
    """אתחול מסד הנתונים בעת הפעלה"""
    try:
        ensure_database_initialized()
        logger.info("✅ מסד נתונים אותחל")
    except Exception as e:
        logger.error(f"❌ שגיאה באתחול מסד נתונים: {e}")

# ========== הגדרת Webhook ==========
@flask_app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    """הגדרת webhook לבוט"""
    try:
        if not WEBHOOK_URL:
            return jsonify({"error": "WEBHOOK_URL לא מוגדר"}), 400
        
        webhook_url = f"{WEBHOOK_URL}/webhook"
        # בסביבת production, יש להגדיר webhook אמיתי
        # כאן נחזיר הודעה שהמערכת עובדת
        return jsonify({
            "status": "success",
            "message": "Webhook מוכן להגדרה",
            "webhook_url": webhook_url,
            "bot_username": bot.get_me().username if hasattr(bot, 'get_me') else "לא זמין"
        })
    except Exception as e:
        logger.error(f"❌ שגיאה בהגדרת webhook: {e}")
        return jsonify({"error": str(e)}), 500

# ========== Webhook Endpoint ==========
@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """טיפול בפקודות מטלגרם"""
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            
            # עיבוד עדכון בבוט
            asyncio.run(process_update(update))
            
            return 'OK'
        else:
            return 'Invalid content type', 400
    except Exception as e:
        logger.error(f"❌ שגיאה בעיבוד webhook: {e}")
        return jsonify({"error": str(e)}), 500

async def process_update(update):
    """עיבוד עדכון מבוט טלגרם"""
    try:
        if update.message:
            message = update.message
            user = message.from_user
            
            logger.info(f"📩 הודעה מ-{user.id} ({user.first_name}): {message.text}")
            
            # טיפול בפקודות
            if message.text:
                await handle_command(message)
                
    except Exception as e:
        logger.error(f"❌ שגיאה בעיבוד עדכון: {e}")

async def handle_command(message):
    """טיפול בפקודת המשתמש"""
    try:
        text = message.text
        user = message.from_user
        
        if text.startswith('/start'):
            await commands.start(message, bot)
        elif text.startswith('/checkin'):
            await commands.checkin(message, bot)
        elif text.startswith('/balance'):
            await commands.balance(message, bot)
        elif text.startswith('/referral'):
            await commands.referral(message, bot)
        elif text.startswith('/my_referrals'):
            await commands.my_referrals(message, bot)
        elif text.startswith('/leaderboard'):
            await commands.leaderboard(message, bot)
        elif text.startswith('/level'):
            await commands.level(message, bot)
        elif text.startswith('/contact'):
            await commands.contact(message, bot)
        elif text.startswith('/help'):
            await commands.help_command(message, bot)
        elif text.startswith('/website'):
            await commands.website(message, bot)
        elif text.startswith('/admin'):
            await admin_commands.admin_panel(message, bot)
        elif text.startswith('/add_tokens'):
            await admin_commands.add_tokens(message, bot)
        elif text.startswith('/reset_checkin'):
            await admin_commands.reset_checkin(message, bot)
        else:
            await bot.reply_to(message, "❔ לא מזהה את הפקודה. שלח /help לעזרה")
            
    except Exception as e:
        logger.error(f"❌ שגיאה בטיפול בפקודה: {e}")
        await bot.reply_to(message, "❌ אירעה שגיאה בעיבוד הפקודה. אנא נסה שוב.")

# ========== דפי אתר ==========
@flask_app.route('/')
def index():
    """דף הבית"""
    try:
        stats = get_system_stats()
        return render_template('index.html', 
                             stats=stats,
                             bot_username=bot.get_me().username if hasattr(bot, 'get_me') else "CryptoClassBot")
    except Exception as e:
        logger.error(f"❌ שגיאה בטעינת דף הבית: {e}")
        return render_template('error.html', error="שגיאה בטעינת הדף")

@flask_app.route('/stats')
def stats_page():
    """דף סטטיסטיקות"""
    try:
        stats = get_system_stats()
        top_users = get_top_users(10, 'tokens')
        return render_template('stats.html', 
                             stats=stats,
                             top_users=top_users)
    except Exception as e:
        logger.error(f"❌ שגיאה בטעינת סטטיסטיקות: {e}")
        return render_template('error.html', error="שגיאה בטעינת סטטיסטיקות")

@flask_app.route('/health')
def health_check():
    """בדיקת בריאות המערכת"""
    try:
        # בדיקת חיבור למסד נתונים
        session = Session()
        session.execute("SELECT 1")
        session.close()
        
        # בדיקת בוט
        bot_ok = BOT_TOKEN is not None
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "bot": "active" if bot_ok else "inactive",
            "version": "2.2.0",
            "environment": os.environ.get("RAILWAY_ENVIRONMENT", "development")
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@flask_app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    """כניסת מורה"""
    from flask import request, session, redirect, url_for
    
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
    from flask import session, redirect, url_for
    
    if not session.get('teacher_logged_in'):
        return redirect(url_for('teacher_login'))
    
    try:
        stats = get_system_stats()
        top_users = get_top_users(10, 'tokens')
        
        return render_template('teacher/teacher_dashboard.html',
                             stats=stats,
                             top_users=top_users)
    except Exception as e:
        logger.error(f"❌ שגיאה בטעינת דשבורד מורה: {e}")
        return render_template('error.html', error="שגיאה בטעינת הדשבורד")

@flask_app.route('/teacher/logout')
def teacher_logout():
    """יציאת מורה"""
    from flask import session, redirect, url_for
    session.pop('teacher_logged_in', None)
    return redirect(url_for('index'))

# ========== API פנימי ==========
@flask_app.route('/api/v1/user/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    """API לקבלת נתוני משתמש"""
    try:
        user = get_user(user_id)
        if user:
            return jsonify({
                "id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "tokens": user.tokens,
                "level": user.level,
                "referrals": user.total_referrals,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })
        else:
            return jsonify({"error": "משתמש לא נמצא"}), 404
    except Exception as e:
        logger.error(f"❌ שגיאה ב-API user: {e}")
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/v1/stats', methods=['GET'])
def api_get_stats():
    """API לקבלת סטטיסטיקות"""
    try:
        stats = get_system_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"❌ שגיאה ב-API stats: {e}")
        return jsonify({"error": str(e)}), 500

# ========== פונקציות מערכת ==========
def run_bot_polling():
    """הרצת הבוט בפולינג (לגיבוי)"""
    try:
        logger.info("🤖 מפעיל בוט בפולינג...")
        asyncio.run(bot.polling(non_stop=True, timeout=60))
    except Exception as e:
        logger.error(f"❌ שגיאה בהרצת בוט: {e}")

# ========== הרצה ==========
if __name__ == '__main__':
    # הפעלת הבוט בפולינג בתוך thread נפרד
    if os.environ.get("USE_POLLING", "false").lower() == "true":
        bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
        bot_thread.start()
        logger.info("✅ בוט רץ בפולינג (thread נפרד)")
    
    # הפעלת שרת Flask
    logger.info(f"🚀 מפעיל שרת Flask על פורט {PORT}")
    flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
