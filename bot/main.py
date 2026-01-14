#!/usr/bin/env python3
"""
Crypto-Class - בוט טלגרם עם מסד נתונים ושרת אינטרנט משולב
גרסה מעודכנת עם טיפול ב-Event Loop
"""

import os
import sys
import logging
from datetime import datetime
from functools import wraps
import asyncio
import threading
import time
import concurrent.futures

# הוסף את תיקיית הפרויקט הראשית לנתיב החיפוש
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# הגדרת לוגים מיד בהתחלה
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

logger.info("🚀 מאתחל את המערכת...")

# יבוא ספריות
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
from telegram.error import TelegramError
from flask import Flask, request, jsonify, session, redirect, url_for, render_template

# ========== הגדרות מערכת ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip('/')
PORT = int(os.environ.get("PORT", 5000))
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "admin123")
TEACHER_SECRET = os.environ.get("TEACHER_SECRET", "default-secret-key-change-me")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "224223270").split(",") if x]

# בדיקת הגדרות קריטיות
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN לא הוגדר! הגדר את משתנה הסביבה BOT_TOKEN")
    sys.exit(1)

logger.info(f"🔧 הגדרות מערכת:")
logger.info(f"   • BOT_TOKEN: {'מוגדר' if BOT_TOKEN else 'לא מוגדר!'}")
logger.info(f"   • WEBHOOK_URL: {WEBHOOK_URL}")
logger.info(f"   • PORT: {PORT}")
logger.info(f"   • ADMIN_IDS: {ADMIN_IDS}")

# ========== אתחול מסד נתונים ==========
try:
    from database.db import init_database
    init_database()
    logger.info("✅ מסד נתונים אותחל בהצלחה")
    DATABASE_AVAILABLE = True
except Exception as e:
    logger.error(f"❌ שגיאה באתחול מסד נתונים: {e}")
    DATABASE_AVAILABLE = False

# ========== יבוא הפקודות ==========
try:
    # יבוא הפקודות הסינכרוניות המעודכנות
    from bot import commands_sync as commands
    logger.info("✅ מודול commands_sync נטען")
    
    # יבוא פקודות האדמין (אם קיים)
    try:
        from bot import admin_commands
        logger.info("✅ מודול admin_commands נטען")
    except ImportError:
        admin_commands = None
        logger.warning("⚠️ מודול admin_commands לא נמצא")
        
except ImportError as e:
    logger.error(f"❌ שגיאה ביבוא commands: {e}")
    sys.exit(1)

# ========== יבוא שאילתות ==========
try:
    from database.queries import get_system_stats, get_checkin_data, get_top_users, get_all_users
    logger.info("✅ מודול queries נטען")
except ImportError as e:
    logger.error(f"❌ שגיאה ביבוא queries: {e}")
    sys.exit(1)

# ========== יצירת Flask app ==========
flask_app = Flask(__name__)
flask_app.secret_key = TEACHER_SECRET

# ========== Middleware לאימות מורים ==========
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'teacher_logged_in' not in session:
            return redirect(url_for('teacher_login'))
        return f(*args, **kwargs)
    return decorated_function

# ========== פונקציות עזר ==========
def is_admin(user_id):
    """בדיקה אם משתמש הוא אדמין"""
    return user_id in ADMIN_IDS

# ========== Thread Pool Executor לעיבוד סינכרוני ==========
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

# ========== יצירה עצלנית של אפליקציית הטלגרם ==========
_application_instance = None
_application_initialized = False
_app_init_lock = threading.Lock()

def get_application() -> Application:
    """יצירה ואתחול עצלניים של אפליקציית הטלגרם (סינכרוני)"""
    global _application_instance, _application_initialized
    
    with _app_init_lock:
        if _application_instance is None:
            logger.info("🔄 יוצר את אפליקציית הטלגרם...")
            
            # יצירת event loop חדש עבור האפליקציה
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # בניית האפליקציה
                _application_instance = Application.builder().token(BOT_TOKEN).build()
                
                # רישום פקודות רגילות
                _application_instance.add_handler(CommandHandler("start", commands.start))
                _application_instance.add_handler(CommandHandler("checkin", commands.checkin))
                _application_instance.add_handler(CommandHandler("balance", commands.balance))
                _application_instance.add_handler(CommandHandler("referral", commands.referral))
                _application_instance.add_handler(CommandHandler("my_referrals", commands.my_referrals))
                _application_instance.add_handler(CommandHandler("leaderboard", commands.leaderboard))
                _application_instance.add_handler(CommandHandler("level", commands.level))
                _application_instance.add_handler(CommandHandler("contact", commands.contact))
                _application_instance.add_handler(CommandHandler("help", commands.help_command))
                _application_instance.add_handler(CommandHandler("website", commands.website))
                
                # רישום פקודות אדמין אם זמין
                if admin_commands:
                    _application_instance.add_handler(CommandHandler("admin", admin_commands.admin_panel))
                    _application_instance.add_handler(CommandHandler("admin_stats", admin_commands.admin_stats))
                    _application_instance.add_handler(CommandHandler("admin_users", admin_commands.admin_users))
                    _application_instance.add_handler(CommandHandler("admin_broadcast", admin_commands.admin_broadcast))
                    _application_instance.add_handler(CommandHandler("add_tokens", admin_commands.add_tokens))
                    _application_instance.add_handler(CommandHandler("reset_checkin", admin_commands.reset_checkin))
                
                # פקודת test פשוטה
                async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    """פקודת בדיקה"""
                    try:
                        user = update.effective_user
                        logger.info(f"✅ פקודת test מהמשתמש: {user.id}")
                        
                        is_user_admin = is_admin(user.id)
                        
                        await update.message.reply_text(
                            "✅ **הבוט פועל ומחובר!**\n\n"
                            f"👤 מזהה: {user.id}\n"
                            f"👋 שם: {user.first_name}\n"
                            f"👑 אדמין: {'✅ כן' if is_user_admin else '❌ לא'}\n"
                            f"📅 זמן: {datetime.now().strftime('%H:%M:%S')}\n"
                            f"🗄️ מסד נתונים: {'✅ פעיל' if DATABASE_AVAILABLE else '❌ לא פעיל'}",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"❌ שגיאה בפקודת test: {e}")
                
                _application_instance.add_handler(CommandHandler("test", test_command))
                
                # Error handler
                async def error_handler(update: object, context: CallbackContext):
                    logger.error(f"❌ שגיאה: {context.error}")
                
                _application_instance.add_error_handler(error_handler)
                
                # אתחול האפליקציה
                loop.run_until_complete(_application_instance.initialize())
                _application_initialized = True
                logger.info("✅ אפליקציית טלגרם אותחלה בהצלחה")
                
                return _application_instance
                
            except Exception as e:
                logger.error(f"❌ שגיאה באתחול אפליקציית טלגרם: {e}")
                raise
            finally:
                loop.close()
        
        return _application_instance

# ========== פונקציה להגדרת webhook ==========
def setup_webhook_sync():
    """הגדרת webhook בלבד (ללא אתחול Application)"""
    try:
        logger.info("🔄 מגדיר webhook...")
        
        # יצירת event loop חדש
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def setup():
            try:
                # שימוש ב-Bot פשוט רק להגדרת ה-webhook
                bot = Bot(token=BOT_TOKEN)
                await bot.delete_webhook()
                await asyncio.sleep(1)
                
                webhook_url = f"{WEBHOOK_URL}/webhook"
                logger.info(f"🔄 מגדיר webhook ל: {webhook_url}")
                
                await bot.set_webhook(
                    url=webhook_url,
                    max_connections=40,
                    allowed_updates=["message", "callback_query"]
                )
                logger.info("✅ Webhook הוגדר בהצלחה")
                return True
            except Exception as e:
                logger.error(f"❌ שגיאה בהגדרת webhook: {e}")
                return False
        
        success = loop.run_until_complete(setup())
        loop.close()
        
        if success:
            logger.info("🤖 Webhook מוכן - הבוט יפעל כאשר תשלח לו הודעה")
        else:
            logger.warning("⚠️ Webhook לא הוגדר")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ שגיאה קריטית בהגדרת webhook: {e}")
        return False

# ========== פונקציה לעיבוד עדכון ==========
async def process_webhook_update(update_data):
    """עיבוד אסינכרוני של עדכון webhook"""
    try:
        # קבל את האפליקציה המאותחלת
        app = get_application()
        
        # המרת הנתונים לעדכון
        update = Update.de_json(update_data, app.bot)
        
        # עיבוד העדכון
        await app.process_update(update)
        
        # לוג אם יש הודעה
        if update.message and update.message.text:
            user = update.effective_user
            logger.info(f"✅ עובד עדכון: {user.id} -> {update.message.text}")
        
    except Exception as e:
        logger.error(f"❌ שגיאה בעיבוד עדכון: {e}")

def process_webhook_update_sync(update_data):
    """עיבוד סינכרוני של עדכון webhook"""
    try:
        # יצירת event loop חדש לעיבוד
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # הפעלת העיבוד האסינכרוני
        loop.run_until_complete(process_webhook_update(update_data))
        
        # סגירה מסודרת של הלולאה
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        
    except Exception as e:
        logger.error(f"❌ שגיאה ב-process_webhook_update_sync: {e}")

# ========== פונקציית webhook לעיבוד הודעות ==========
@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """נקודת כניסה לעדכוני טלגרם"""
    try:
        # קבל את הנתונים מה-webhook
        update_data = request.get_json()
        
        if not update_data:
            logger.error("❌ אין נתונים בעדכון webhook")
            return jsonify({"error": "No data"}), 400
        
        # לוג מידע בסיסי
        user_id = None
        text = None
        
        if 'message' in update_data and 'text' in update_data['message']:
            text = update_data['message']['text']
            user_id = update_data['message']['from']['id'] if 'from' in update_data['message'] else 'unknown'
            logger.info(f"📩 קבלת הודעה ממשתמש {user_id}: {text}")
        
        # עיבוד העדכון ב-executor נפרד כדי לא לחסום
        executor.submit(process_webhook_update_sync, update_data)
        
        return 'OK'
        
    except Exception as e:
        logger.error(f"❌ שגיאה בעיבוד webhook: {e}")
        return jsonify({"error": str(e)}), 500

# ========== שאר נתיבי Flask ==========
@flask_app.route('/')
def index():
    """דף הבית"""
    try:
        stats = get_system_stats() if DATABASE_AVAILABLE else {}
        
        return render_template(
            'index.html',
            bot_token_defined=bool(BOT_TOKEN),
            database_available=DATABASE_AVAILABLE,
            webhook_configured=True,
            application_initialized=_application_initialized,
            stats=stats
        )
    except Exception as e:
        logger.error(f"❌ שגיאה בדף הבית: {e}")
        return f"שגיאה: {str(e)}", 500

@flask_app.route('/stats')
def public_stats():
    """דף סטטיסטיקות ציבורי"""
    try:
        if not DATABASE_AVAILABLE:
            return render_template('error.html', message="מסד הנתונים לא זמין כרגע"), 500
        
        stats = get_system_stats()
        top_users = get_top_users(10, 'tokens')
        
        return render_template(
            'stats.html',
            stats=stats,
            top_users=top_users
        )
            
    except Exception as e:
        logger.error(f"❌ שגיאה בדף סטטיסטיקות: {e}")
        return render_template('error.html', message=f"שגיאה בטעינת דף הסטטיסטיקות: {str(e)}"), 500

@flask_app.route('/health')
def health():
    """בדיקת בריאות"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_status": "active" if BOT_TOKEN else "inactive",
        "database": "available" if DATABASE_AVAILABLE else "unavailable",
        "webhook_configured": True,
        "application_initialized": _application_initialized,
        "bot_token_defined": bool(BOT_TOKEN),
        "admin_ids": ADMIN_IDS
    })

@flask_app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    """כניסת מורה"""
    try:
        if request.method == 'POST':
            password = request.form.get('password')
            
            if password == TEACHER_PASSWORD:
                session['teacher_logged_in'] = True
                return redirect(url_for('teacher_dashboard'))
            else:
                error = "סיסמה שגויה"
                return render_template('teacher/login.html', error=error)
        
        return render_template('teacher/login.html')
        
    except Exception as e:
        logger.error(f"❌ שגיאה בדף כניסת מורה: {e}")
        return render_template('error.html', message=f"שגיאה: {str(e)}"), 500

@flask_app.route('/teacher/logout')
def teacher_logout():
    """יציאה מהמערכת"""
    session.pop('teacher_logged_in', None)
    return redirect(url_for('teacher_login'))

@flask_app.route('/teacher')
@login_required
def teacher_dashboard():
    """דשבורד מורה"""
    try:
        if not DATABASE_AVAILABLE:
            return render_template('error.html', message="מסד הנתונים לא זמין"), 500
        
        stats = get_system_stats()
        top_users = get_top_users(10, 'tokens')
        
        return render_template(
            'teacher/dashboard.html',
            stats=stats,
            top_users=top_users
        )
            
    except Exception as e:
        logger.error(f"❌ שגיאה בדשבורד מורה: {e}")
        return render_template('error.html', message=f"שגיאה בטעינת נתונים: {str(e)}"), 500

@flask_app.route('/teacher/users')
@login_required
def teacher_users():
    """ניהול משתמשים - למורים"""
    try:
        if not DATABASE_AVAILABLE:
            return render_template('error.html', message="מסד הנתונים לא זמין"), 500
        
        users = get_all_users()
        
        return render_template(
            'teacher/users.html',
            users=users
        )
            
    except Exception as e:
        logger.error(f"❌ שגיאה בדף משתמשים: {e}")
        return render_template('error.html', message=f"שגיאה בטעינת משתמשים: {str(e)}"), 500

@flask_app.route('/setwebhook')
def set_webhook_manual():
    """הגדרת webhook ידנית"""
    success = setup_webhook_sync()
    
    if success:
        return render_template('success.html', 
            title="Webhook הוגדר",
            message="הבוט אמור לענות כעת לפקודות.",
            details="נסה לשלוח /start או /test לבוט בטלגרם."
        )
    else:
        return render_template('error.html', 
            title="שגיאת Webhook",
            message="לא ניתן להגדיר את ה-webhook כרגע.",
            details="נסה לרסטרט את השרת או בדוק את הלוגים."
        ), 500

@flask_app.route('/deletewebhook')
def delete_webhook():
    """מחיקת webhook"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def delete():
            bot = Bot(token=BOT_TOKEN)
            await bot.delete_webhook()
        
        loop.run_until_complete(delete())
        loop.close()
        
        logger.info("✅ Webhook נמחק בהצלחה")
        return jsonify({"success": True, "message": "Webhook deleted successfully"})
    except Exception as e:
        logger.error(f"❌ שגיאה במחיקת webhook: {e}")
        return jsonify({"error": str(e)}), 500

# ========== אתחול המערכת ==========
def initialize_on_startup():
    """אתחול המערכת בעת הפעלה"""
    time.sleep(3)  # המתן קצת
    logger.info("🚀 מתחיל אתחול אוטומטי...")
    
    # אתחול האפליקציה
    try:
        get_application()
        logger.info("✅ אפליקציית טלגרם אותחלה")
    except Exception as e:
        logger.error(f"❌ שגיאה באתחול אפליקציה: {e}")
    
    # הגדר webhook
    setup_webhook_sync()

# התחל את האתחול בפתיל נפרד
worker_id = os.environ.get("GUNICORN_WORKER_ID", "0")
if worker_id == "0":
    startup_thread = threading.Thread(target=initialize_on_startup, daemon=True)
    startup_thread.start()
    logger.info("🚀 התחלת אתחול אוטומטי בפתיל נפרד")
else:
    logger.info(f"⏸️ Worker {worker_id} - לא מפעיל אתחול בוט")

# ========== הרצת האפליקציה ==========
if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=PORT, debug=False)
