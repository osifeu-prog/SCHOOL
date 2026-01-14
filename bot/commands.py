#!/usr/bin/env python3
"""
מודול פקודות הבוט - Crypto-Class
כל הפקודות מומרות לסינכרוניות כדי למנוע בעיות ב-event loops
"""

import logging
import random
import string
from datetime import datetime, timedelta
from database.queries import (
    get_user, register_user, checkin_user, get_balance,
    get_user_referrals, get_top_users, get_level_info,
    get_total_referrals, get_or_create_referral_code,
    get_referred_users, add_tokens, update_level,
    get_system_stats, get_activity_count
)

logger = logging.getLogger(__name__)

# ========== פונקציות עזר ==========

def generate_referral_code(user_id: int, length: int = 8) -> str:
    """יצירת קוד הפניה ייחודי"""
    # בסיס מהמזהה של המשתמש
    base = str(user_id)[-4:] if len(str(user_id)) >= 4 else str(user_id).zfill(4)
    
    # הוסף תווים אקראיים
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(length - 4))
    
    code = f"{base}{random_part}"
    return code[:length]

def calculate_level(tokens: int) -> int:
    """חישוב רמה לפי כמות הטוקנים"""
    if tokens < 10:
        return 1
    elif tokens < 50:
        return 2
    elif tokens < 100:
        return 3
    elif tokens < 200:
        return 4
    elif tokens < 500:
        return 5
    elif tokens < 1000:
        return 6
    elif tokens < 2000:
        return 7
    elif tokens < 5000:
        return 8
    elif tokens < 10000:
        return 9
    else:
        return 10

def get_level_progress(tokens: int) -> tuple:
    """קבלת התקדמות ברמה הנוכחית"""
    level = calculate_level(tokens)
    
    # גבולות רמות
    level_thresholds = [0, 10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
    
    current_level_min = level_thresholds[level - 1]
    next_level_min = level_thresholds[level]
    
    progress = tokens - current_level_min
    total_for_level = next_level_min - current_level_min
    
    return level, progress, total_for_level, next_level_min

# ========== פקודות הבוט ==========

async def start(update, context):
    """פקודת התחלה - רישום/התחברות משתמש"""
    try:
        user = update.effective_user
        logger.info(f"🚀 קבלת /start ממשתמש: {user.id} ({user.first_name})")
        
        # בדוק אם המשתמש קיים
        existing_user = get_user(user.id)
        
        if existing_user:
            # משתמש קיים - הצג הודעת ברוכים השב
            welcome_message = (
                f"🎉 ברוך הבא ל-Crypto-Class! 🚀\n\n"
                f"👋 ברוך השב! כבר רשום במערכת.\n\n"
                f"📋 פקודות זמינות:\n"
                f"• /checkin - צ'ק-אין יומי (מקבל טוקן)\n"
                f"• /balance - בדיקת יתרת טוקנים\n"
                f"• /referral - קוד ההפניה שלך\n"
                f"• /my_referrals - המוזמנים שלך\n"
                f"• /leaderboard - טבלת מובילים\n"
                f"• /level - הרמה והניסיון שלך\n"
                f"• /contact - פניה למנהל המערכת\n"
                f"• /help - עזרה והדרכה\n"
                f"• /website - קישור לאתר המערכת\n\n"
                f"🚀 התחל עם /checkin כדי לצבור טוקנים!"
            )
            await update.message.reply_text(welcome_message)
        else:
            # משתמש חדש - רשום אותו
            referral_code = generate_referral_code(user.id)
            success = register_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                referral_code=referral_code
            )
            
            if success:
                logger.info(f"✅ משתמש נרשם: {user.id} עם קוד הפניה: {referral_code}")
                welcome_message = (
                    f"🎉 ברוך הבא ל-Crypto-Class! 🚀\n\n"
                    f"✅ נרשמת בהצלחה למערכת!\n"
                    f"👤 שם: {user.first_name}\n"
                    f"🆔 מזהה: {user.id}\n"
                    f"📅 תאריך: {datetime.now().strftime('%d/%m/%Y')}\n\n"
                    f"📋 פקודות זמינות:\n"
                    f"• /checkin - צ'ק-אין יומי (מקבל טוקן)\n"
                    f"• /balance - בדיקת יתרת טוקנים\n"
                    f"• /referral - קוד ההפניה שלך\n"
                    f"• /my_referrals - המוזמנים שלך\n"
                    f"• /leaderboard - טבלת מובילים\n"
                    f"• /level - הרמה והניסיון שלך\n"
                    f"• /contact - פניה למנהל המערכת\n"
                    f"• /help - עזרה והדרכה\n\n"
                    f"🚀 התחל עם /checkin כדי לצבור טוקנים!"
                )
                await update.message.reply_text(welcome_message)
            else:
                await update.message.reply_text(
                    "❌ אירעה שגיאה בזמן הרישום\n\n"
                    "אנא נסה שוב מאוחר יותר."
                )
                
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת start: {e}")
        await update.message.reply_text(
            "❌ אירעה שגיאה בזמן הרישום\n\n"
            "אנא נסה שוב מאוחר יותר."
        )

async def checkin(update, context):
    """צ'ק-אין יומי - קבלת טוקן יומי"""
    try:
        user = update.effective_user
        logger.info(f"📅 קבלת /checkin ממשתמש: {user.id}")
        
        # בצע צ'ק-אין
        success, message = checkin_user(user.id)
        
        if success:
            # קבל את היתרה המעודכנת
            balance = get_balance(user.id)
            
            response = (
                f"✅ {message}\n\n"
                f"💰 היתרה המעודכנת שלך: {balance} טוקנים 🪙\n\n"
                f"📈 המשך להתמיד!\n"
                f"🎯 רץ ליעד הרמה הבאה עם /level"
            )
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(f"❌ {message}")
            
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת checkin: {e}")
        await update.message.reply_text("❌ שגיאה. נסה שוב.")

async def balance(update, context):
    """הצגת יתרת הטוקנים של המשתמש"""
    try:
        user = update.effective_user
        logger.info(f"💰 קבלת /balance ממשתמש: {user.id}")
        
        balance = get_balance(user.id)
        
        response = (
            f"💰 היתרה שלך, {user.first_name}:\n"
            f"{balance} טוקנים 🪙\n\n"
        )
        
        # הוסף מידע על רמה
        level, progress, total, next_level = get_level_progress(balance)
        response += (
            f"🏆 רמה: {level}\n"
            f"📊 התקדמות: {progress}/{total} טוקנים\n"
            f"🎯 עד לרמה {level+1}: {next_level - balance} טוקנים\n\n"
            f"💪 המשך לצבור טוקנים עם /checkin"
        )
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת balance: {e}")
        await update.message.reply_text("❌ אירעה שגיאה. נסה שוב מאוחר יותר.")

async def referral(update, context):
    """הצגת קוד ההפניה של המשתמש"""
    try:
        user = update.effective_user
        logger.info(f"📱 קבלת /referral ממשתמש: {user.id}")
        
        # קבל את המשתמש
        db_user = get_user(user.id)
        
        if not db_user:
            await update.message.reply_text("❌ אתה לא רשום במערכת. שלח /start כדי להירשם.")
            return
        
        referral_code = db_user.referral_code
        
        # סטטיסטיקות הפניות
        total_referrals = get_total_referrals(user.id)
        
        response = (
            f"👤 קוד ההפניה שלך, {user.first_name}:\n\n"
            f"📱 קוד: {referral_code}\n\n"
            f"📊 סטטיסטיקות הפניות:\n"
            f"• משתמשים שהזמנת: {total_referrals}\n"
            f"• טוקנים שהרווחת מהפניות: {total_referrals * 10}\n\n"
            f"🎯 איך להזמין חברים:\n"
            f"1. שלח לחבר את הקישור:\n"
            f"https://t.me/{context.bot.username}?start={referral_code}\n"
            f"2. או בקש ממנו לשלוח /start {referral_code}\n"
            f"3. קבל 10 טוקנים על כל חבר שמצטרף!"
        )
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת referral: {e}")
        await update.message.reply_text("❌ אירעה שגיאה. נסה שוב מאוחר יותר.")

async def my_referrals(update, context):
    """הצגת רשימת המוזמנים של המשתמש"""
    try:
        user = update.effective_user
        logger.info(f"👥 קבלת /my_referrals ממשתמש: {user.id}")
        
        # קבל את המוזמנים
        referrals = get_referred_users(user.id)
        total_referrals = get_total_referrals(user.id)
        
        if not referrals:
            response = (
                f"📊 סטטיסטיקות הפניות של {user.first_name}:\n\n"
                f"👥 מוזמנים: 0\n"
                f"💰 טוקנים מהפניות: 0\n\n"
                f"🎯 עדיין לא הזמנת חברים.\n"
                f"📱 השתמש ב-/referral כדי לקבל את קוד ההפניה שלך!"
            )
        else:
            response = (
                f"📊 סטטיסטיקות הפניות של {user.first_name}:\n\n"
                f"👥 מוזמנים: {total_referrals}\n"
                f"💰 טוקנים מהפניות: {total_referrals * 10}\n\n"
                f"📋 רשימת המוזמנים:\n"
            )
            
            for i, ref in enumerate(referrals[:10], 1):  # הגבל ל-10 מוזמנים
                ref_date = ref.created_at.strftime('%d/%m/%Y') if ref.created_at else "תאריך לא ידוע"
                response += f"{i}. {ref.first_name or 'משתמש'} - {ref_date}\n"
            
            if len(referrals) > 10:
                response += f"\n... ועוד {len(referrals) - 10} מוזמנים"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת my_referrals: {e}")
        await update.message.reply_text("❌ אירעה שגיאה. נסה שוב מאוחר יותר.")

async def leaderboard(update, context):
    """טבלת המובילים - המשתמשים עם הכי הרבה טוקנים"""
    try:
        user = update.effective_user
        logger.info(f"🏆 קבלת /leaderboard ממשתמש: {user.id}")
        
        # קבל את המובילים
        top_users = get_top_users(limit=10, order_by='tokens')
        
        if not top_users:
            response = "🏆 טבלת המובילים:\n\nאין עדיין נתונים. היה הראשון שצובר טוקנים! 💪"
        else:
            response = "🏆 טבלת המובילים - Top 10:\n\n"
            
            for i, top_user in enumerate(top_users, 1):
                name = top_user.first_name or top_user.username or f"משתמש {top_user.telegram_id}"
                
                # סימון מיוחד אם זה המשתמש הנוכחי
                if top_user.telegram_id == user.id:
                    response += f"{i}. 👑 {name} - {top_user.tokens} טוקנים\n"
                else:
                    response += f"{i}. {name} - {top_user.tokens} טוקנים\n"
            
            # הוסף את המיקום של המשתמש הנוכחי
            all_users = get_top_users(limit=100, order_by='tokens')
            user_position = None
            
            for i, u in enumerate(all_users, 1):
                if u.telegram_id == user.id:
                    user_position = i
                    break
            
            if user_position:
                user_balance = get_balance(user.id)
                response += f"\n📊 המיקום שלך: #{user_position} עם {user_balance} טוקנים"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת leaderboard: {e}")
        await update.message.reply_text("❌ אירעה שגיאה. נסה שוב מאוחר יותר.")

async def level(update, context):
    """הצגת הרמה וההתקדמות של המשתמש"""
    try:
        user = update.effective_user
        logger.info(f"🏅 קבלת /level ממשתמש: {user.id}")
        
        balance = get_balance(user.id)
        level, progress, total, next_level = get_level_progress(balance)
        
        # סטטיסטיקות נוספות
        total_users = get_system_stats().get('total_users', 0)
        activity_today = get_activity_count()
        
        response = (
            f"🏆 פרופיל של {user.first_name}:\n\n"
            f"💰 טוקנים: {balance}\n"
            f"🏅 רמה: {level}\n"
            f"📊 התקדמות ברמה: {progress}/{total}\n"
            f"🎯 נדרשים עוד {next_level - balance} טוקנים לרמה {level + 1}\n\n"
        )
        
        # הוסף מוטיבציה לפי הרמה
        if level < 3:
            response += "🌱 מתחיל - המשך כך! כל יום צ'ק-אין מקרב אותך לרמה הבאה.\n"
        elif level < 6:
            response += "🚀 מתקדם - עבודה טובה! אתה בדרך להצלחה.\n"
        elif level < 9:
            response += "💎 מנוסה - מעולה! אתה אחד המובילים.\n"
        else:
            response += "👑 אלוף - מדהים! אתה בפסגה.\n"
        
        response += (
            f"\n📈 סטטיסטיקות:\n"
            f"• פעילים היום: {activity_today}\n"
            f"• משתמשים רשומים: {total_users}\n\n"
            f"💪 השתמש ב-/checkin כל יום כדי להתקדם!"
        )
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת level: {e}")
        await update.message.reply_text("❌ אירעה שגיאה. נסה שוב מאוחר יותר.")

async def contact(update, context):
    """הצגת פרטי קשר עם המנהל"""
    try:
        response = (
            "📞 צור קשר עם המנהל:\n\n"
            "👤 אוסיף אונגר\n"
            "מנהל המערכת\n\n"
            "📧 אימייל: osifeu@example.com\n"
            "📱 טלגרם: @osifeu\n\n"
            "💬 ניתן לפנות בנושאים:\n"
            "• תמיכה טכנית\n"
            "• שאלות על המערכת\n"
            "• הצעות לשיפור\n"
            "• דיווח על בעיות\n\n"
            "🕒 זמני תגובה: 24-48 שעות\n\n"
            "✉️ נשמח לעזור!"
        )
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת contact: {e}")
        await update.message.reply_text("❌ אירעה שגיאה. נסה שוב מאוחר יותר.")

async def help_command(update, context):
    """הצגת הודעת עזרה עם כל הפקודות"""
    try:
        response = (
            "🆘 עזרה והדרכה - Crypto-Class\n\n"
            "📚 רשימת הפקודות:\n\n"
            "• /start - הרשמה והתחלת שימוש\n"
            "• /checkin - צ'ק-אין יומי לקבלת טוקן\n"
            "• /balance - הצגת יתרת הטוקנים\n"
            "• /referral - קוד ההפניה שלך\n"
            "• /my_referrals - רשימת המוזמנים שלך\n"
            "• /leaderboard - טבלת המובילים\n"
            "• /level - הרמה וההתקדמות שלך\n"
            "• /contact - פרטי קשר עם המנהל\n"
            "• /help - תפריט זה\n\n"
            "🎯 איך לעבוד עם המערכת:\n"
            "1. שלח /start כדי להירשם\n"
            "2. שלח /checkin כל יום לקבלת טוקן\n"
            "3. הזמן חברים עם /referral\n"
            "4. עקוב אחר ההתקדמות עם /level\n"
            "5. תחרה עם אחרים ב-/leaderboard\n\n"
            "💰 מערכת הטוקנים:\n"
            "• צ'ק-אין יומי: 1 טוקן\n"
            "• הזמנת חבר: 10 טוקנים\n"
            "• משימות מיוחדות: טוקנים נוספים\n\n"
            "❓ בעיות טכניות? שלח /contact"
        )
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת help: {e}")
        await update.message.reply_text("❌ אירעה שגיאה. נסה שוב מאוחר יותר.")

async def website(update, context):
    """שליחת קישור לאתר המערכת"""
    try:
        # URL האתר מהסביבה או ברירת מחדל
        web_url = "https://school-production-4d9d.up.railway.app"
        
        response = (
            "🌐 אתר המערכת - Crypto-Class\n\n"
            f"🔗 קישור: {web_url}\n\n"
            "📊 באתר תוכל למצוא:\n"
            "• סטטיסטיקות מערכת\n"
            "• טבלאות מובילים\n"
            "• דשבורד ניהול למורים\n"
            "• בדיקת בריאות המערכת\n\n"
            "💻 גש לאתר למידע נוסף!"
        )
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת website: {e}")
        await update.message.reply_text("❌ אירעה שגיאה. נסה שוב מאוחר יותר.")
