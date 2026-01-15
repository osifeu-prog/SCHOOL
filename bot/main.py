#!/usr/bin/env python3
"""
Crypto-Class - מערכת משודרגת ובדוקה
"""

import os
import sys
import logging
import telebot
from flask import Flask, request, jsonify, render_template
import threading
import asyncio

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== הגדרות מערכת ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN לא מוגדר!")
    sys.exit(1)

PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip('/')

# אתחול הבוט
bot = telebot.TeleBot(BOT_TOKEN)

# ========== יבוא מודולים ==========
try:
    from database.db import Session, init_database
    from database.queries import (
        get_user, register_user, checkin_user, get_balance,
        get_top_users, get_system_stats
    )
    logger.info("✅ מודולים נטענו בהצלחה")
except ImportError as e:
    logger.error(f"❌ שגיאה בטעינת מודולים: {e}")
    sys.exit(1)

# ========== יצירת Flask app ==========
flask_app = Flask(__name__)

# ========== Webhook Endpoint ==========
@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """טיפול בפקודות מטלגרם"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        
        # תהליך העדכון בבוט
        bot.process_new_updates([update])
        
        return 'OK'
    else:
        return 'Invalid content type', 400

# ========== פקודות הבוט ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    """טיפול בפקודת /start"""
    try:
        user = message.from_user
        logger.info(f"🚀 /start מ-{user.id} ({user.first_name})")
        
        # בדוק אם המשתמש קיים
        existing_user = get_user(user.id)
        
        if existing_user:
            # משתמש קיים
            response = (
                f"👋 **ברוך השב, {user.first_name}!**\n\n"
                f"🎓 אתה כבר רשום ב-**Crypto-Class**\n"
                f"💰 הטוקנים שלך: **{existing_user.tokens:,}**\n"
                f"🏆 הרמה שלך: **{existing_user.level}**\n\n"
                f"📋 **פקודות זמינות:**\n"
                f"• /checkin - צ'ק-אין יומי (טוקן)\n"
                f"• /balance - יתרת טוקנים\n"
                f"• /referral - קוד הפניה\n"
                f"• /leaderboard - טבלת מובילים\n"
                f"• /profile - הפרופיל שלך\n"
                f"• /help - עזרה מלאה\n\n"
                f"🚀 **התחל עם:** /checkin"
            )
            
            # כפתורים מהירים
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(
                telebot.types.InlineKeyboardButton("✅ צ'ק-אין", callback_data="checkin"),
                telebot.types.InlineKeyboardButton("💰 טוקנים", callback_data="balance")
            )
            markup.row(
                telebot.types.InlineKeyboardButton("🏆 מובילים", callback_data="leaderboard"),
                telebot.types.InlineKeyboardButton("👥 הפניות", callback_data="referrals")
            )
            
            bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=markup)
            
        else:
            # משתמש חדש
            success = register_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            if success:
                # קבל את המשתמש שנרשם
                new_user = get_user(user.id)
                
                response = (
                    f"🎉 **ברוך הבא ל-Crypto-Class!**\n\n"
                    f"✅ **נרשמת בהצלחה!**\n"
                    f"👤 **שם:** {user.first_name}\n"
                    f"🆔 **מזהה:** {user.id}\n"
                    f"📅 **תאריך:** היום\n"
                    f"🔗 **קוד הפניה:** `{new_user.referral_code if new_user else 'לא זמין'}`\n\n"
                    f"🎁 **קבלת מתנה:** **10 טוקנים**!\n\n"
                    f"📚 **מה זה Crypto-Class?**\n"
                    f"זו מערכת למידה מבוססת טוקנים.\n\n"
                    f"🚀 **התחל עכשיו עם:** /checkin"
                )
                
                # כפתורים מהירים
                markup = telebot.types.InlineKeyboardMarkup()
                markup.row(
                    telebot.types.InlineKeyboardButton("🎁 קח טוקנים!", callback_data="get_tokens"),
                    telebot.types.InlineKeyboardButton("📚 למד עוד", callback_data="learn_more")
                )
                
                bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=markup)
                
            else:
                bot.send_message(message.chat.id, "❌ **אירעה שגיאה ברישום**\n\nנסה שוב או פנה לתמיכה: /contact", parse_mode="Markdown")
                
    except Exception as e:
        logger.error(f"❌ שגיאה ב-/start: {e}")
        bot.send_message(message.chat.id, "❌ אירעה שגיאה. אנא נסה שוב.")

@bot.message_handler(commands=['checkin'])
def handle_checkin(message):
    """טיפול בפקודת /checkin"""
    try:
        user = message.from_user
        
        success, msg = checkin_user(user.id)
        
        if success:
            balance = get_balance(user.id)
            response = f"✅ {msg}\n\n💰 **היתרה שלך:** {balance} טוקנים"
        else:
            response = f"⚠️ {msg}"
            
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ שגיאה ב-/checkin: {e}")
        bot.send_message(message.chat.id, "❌ אירעה שגיאה. נסה שוב.")

@bot.message_handler(commands=['balance'])
def handle_balance(message):
    """טיפול בפקודת /balance"""
    try:
        user = message.from_user
        balance = get_balance(user.id)
        
        response = (
            f"💰 **יתרת הטוקנים שלך, {user.first_name}:**\n\n"
            f"🪙 **סך הכל:** {balance} טוקנים\n\n"
            f"💡 **טיפ:** שלח /checkin כל יום לקבלת טוקנים נוספים!"
        )
        
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ שגיאה ב-/balance: {e}")
        bot.send_message(message.chat.id, "❌ אירעה שגיאה. נסה שוב.")

@bot.message_handler(commands=['referral'])
def handle_referral(message):
    """טיפול בפקודת /referral"""
    try:
        user = message.from_user
        db_user = get_user(user.id)
        
        if not db_user:
            bot.send_message(message.chat.id, "❌ **אתה לא רשום!**\n\nשלח /start כדי להירשם.", parse_mode="Markdown")
            return
        
        referral_code = db_user.referral_code
        bot_username = bot.get_me().username
        invite_link = f"https://t.me/{bot_username}?start={referral_code}"
        
        response = (
            f"👥 **מערכת ההפניות שלך**\n\n"
            f"🔗 **קוד ההפניה שלך:**\n`{referral_code}`\n\n"
            f"📤 **קישור הזמנה:**\n{invite_link}\n\n"
            f"🎁 **בונוסים:**\n"
            f"• הזמן חבר = **10 טוקנים**\n"
            f"• כל 5 חברים = **+50 טוקנים**\n\n"
            f"📝 **הוראות:**\n"
            f"1. שלח לחבר את הקישור\n"
            f"2. הוא ישלח /start עם הקוד\n"
            f"3. קבל 10 טוקנים מיד!"
        )
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("📤 שתף קישור", url=f"https://t.me/share/url?url={invite_link}&text=הצטרף%20לCrypto-Class!"),
            telebot.types.InlineKeyboardButton("👥 מוזמנים", callback_data="my_referrals")
        )
        
        bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        logger.error(f"❌ שגיאה ב-/referral: {e}")
        bot.send_message(message.chat.id, "❌ אירעה שגיאה. נסה שוב.")

@bot.message_handler(commands=['leaderboard'])
def handle_leaderboard(message):
    """טיפול בפקודת /leaderboard"""
    try:
        user = message.from_user
        top_users = get_top_users(10, 'tokens')
        
        if not top_users:
            response = "🏆 **טבלת המובילים**\n\nאין עדיין נתונים. היה הראשון שצובר טוקנים! 💪"
        else:
            response = "🏆 **טבלת המובילים - Top 10**\n\n"
            
            for i, top_user in enumerate(top_users, 1):
                name = top_user.first_name or top_user.username or f"משתמש {top_user.telegram_id}"
                
                if top_user.telegram_id == user.id:
                    response += f"{i}. 👑 **{name}** - {top_user.tokens:,} טוקנים\n"
                else:
                    response += f"{i}. {name} - {top_user.tokens:,} טוקנים\n"
        
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ שגיאה ב-/leaderboard: {e}")
        bot.send_message(message.chat.id, "❌ אירעה שגיאה. נסה שוב.")

@bot.message_handler(commands=['help', 'menu'])
def handle_help(message):
    """תפריט עזרה ראשי"""
    try:
        response = (
            "🆘 **תפריט ראשי - Crypto-Class**\n\n"
            "📱 **פקודות מהירות:**\n\n"
            "👤 **חשבון:**\n"
            "• /start - הרשמה והתחלה\n"
            "• /profile - הפרופיל שלך\n"
            "• /balance - טוקנים\n"
            "• /level - רמה והתקדמות\n\n"
            "📊 **פעילות:**\n"
            "• /checkin - צ'ק-אין יומי\n"
            "• /tasks - משימות זמינות\n"
            "• /referral - הזמן חברים\n"
            "• /leaderboard - טבלת מובילים\n\n"
            "ℹ️ **מידע:**\n"
            "• /help - תפריט זה\n"
            "• /contact - תמיכה\n"
            "• /website - אתר המערכת\n\n"
            "👑 **פקודות מתקדמות:**\n"
            "• /admin - לבעלי הרשאות\n"
            "• /stats - סטטיסטיקות\n\n"
            "💡 **טיפ:** השתמש בכפתורים למהירות!"
        )
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("💰 טוקנים", callback_data="balance"),
            telebot.types.InlineKeyboardButton("✅ צ'ק-אין", callback_data="checkin")
        )
        markup.row(
            telebot.types.InlineKeyboardButton("👥 הפניות", callback_data="referrals"),
            telebot.types.InlineKeyboardButton("🏆 מובילים", callback_data="leaderboard")
        )
        markup.row(
            telebot.types.InlineKeyboardButton("📞 תמיכה", callback_data="contact"),
            telebot.types.InlineKeyboardButton("🌐 אתר", callback_data="website")
        )
        
        bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        logger.error(f"❌ שגיאה ב-/help: {e}")
        bot.send_message(message.chat.id, "❌ אירעה שגיאה. נסה שוב.")

@bot.message_handler(commands=['website'])
def handle_website(message):
    """טיפול בפקודת /website"""
    try:
        web_url = "https://school-production-4d9d.up.railway.app"
        
        response = (
            f"🌐 **אתר האינטרנט של Crypto-Class**\n\n"
            f"🔗 **קישור לאתר:** {web_url}\n\n"
            f"🎯 **מה תמצא באתר:**\n"
            f"• 📊 דשבורד אישי\n"
            f"• 🏆 טבלאות מובילים\n"
            f"• 👨‍🏫 דשבורד מורים\n"
            f"• 📈 סטטיסטיקות\n\n"
            f"💻 **פתח עכשיו:**"
        )
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("🌐 פתח אתר", url=web_url),
            telebot.types.InlineKeyboardButton("📊 דשבורד", url=f"{web_url}/dashboard")
        )
        
        bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        logger.error(f"❌ שגיאה ב-/website: {e}")
        bot.send_message(message.chat.id, "❌ אירעה שגיאה. נסה שוב.")

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    """פאנל ניהול"""
    try:
        user = message.from_user
        
        # בדיקת הרשאות אדמין
        ADMIN_IDS = [224223270]  # החלף למזהה שלך
        
        if user.id not in ADMIN_IDS:
            bot.send_message(message.chat.id, "❌ **אין לך הרשאות ניהול!**", parse_mode="Markdown")
            return
        
        stats = get_system_stats()
        
        response = (
            "👑 **פאנל ניהול - Crypto-Class**\n\n"
            "📊 **סטטיסטיקות מערכת:**\n"
            f"• 👥 משתמשים: {stats.get('total_users', 0):,}\n"
            f"• 📅 פעילים היום: {stats.get('active_today', 0):,}\n"
            f"• 💰 טוקנים כוללים: {stats.get('total_tokens', 0):,}\n\n"
            "⚙️ **פקודות ניהול:**\n"
            "• /admin_stats - סטטיסטיקות מפורטות\n"
            "• /admin_users - ניהול משתמשים\n"
            "• /admin_broadcast - שליחת הודעה לכולם\n"
            "• /add_tokens <id> <amount> - הוספת טוקנים\n"
            "• /reset_checkin <id> - איפוס צ'ק-אין\n\n"
            "🆔 **מזהה האדמין שלך:** {user.id}"
        )
        
        bot.send_message(message.chat.id, response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ שגיאה ב-/admin: {e}")
        bot.send_message(message.chat.id, "❌ אירעה שגיאה. נסה שוב.")

# ========== טיפול בכפתורים ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """טיפול בכפתורי אינטראקציה"""
    try:
        user = call.from_user
        chat_id = call.message.chat.id
        data = call.data
        
        logger.info(f"🔘 Callback from {user.id}: {data}")
        
        if data == "checkin":
            # יצירת הודעה דמה לבדיקה
            message = type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})()
            })()
            handle_checkin(message)
            
        elif data == "balance":
            message = type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})()
            })()
            handle_balance(message)
            
        elif data == "referrals":
            message = type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})()
            })()
            handle_referral(message)
            
        elif data == "leaderboard":
            message = type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})()
            })()
            handle_leaderboard(message)
            
        elif data == "contact":
            bot.send_message(chat_id, "📞 **צור קשר:**\n\n👤 אוסיף אונגר\n📱 טלגרם: @osifeu\n📧 טלפון: 0584203384", parse_mode="Markdown")
            
        elif data == "website":
            handle_website(type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})()
            })())
            
        elif data == "get_tokens":
            bot.answer_callback_query(call.id, "🎉 קיבלת 10 טוקנים מתנה!", show_alert=True)
            
        elif data == "learn_more":
            handle_help(type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})()
            })())
            
        else:
            bot.answer_callback_query(call.id, "⚙️ תכונה זו בפיתוח", show_alert=False)
            
    except Exception as e:
        logger.error(f"❌ שגיאה ב-callback: {e}")
        bot.answer_callback_query(call.id, "❌ אירעה שגיאה", show_alert=False)

# ========== דפי אתר ==========
@flask_app.route('/')
def index():
    """דף הבית"""
    try:
        stats = get_system_stats()
        return render_template('index.html', 
                             stats=stats,
                             bot_username=bot.get_me().username)
    except Exception as e:
        logger.error(f"❌ שגיאה בטעינת דף הבית: {e}")
        return "שגיאה בטעינת הדף", 500

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
        return "שגיאה בטעינת סטטיסטיקות", 500

@flask_app.route('/health')
def health_check():
    """בדיקת בריאות המערכת"""
    try:
        # בדיקת חיבור למסד נתונים
        session = Session()
        session.execute("SELECT 1")
        session.close()
        
        return jsonify({
            "status": "healthy",
            "bot_status": "active",
            "bot_token_defined": BOT_TOKEN is not None,
            "database": "available",
            "webhook_configured": True,
            "application_initialized": True
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@flask_app.route('/setwebhook')
def set_webhook_page():
    """הגדרת webhook"""
    try:
        if WEBHOOK_URL:
            bot.remove_webhook()
            bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
            return """
            <h1>✅ Webhook הוגדר בהצלחה!</h1>
            <p>הבוט אמור לענות כעת לפקודות.</p>
            <p>נסה לשלוח /start או /help לבוט בטלגרם.</p>
            <a href="/">חזרה לדף הבית</a> | 
            <a href="/health">🩺 בדיקת בריאות</a>
            """
        else:
            return "WEBHOOK_URL לא מוגדר", 400
    except Exception as e:
        return f"שגיאה: {str(e)}", 500

# ========== אתחול ==========
def initialize_system():
    """אתחול המערכת"""
    try:
        logger.info("🔧 מאתחל מסד נתונים...")
        init_database()
        logger.info("✅ מסד נתונים אותחל")
        
        # הגדר webhook אם יש URL
        if WEBHOOK_URL:
            logger.info(f"🔗 מגדיר webhook ל: {WEBHOOK_URL}")
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
            logger.info("✅ Webhook הוגדר")
        else:
            logger.warning("⚠️ WEBHOOK_URL לא מוגדר - הבוט יפעל בפולינג")
            
    except Exception as e:
        logger.error(f"❌ שגיאה באתחול: {e}")

# ========== הרצה ==========
if __name__ == '__main__':
    # הפעל אתחול בפתיל נפרד
    import time
    threading.Thread(target=initialize_system, daemon=True).start()
    
    # הפעל את שרת Flask
    logger.info(f"🚀 מפעיל שרת Flask על פורט {PORT}")
    flask_app.run(host='0.0.0.0', port=PORT, debug=False)
