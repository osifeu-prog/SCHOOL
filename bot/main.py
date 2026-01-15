#!/usr/bin/env python3
"""
Crypto-Class - מערכת מלאה משולבת
גרסה 2.2.0 - יציבה ומשודרגת
"""

import os
import sys
import logging
import threading
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import telebot
from telebot.async_telebot import AsyncTeleBot

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
    # עבור בדיקות מקומיות
    BOT_TOKEN = "dummy_token_for_testing"
    logger.warning("⚠️ משתמש בטוקן דמי לבדיקה מקומית")

PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip('/')
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin123")
SECRET_KEY = os.environ.get("SECRET_KEY", "crypto-class-secret-key-2026-change-this")

# אתחול הבוט
try:
    bot = AsyncTeleBot(BOT_TOKEN)
    logger.info(f"✅ בוט אותחל")
except Exception as e:
    logger.error(f"❌ שגיאה באתחול הבוט: {e}")
    # יצירת בוט דמי לבדיקה
    bot = None

# ========== יבוא מודולים פנימיים ==========
try:
    from database.db import Session, init_database, ensure_database_initialized
    from database.queries import (
        get_user, register_user, checkin_user, get_balance,
        get_top_users, get_system_stats, get_activity_count,
        get_total_referrals, get_referred_users, get_all_users,
        get_user_attendance_history, get_checkin_data,
        add_tokens_to_user, reset_user_checkin, get_daily_stats
    )
    logger.info("✅ מודולי מסד נתונים נטענו")
except ImportError as e:
    logger.error(f"❌ שגיאה בטעינת מודולי מסד נתונים: {e}")
    # פונקציות דמה לבדיקה
    def get_user(*args, **kwargs): return None
    def get_system_stats(*args, **kwargs): return {'total_users': 0, 'active_today': 0, 'total_tokens': 0}
    def get_top_users(*args, **kwargs): return []
    Session = None

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
            return jsonify({
                "status": "info",
                "message": "WEBHOOK_URL לא מוגדר. משתמש בפולינג מקומי.",
                "mode": "polling"
            })
        
        webhook_url = f"{WEBHOOK_URL}/webhook"
        
        try:
            # נסה להגדיר webhook אם הבוט זמין
            if bot:
                import asyncio
                asyncio.run(bot.set_webhook(url=webhook_url))
                return jsonify({
                    "status": "success",
                    "message": "Webhook הוגדר בהצלחה",
                    "webhook_url": webhook_url
                })
            else:
                return jsonify({
                    "status": "info",
                    "message": "בוט לא זמין. הגדרת webhook נדחתה.",
                    "suggested_url": webhook_url
                })
        except Exception as e:
            logger.error(f"❌ שגיאה בהגדרת webhook: {e}")
            return jsonify({
                "status": "error",
                "message": f"שגיאה בהגדרת webhook: {str(e)}",
                "suggested_url": webhook_url
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
            
            # מעבד את העדכון במייל (א-סינכרוני)
            threading.Thread(target=process_update_sync, args=(update,)).start()
            
            return 'OK'
        else:
            return 'Invalid content type', 400
    except Exception as e:
        logger.error(f"❌ שגיאה בעיבוד webhook: {e}")
        return jsonify({"error": str(e)}), 500

def process_update_sync(update):
    """עיבוד עדכון בצורה סינכרונית"""
    try:
        if bot:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_update(update))
            loop.close()
    except Exception as e:
        logger.error(f"❌ שגיאה בעיבוד עדכון: {e}")

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
        
        # יבוא דינמי של הפקודות
        try:
            from bot.commands_sync import (
                start, checkin, balance, referral, my_referrals,
                leaderboard, level, profile, tasks, contact,
                help_command, website, admin_panel, add_tokens,
                reset_checkin
            )
        except ImportError as e:
            logger.error(f"❌ שגיאה ביבוא פקודות: {e}")
            if bot:
                await bot.reply_to(message, "🔧 המערכת בעיצומה של עדכון. נסה שוב בעוד מספר דקות.")
            return
        
        if text.startswith('/start'):
            await start(message, bot)
        elif text.startswith('/checkin'):
            await checkin(message, bot)
        elif text.startswith('/balance'):
            await balance(message, bot)
        elif text.startswith('/referral'):
            await referral(message, bot)
        elif text.startswith('/my_referrals'):
            await my_referrals(message, bot)
        elif text.startswith('/leaderboard'):
            await leaderboard(message, bot)
        elif text.startswith('/level'):
            await level(message, bot)
        elif text.startswith('/profile'):
            await profile(message, bot)
        elif text.startswith('/tasks'):
            await tasks(message, bot)
        elif text.startswith('/contact'):
            await contact(message, bot)
        elif text.startswith('/help'):
            await help_command(message, bot)
        elif text.startswith('/website'):
            await website(message, bot)
        elif text.startswith('/admin'):
            await admin_panel(message, bot)
        elif text.startswith('/add_tokens'):
            await add_tokens(message, bot)
        elif text.startswith('/reset_checkin'):
            await reset_checkin(message, bot)
        else:
            if bot:
                await bot.reply_to(message, "❔ לא מזהה את הפקודה. שלח /help לעזרה")
            
    except Exception as e:
        logger.error(f"❌ שגיאה בטיפול בפקודה: {e}")
        if bot:
            await bot.reply_to(message, "❌ אירעה שגיאה בעיבוד הפקודה. אנא נסה שוב.")

# ========== דפי אתר ==========
@flask_app.route('/')
def index():
    """דף הבית"""
    try:
        stats = get_system_stats()
        bot_username = "CryptoClassBot"  # ברירת מחדל
        if bot:
            try:
                bot_info = asyncio.run(bot.get_me())
                bot_username = bot_info.username if hasattr(bot_info, 'username') else "CryptoClassBot"
            except:
                pass
        
        # קבל נתונים נוספים
        today_stats = get_daily_stats()
        
        return render_template('index.html', 
                             stats=stats,
                             today_stats=today_stats,
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
        
        # פונקציית עזר לפורמט מספרים
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
        # בדיקת חיבור למסד נתונים
        db_status = "unknown"
        try:
            if Session:
                session = Session()
                session.execute("SELECT 1")
                session.close()
                db_status = "connected"
            else:
                db_status = "no_session"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # בדיקת בוט
        bot_status = "inactive"
        if bot:
            try:
                # בדיקה בסיסית
                bot_status = "active"
            except:
                bot_status = "error"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "bot": bot_status,
            "version": "2.2.0",
            "environment": os.environ.get("RAILWAY_ENVIRONMENT", "development"),
            "features": {
                "webhook": bool(WEBHOOK_URL),
                "teacher_dashboard": True,
                "api": True,
                "tasks": True
            }
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
        
        # פונקציית עזר לפורמט מספרים
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

@flask_app.route('/teacher/users')
def teacher_users():
    """ניהול משתמשים למורים"""
    if not session.get('teacher_logged_in'):
        return redirect(url_for('teacher_login'))
    
    try:
        users = get_all_users(limit=50)
        stats = get_system_stats()
        
        # פונקציית עזר לפורמט מספרים
        def intcomma(value):
            try:
                return f"{int(value):,}"
            except:
                return str(value)
        
        return render_template('teacher/teacher_users.html',
                             users=users,
                             stats=stats,
                             intcomma=intcomma,
                             now=datetime.now)
    except Exception as e:
        logger.error(f"❌ שגיאה בטעינת משתמשים: {e}")
        return render_template('error.html', error="שגיאה בטעינת משתמשים")

# ========== API פנימי ==========
@flask_app.route('/api/v1/user/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    """API לקבלת נתוני משתמש"""
    try:
        user = get_user(user_id)
        if user:
            return jsonify({
                "status": "success",
                "data": {
                    "id": user.telegram_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "tokens": user.tokens,
                    "level": user.level,
                    "referrals": user.total_referrals,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
            })
        else:
            return jsonify({"status": "error", "message": "משתמש לא נמצא"}), 404
    except Exception as e:
        logger.error(f"❌ שגיאה ב-API user: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@flask_app.route('/api/v1/stats', methods=['GET'])
def api_get_stats():
    """API לקבלת סטטיסטיקות"""
    try:
        stats = get_system_stats()
        return jsonify({
            "status": "success",
            "data": stats
        })
    except Exception as e:
        logger.error(f"❌ שגיאה ב-API stats: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@flask_app.route('/api/v1/checkin_data/<int:days>', methods=['GET'])
def api_get_checkin_data(days):
    """API לקבלת נתוני צ'ק-אין"""
    try:
        data = get_checkin_data(days)
        return jsonify({
            "status": "success",
            "data": data
        })
    except Exception as e:
        logger.error(f"❌ שגיאה ב-API checkin data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== פונקציות מערכת ==========
def run_bot_polling():
    """הרצת הבוט בפולינג (לגיבוי)"""
    try:
        if bot:
            logger.info("🤖 מפעיל בוט בפולינג...")
            asyncio.run(bot.polling(non_stop=True, timeout=60))
    except Exception as e:
        logger.error(f"❌ שגיאה בהרצת בוט: {e}")

# ========== שגיאות ==========
@flask_app.errorhandler(404)
def page_not_found(e):
    """טיפול בשגיאות 404"""
    return render_template('error.html', 
                         error="הדף לא נמצא",
                         message="הדף שביקשת אינו קיים במערכת."), 404

@flask_app.errorhandler(500)
def internal_server_error(e):
    """טיפול בשגיאות 500"""
    logger.error(f"❌ שגיאת שרת פנימית: {e}")
    return render_template('error.html', 
                         error="שגיאת שרת פנימית",
                         message="אירעה שגיאה בעיבוד הבקשה. אנא נסה שוב מאוחר יותר."), 500

# ========== הרצה ==========
if __name__ == '__main__':
    # אתחול מסד נתונים
    try:
        ensure_database_initialized()
        logger.info("✅ מסד נתונים אותחל")
    except Exception as e:
        logger.error(f"❌ שגיאה באתחול מסד נתונים: {e}")
    
    # הפעלת הבוט בפולינג אם מופעל
    if os.environ.get("USE_POLLING", "false").lower() == "true" and bot:
        bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
        bot_thread.start()
        logger.info("✅ בוט רץ בפולינג (thread נפרד)")
    
    # הפעלת שרת Flask
    logger.info(f"🚀 מפעיל שרת Flask על פורט {PORT}")
    logger.info(f"🌐 כתובת: http://localhost:{PORT}")
    logger.info(f"📊 בריאות מערכת: http://localhost:{PORT}/health")
    logger.info(f"👨‍🏫 דשבורד מורים: http://localhost:{PORT}/teacher/login")
    
    flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
