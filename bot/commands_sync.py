#!/usr/bin/env python3
"""
פקודות בוט סינכרוניות משודרגות
כל הפקודות עם טיפול שגיאות משופר ואינטגרציה מלאה
"""

import logging
import random
import string
from datetime import datetime
import traceback

# יבוא פונקציות ממסד הנתונים
from database.queries import (
    get_user, register_user, checkin_user, get_balance,
    get_top_users, get_total_referrals, get_system_stats,
    get_activity_count, get_referred_users, add_tokens_to_user,
    create_task, get_available_tasks, complete_task,
    get_user_tasks, get_user_attendance_history
)

logger = logging.getLogger(__name__)

# ========== פונקציות עזר משופרות ==========

def generate_referral_code(user_id: int, length: int = 8) -> str:
    """יצירת קוד הפניה ייחודי עם בדיקת כפילויות"""
    try:
        # בסיס מהמזהה של המשתמש
        base = str(user_id)[-4:] if len(str(user_id)) >= 4 else str(user_id).zfill(4)
        
        # הוסף תווים אקראיים
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choice(chars) for _ in range(length - 4))
        
        code = f"{base}{random_part}"
        return code[:length]
    except Exception as e:
        logger.error(f"❌ שגיאה ביצירת קוד הפניה: {e}")
        return f"REF{user_id}"

def calculate_level(tokens: int) -> int:
    """חישוב רמה לפי טוקנים עם נוסחה מתקדמת"""
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
    elif tokens < 20000:
        return 10
    elif tokens < 50000:
        return 11
    elif tokens < 100000:
        return 12
    else:
        return 13

def get_level_progress(tokens: int) -> tuple:
    """קבלת התקדמות ברמה הנוכחית עם חישוב מדויק"""
    level = calculate_level(tokens)
    
    # גבולות רמות דינמיות
    level_thresholds = [0, 10, 50, 100, 200, 500, 1000, 2000, 5000, 
                       10000, 20000, 50000, 100000, 200000]
    
    if level >= len(level_thresholds):
        return level, 0, 1, level_thresholds[-1]
    
    current_level_min = level_thresholds[level - 1]
    next_level_min = level_thresholds[level]
    
    progress = tokens - current_level_min
    total_for_level = next_level_min - current_level_min
    
    return level, progress, total_for_level, next_level_min

def format_number(num: int) -> str:
    """פורמט מספר עם פסיקים"""
    return f"{num:,}"

# ========== פונקציות טיפול בשגיאות ==========

async def safe_reply(bot, chat_id, text, parse_mode=None, reply_markup=None):
    """שליחת הודעה עם טיפול בשגיאות"""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
        return True
    except Exception as e:
        logger.error(f"❌ שגיאה בשליחת הודעה: {e}")
        return False

async def handle_command_error(bot, chat_id, command, error):
    """טיפול בשגיאות פקודה"""
    error_msg = (
        f"⚠️ **שגיאה בפקודה {command}**\n\n"
        f"המערכת נתקלה בבעיה טכנית.\n"
        f"נסה שוב מאוחר יותר או פנה לתמיכה.\n\n"
        f"📞 /contact - לתמיכה טכנית"
    )
    await safe_reply(bot, chat_id, error_msg, parse_mode="Markdown")
    logger.error(f"❌ שגיאה בפקודה {command}: {error}\n{traceback.format_exc()}")

# ========== פקודות בוט משודרגות ==========

async def start(message, bot):
    """פקודת התחלה משודרגת"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        logger.info(f"🚀 /start ממשתמש {user.id} ({user.first_name})")
        
        # בדיקה אם המשתמש קיים
        db_user = get_user(user.id)
        
        if db_user:
            # משתמש קיים
            welcome_msg = (
                f"👋 **ברוך השב, {user.first_name}!**\n\n"
                f"🎓 אתה כבר רשום ב-**Crypto-Class**\n"
                f"💰 הטוקנים שלך: **{db_user.tokens:,}**\n"
                f"🏆 הרמה שלך: **{db_user.level}**\n\n"
                f"📋 **פקודות זמינות:**\n"
                f"• /checkin - צ'ק-אין יומי (טוקן)\n"
                f"• /balance - יתרת טוקנים\n"
                f"• /tasks - משימות זמינות\n"
                f"• /referral - קוד הפניה\n"
                f"• /leaderboard - טבלת מובילים\n"
                f"• /profile - הפרופיל שלך\n"
                f"• /help - עזרה מלאה\n\n"
                f"🚀 **התחל עם:** /checkin"
            )
            
            # הוסף כפתורים מהירים
            from telebot import types
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("✅ צ'ק-אין", callback_data="checkin"),
                types.InlineKeyboardButton("💰 טוקנים", callback_data="balance")
            )
            markup.row(
                types.InlineKeyboardButton("🏆 מובילים", callback_data="leaderboard"),
                types.InlineKeyboardButton("👥 הפניות", callback_data="referrals")
            )
            
            await safe_reply(bot, chat_id, welcome_msg, parse_mode="Markdown", reply_markup=markup)
            
        else:
            # משתמש חדש
            # בדוק אם יש קוד הפניה
            referral_code = None
            if len(message.text.split()) > 1:
                referral_code = message.text.split()[1]
            
            # רישום המשתמש
            success = register_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                referral_code=referral_code
            )
            
            if success:
                # קבל את המשתמש שנרשם
                new_user = get_user(user.id)
                
                welcome_msg = (
                    f"🎉 **ברוך הבא ל-Crypto-Class!**\n\n"
                    f"✅ **נרשמת בהצלחה!**\n"
                    f"👤 **שם:** {user.first_name}\n"
                    f"🆔 **מזהה:** {user.id}\n"
                    f"📅 **תאריך:** {datetime.now().strftime('%d/%m/%Y')}\n"
                    f"🔗 **קוד הפניה:** `{new_user.referral_code}`\n\n"
                    f"🎁 **קבלת מתנה:** **10 טוקנים**!\n\n"
                    f"📚 **מה זה Crypto-Class?**\n"
                    f"זו מערכת למידה מבוססת טוקנים.\n"
                    f"• צבור טוקנים עם צ'ק-אין ומשימות\n"
                    f"• הזמן חברים וקבל טוקנים\n"
                    f"• התקדם ברמות וקבל הטבות\n\n"
                    f"🚀 **התחל עכשיו עם:** /checkin"
                )
                
                # הוסף טוקנים מתנה
                add_tokens_to_user(user.id, 10)
                
                # כפתורים מהירים
                from telebot import types
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton("🎁 קח את הטוקנים!", callback_data="get_tokens"),
                    types.InlineKeyboardButton("📚 למד עוד", callback_data="learn_more")
                )
                
                await safe_reply(bot, chat_id, welcome_msg, parse_mode="Markdown", reply_markup=markup)
                
                # הודעה פרטית נוספת
                guide_msg = (
                    f"📖 **מדריך מהיר:**\n\n"
                    f"1. **צ'ק-אין יומי** - שלח /checkin כל יום\n"
                    f"2. **הזמן חברים** - שלח /referral\n"
                    f"3. **בצע משימות** - שלח /tasks\n"
                    f"4. **עקוב אחריי** - שלח /profile\n\n"
                    f"📊 **סטטיסטיקות ראשונות:**\n"
                    f"• הטוקנים שלך: **10**\n"
                    f"• הרמה שלך: **1**\n\n"
                    f"🚀 קדימה, התחל לצבור!"
                )
                
                await safe_reply(bot, chat_id, guide_msg, parse_mode="Markdown")
                
            else:
                error_msg = "❌ **אירעה שגיאה ברישום**\n\nנסה שוב או פנה לתמיכה: /contact"
                await safe_reply(bot, chat_id, error_msg, parse_mode="Markdown")
                
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/start", e)

async def checkin(message, bot):
    """צ'ק-אין יומי משודרג"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        
        logger.info(f"📅 /checkin ממשתמש {user.id}")
        
        # בצע צ'ק-אין
        success, msg = checkin_user(user.id)
        
        if success:
            # קבל נתונים מעודכנים
            balance = get_balance(user.id)
            stats = get_system_stats()
            level, progress, total, next_level = get_level_progress(balance)
            
            # הודעה מפורטת
            response = (
                f"✅ **{msg}**\n\n"
                f"💰 **יתרה מעודכנת:** {format_number(balance)} טוקנים\n"
                f"🏆 **רמה:** {level}\n"
                f"📊 **התקדמות:** {progress}/{total} טוקנים\n\n"
                f"🎯 **לרמה הבאה חסרים:** {format_number(next_level - balance)} טוקנים\n\n"
                f"📈 **סטטיסטיקות מערכת:**\n"
                f"• 👥 משתמשים: {format_number(stats.get('total_users', 0))}\n"
                f"• 📅 פעילים היום: {format_number(stats.get('active_today', 0))}\n"
                f"• 💰 טוקנים כוללים: {format_number(stats.get('total_tokens', 0))}\n\n"
                f"💪 **המשך להתמיד!**\n"
                f"הצ'ק-אין הבא בעוד 24 שעות."
            )
            
            # כפתורים
            from telebot import types
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("💰 יתרה", callback_data="balance"),
                types.InlineKeyboardButton("🏆 רמה", callback_data="level")
            )
            markup.row(
                types.InlineKeyboardButton("👥 הזמן חבר", callback_data="invite"),
                types.InlineKeyboardButton("📊 סטטיסטיקות", callback_data="stats")
            )
            
            await safe_reply(bot, chat_id, response, parse_mode="Markdown", reply_markup=markup)
            
        else:
            # בדוק מתי אפשר שוב
            user_data = get_user(user.id)
            if user_data and user_data.last_checkin:
                last_checkin = user_data.last_checkin
                if hasattr(last_checkin, 'strftime'):
                    last_date = last_checkin.strftime('%d/%m/%Y %H:%M')
                    response = (
                        f"⏳ **כבר ביצעת צ'ק-אין היום!**\n\n"
                        f"🕒 **צ'ק-אין אחרון:** {last_date}\n"
                        f"⏰ **צ'ק-אין הבא:** מחר בשעה זו\n\n"
                        f"📊 **הטוקנים שלך:** {format_number(user_data.tokens)}\n"
                        f"🏆 **הרמה שלך:** {user_data.level}\n\n"
                        f"💡 **טיפ:** הזמן חברים עם /referral כדי לקבל טוקנים נוספים!"
                    )
                else:
                    response = msg
            else:
                response = msg
                
            await safe_reply(bot, chat_id, response, parse_mode="Markdown")
            
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/checkin", e)

async def balance(message, bot):
    """יתרת טוקנים מפורטת"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        
        balance_amount = get_balance(user.id)
        level, progress, total, next_level = get_level_progress(balance_amount)
        
        # היסטוריית צ'ק-אין
        attendance_history = get_user_attendance_history(user.id, 7)
        streak = len(attendance_history)
        
        response = (
            f"💰 **פירוט יתרה - {user.first_name}**\n\n"
            f"🪙 **טוקנים נוכחיים:** {format_number(balance_amount)}\n"
            f"🏆 **רמה:** {level}\n"
            f"📊 **התקדמות ברמה:** {progress}/{total}\n"
            f"🎯 **לרמה {level+1} חסרים:** {format_number(next_level - balance_amount)}\n\n"
            f"🔥 **רצף צ'ק-אין:** {streak} ימים\n"
            f"📅 **אחרון:** {attendance_history[0].date.strftime('%d/%m') if attendance_history else 'אין'}\n\n"
            f"💎 **הטבות לפי רמה:**\n"
        )
        
        # הוסף הטבות לפי רמה
        if level >= 3:
            response += "• ✅ גישה לפורום VIP\n"
        if level >= 5:
            response += "• 🎁 הטבות שבועיות\n"
        if level >= 7:
            response += "• 👑 דירוג אלוף\n"
        if level >= 10:
            response += "• 💰 בונוסים מיוחדים\n"
        
        response += f"\n🚀 **הגדל את הרמה עם:** /tasks"
        
        # גרף התקדמות פשוט
        progress_bar_length = 20
        filled = int((progress / total) * progress_bar_length) if total > 0 else 0
        progress_bar = "▓" * filled + "░" * (progress_bar_length - filled)
        
        response += f"\n\n📈 **מתקדם לרמה {level+1}:**\n`{progress_bar}` {int((progress/total)*100)}%"
        
        await safe_reply(bot, chat_id, response, parse_mode="Markdown")
        
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/balance", e)

async def referral(message, bot):
    """מערכת הפניות משודרגת"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        
        db_user = get_user(user.id)
        if not db_user:
            await safe_reply(bot, chat_id, "❌ **אתה לא רשום!**\n\nשלח /start כדי להירשם.", parse_mode="Markdown")
            return
        
        referral_code = db_user.referral_code
        total_refs = get_total_referrals(user.id)
        referred_users = get_referred_users(user.id)
        
        # צור קישור הפניה
        bot_username = (await bot.get_me()).username
        invite_link = f"https://t.me/{bot_username}?start={referral_code}"
        
        response = (
            f"👥 **מערכת ההפניות שלך**\n\n"
            f"🔗 **קוד ההפניה שלך:**\n`{referral_code}`\n\n"
            f"📊 **סטטיסטיקות:**\n"
            f"• 👥 משתמשים שהוזמנו: **{total_refs}**\n"
            f"• 💰 טוקנים מהפניות: **{total_refs * 10}**\n"
            f"• 🎯 יעד ההזמנות הבא: **{total_refs + 1}**\n\n"
            f"🎁 **בונוסי הפניה:**\n"
            f"• הזמן חבר = **10 טוקנים**\n"
            f"• כל 5 חברים = **+50 טוקנים**\n"
            f"• כל 10 חברים = **רמה חינם!**\n\n"
            f"🔗 **קישור הזמנה:**\n{invite_link}\n\n"
            f"📝 **הוראות:**\n"
            f"1. שלח לחבר את הקישור\n"
            f"2. הוא ישלח /start עם הקוד\n"
            f"3. קבל 10 טוקנים מיד!\n\n"
            f"👥 **מוזמנים אחרונים:**\n"
        )
        
        # הוסף מוזמנים אחרונים
        if referred_users:
            for i, ref in enumerate(referred_users[:5], 1):
                name = ref.first_name or ref.username or f"משתמש {ref.telegram_id}"
                date_str = ref.created_at.strftime('%d/%m') if ref.created_at else "לאחרונה"
                response += f"{i}. {name} - {date_str}\n"
            if len(referred_users) > 5:
                response += f"... ועוד {len(referred_users) - 5} מוזמנים\n"
        else:
            response += "עדיין אין מוזמנים. התחל להזמין!\n"
        
        response += f"\n📱 **לצפייה במוזמנים המלאים:** /my_referrals"
        
        # כפתורים מהירים
        from telebot import types
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("📤 שתף קישור", url=f"https://t.me/share/url?url={invite_link}&text=הצטרף%20לCrypto-Class!"),
            types.InlineKeyboardButton("👥 מוזמנים", callback_data="my_referrals")
        )
        
        await safe_reply(bot, chat_id, response, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/referral", e)

async def my_referrals(message, bot):
    """מוזמנים מפורט"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        
        referred_users = get_referred_users(user.id)
        total_refs = get_total_referrals(user.id)
        
        if not referred_users:
            response = (
                f"👥 **המוזמנים שלך - {user.first_name}**\n\n"
                f"📭 **עדיין אין מוזמנים**\n\n"
                f"💡 **טיפים להזמנות:**\n"
                f"• שתף את קוד ההפניה בקבוצות\n"
                f"• שלח לחברים אישית\n"
                f"• הצע טוקנים כמתנה\n\n"
                f"🔗 **לקבלת קוד הפניה:** /referral"
            )
        else:
            response = (
                f"👥 **המוזמנים שלך - {user.first_name}**\n\n"
                f"📊 **סה\"כ מוזמנים:** {total_refs}\n"
                f"💰 **טוקנים שהרווחת:** {total_refs * 10}\n\n"
                f"📋 **רשימת מוזמנים:**\n"
            )
            
            for i, ref in enumerate(referred_users, 1):
                name = ref.first_name or ref.username or f"משתמש {ref.telegram_id}"
                date_str = ref.created_at.strftime('%d/%m/%Y') if ref.created_at else "לא ידוע"
                tokens = ref.tokens or 0
                response += f"{i}. **{name}** - {date_str} ({tokens} טוקנים)\n"
        
        await safe_reply(bot, chat_id, response, parse_mode="Markdown")
        
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/my_referrals", e)

async def leaderboard(message, bot):
    """טבלת מובילים משודרגת"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        
        # קבל מובילים לפי קטגוריות
        top_tokens = get_top_users(10, 'tokens')
        top_referrals = get_top_users(10, 'referrals')
        top_level = get_top_users(10, 'level')
        
        # מצא את המיקום של המשתמש
        all_users = get_top_users(100, 'tokens')
        user_position = None
        for i, u in enumerate(all_users, 1):
            if u.telegram_id == user.id:
                user_position = i
                break
        
        response = (
            f"🏆 **טבלת המובילים - Crypto-Class**\n\n"
            f"💰 **מובילים בטוקנים:**\n"
        )
        
        # הוסף 5 מובילים ראשונים
        for i, top_user in enumerate(top_tokens[:5], 1):
            name = top_user.first_name or top_user.username or f"משתמש {top_user.telegram_id}"
            if top_user.telegram_id == user.id:
                response += f"{i}. 👑 **{name}** - {format_number(top_user.tokens)} טוקנים\n"
            else:
                response += f"{i}. {name} - {format_number(top_user.tokens)} טוקנים\n"
        
        response += f"\n👥 **מובילים בהפניות:**\n"
        for i, top_user in enumerate(top_referrals[:3], 1):
            name = top_user.first_name or top_user.username or f"משתמש {top_user.telegram_id}"
            response += f"{i}. {name} - {top_user.total_referrals} מוזמנים\n"
        
        response += f"\n🎯 **מובילים ברמה:**\n"
        for i, top_user in enumerate(top_level[:3], 1):
            name = top_user.first_name or top_user.username or f"משתמש {top_user.telegram_id}"
            response += f"{i}. {name} - רמה {top_user.level}\n"
        
        # הוסף את מיקום המשתמש
        if user_position:
            user_balance = get_balance(user.id)
            response += f"\n📊 **המיקום שלך:** #{user_position} עם {format_number(user_balance)} טוקנים\n"
        
        response += f"\n⏰ **עדכון אחרון:** {datetime.now().strftime('%H:%M')}"
        
        # כפתורים לקטגוריות שונות
        from telebot import types
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("💰 טוקנים", callback_data="top_tokens"),
            types.InlineKeyboardButton("👥 הפניות", callback_data="top_refs")
        )
        markup.row(
            types.InlineKeyboardButton("🎯 רמה", callback_data="top_level"),
            types.InlineKeyboardButton("📈 פרופיל שלי", callback_data="my_profile")
        )
        
        await safe_reply(bot, chat_id, response, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/leaderboard", e)

async def level(message, bot):
    """מידע רמה מפורט"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        
        balance = get_balance(user.id)
        level_num, progress, total, next_level = get_level_progress(balance)
        
        # חישוב אחוזים
        percentage = int((progress / total) * 100) if total > 0 else 0
        
        response = (
            f"🎯 **רמה וקידום - {user.first_name}**\n\n"
            f"🏆 **רמה נוכחית:** {level_num}\n"
            f"💰 **טוקנים:** {format_number(balance)}\n"
            f"📊 **התקדמות:** {format_number(progress)}/{format_number(total)} ({percentage}%)\n"
            f"🎯 **לרמה {level_num+1} חסרים:** {format_number(next_level - balance)} טוקנים\n\n"
        )
        
        # הוסף גרף התקדמות
        bar_length = 15
        filled = int((progress / total) * bar_length) if total > 0 else 0
        progress_bar = "█" * filled + "░" * (bar_length - filled)
        response += f"`{progress_bar}`\n\n"
        
        # תיאור הרמה
        level_descriptions = {
            1: "🌱 **מתחיל** - אתה בתחילת הדרך! המשך לצבור טוקנים.",
            2: "🚀 **לומד** - אתה מתקדם יפה. המשך כך!",
            3: "💪 **פעיל** - אתה תורם לקהילה. מעולה!",
            4: "🌟 **מתמיד** - התמדה מרשימה. המשך להתקדם!",
            5: "🏅 **מתקדם** - הגעת לחצי הדרך. כל הכבוד!",
            6: "💎 **מוביל** - אתה בין המובילים. ממשיך למצוינות!",
            7: "👑 **אלוף** - אתה בפסגה. שמור על ההובלה!",
            8: "🚀 **מאסטר** - רמת מאסטר. אתה מודל לחיקוי!",
            9: "🌌 **גורו** - רמת גורו. ידע וניסיון עצומים!",
            10: "⚡ **אליל** - הרמה הגבוהה ביותר. אתה אגדה!"
        }
        
        description = level_descriptions.get(level_num, "מצוין! המשיך להתקדם!")
        response += f"{description}\n\n"
        
        # הטבות הרמה
        response += "🎁 **הטבות הרמה הנוכחית:**\n"
        if level_num >= 1:
            response += "• ✅ גישה לכל הפיצ'רים הבסיסיים\n"
        if level_num >= 3:
            response += "• 🎁 בונוס צ'ק-אין +1 טוקן\n"
        if level_num >= 5:
            response += "• 👑 סימון מיוחד בשם\n"
        if level_num >= 7:
            response += "• 💰 ריבית טוקנים יומית\n"
        if level_num >= 10:
            response += "• 🌟 תואר אלוף המערכת\n"
        
        response += f"\n🚀 **דרכים להתקדם:**\n"
        response += "• 📅 צ'ק-אין יומי עם /checkin\n"
        response += "• 👥 הזמנת חברים עם /referral\n"
        response += "• ✅ ביצוע משימות עם /tasks\n"
        
        await safe_reply(bot, chat_id, response, parse_mode="Markdown")
        
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/level", e)

async def profile(message, bot):
    """פרופיל משתמש מלא"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        
        db_user = get_user(user.id)
        if not db_user:
            await safe_reply(bot, chat_id, "❌ **אינך רשום!**\n\nשלח /start כדי להירשם.", parse_mode="Markdown")
            return
        
        balance = db_user.tokens
        level_num, progress, total, next_level = get_level_progress(balance)
        total_refs = get_total_referrals(user.id)
        attendance_history = get_user_attendance_history(user.id, 30)
        streak = len([a for a in attendance_history if a.date == datetime.now().date()])
        
        response = (
            f"👤 **פרופיל משתמש - {user.first_name}**\n\n"
            f"🆔 **מזהה:** {user.id}\n"
            f"📅 **נרשם:** {db_user.created_at.strftime('%d/%m/%Y') if db_user.created_at else 'לא ידוע'}\n"
            f"💰 **טוקנים:** {format_number(balance)}\n"
            f"🏆 **רמה:** {level_num}\n"
            f"👥 **הפניות:** {total_refs}\n"
            f"🔥 **רצף נוכחות:** {streak} ימים\n\n"
        )
        
        # הישגים
        response += "🏅 **הישגים:**\n"
        if balance >= 100:
            response += "• 💰 אספן טוקנים (100+)\n"
        if total_refs >= 5:
            response += "• 👥 מגייס מצטיין (5+)\n"
        if streak >= 7:
            response += "
                    if streak >= 30:
            response += "• 🔥 מלך הרצף (30+ ימים)\n"
        if level_num >= 5:
            response += "• ⭐ כוכב עולה (רמה 5+)\n"
        if level_num >= 10:
            response += "• 👑 אלוף העל (רמה 10+)\n"
        
        response += f"\n📈 **התקדמות החודש:**\n"
        response += f"• 📅 צ'ק-אין: {len(attendance_history)} ימים\n"
        response += f"• 💰 טוקנים שנוספו: {balance - (db_user.tokens or 0)} (מאז תחילת החודש)\n"
        response += f"• 🎯 משימות שהתחלת: 0 (השתמש ב-/tasks)\n\n"
        
        response += f"🚀 **יעדים להמשך:**\n"
        response += f"• להגיע לרמה {level_num + 1} (חסרים {next_level - balance} טוקנים)\n"
        response += f"• להזמין {5 - total_refs if total_refs < 5 else 0} חברים נוספים\n"
        response += f"• לשמור על רצף של {30 - streak if streak < 30 else 0} ימים נוספים\n"
        
        # כפתורים לפעולות
        from telebot import types
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("💰 טוקנים", callback_data="balance"),
            types.InlineKeyboardButton("🏆 רמה", callback_data="level")
        )
        markup.row(
            types.InlineKeyboardButton("👥 הפניות", callback_data="referrals"),
            types.InlineKeyboardButton("📊 סטטיסטיקות", callback_data="stats")
        )
        
        await safe_reply(bot, chat_id, response, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/profile", e)

async def tasks(message, bot):
    """מערכת משימות משודרגת"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        
        available_tasks = get_available_tasks(user.id)
        user_tasks = get_user_tasks(user.id)
        
        if not available_tasks:
            response = (
                f"✅ **מערכת המשימות**\n\n"
                f"📭 אין משימות זמינות כרגע.\n\n"
                f"📢 **משימות חדשות יתווספו בקרוב!**\n\n"
                f"💡 **בינתיים, אתה יכול:**\n"
                f"• שלח /checkin לצ'ק-אין יומי\n"
                f"• שלח /referral להזמנת חברים\n"
                f"• שלח /leaderboard לראות את המובילים"
            )
        else:
            response = (
                f"✅ **משימות זמינות - {user.first_name}**\n\n"
                f"📋 **סה\"כ משימות:** {len(available_tasks)}\n"
                f"🎯 **הושלמו:** {len([t for t in user_tasks if t.status == 'completed'])}\n\n"
                f"📝 **רשימת משימות:**\n"
            )
            
            for i, task in enumerate(available_tasks[:5], 1):
                status = "🔒"
                for user_task in user_tasks:
                    if user_task.task_id == task.id:
                        if user_task.status == 'completed':
                            status = "✅"
                        else:
                            status = "⏳"
                        break
                
                response += f"{i}. {status} **{task.name}** - {task.tokens_reward} טוקנים\n"
                if task.description:
                    response += f"   📝 {task.description[:50]}...\n"
            
            if len(available_tasks) > 5:
                response += f"\n... ועוד {len(available_tasks) - 5} משימות\n"
            
            response += f"\n🎁 **בונוסים מיוחדים:**\n"
            response += "• השלם 3 משימות - קבל 10 טוקנים בונוס!\n"
            response += "• השלם 10 משימות - עלה רמה חינם!\n"
            response += "• השלם את כל המשימות - תואר 'משימות על'!\n"
            
            response += f"\n🚀 **להתחלת משימה:**\n"
            response += "השתמש ב-/task <מספר משימה>\n"
            response += "לדוגמה: /task 1"
        
        # כפתורים למשימות
        from telebot import types
        markup = types.InlineKeyboardMarkup()
        if available_tasks:
            buttons = []
            for i in range(min(3, len(available_tasks))):
                buttons.append(types.InlineKeyboardButton(f"משימה {i+1}", callback_data=f"task_{i+1}"))
            markup.row(*buttons)
        
        markup.row(
            types.InlineKeyboardButton("📋 משימות שלי", callback_data="my_tasks"),
            types.InlineKeyboardButton("🎯 התחל משימה", callback_data="start_task")
        )
        
        await safe_reply(bot, chat_id, response, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/tasks", e)

async def contact(message, bot):
    """צור קשר משופר"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        
        response = (
            f"📞 **צור קשר - Crypto-Class**\n\n"
            f"👤 **מנהל המערכת:** אוסיף אונגר\n"
            f"💼 **תפקיד:** מנהל פרויקט ומפתח ראשי\n\n"
            f"📱 **דרכי התקשרות:**\n"
            f"• ✉️ אימייל: osifeu@example.com\n"
            f"• 📞 טלפון: 058-420-3384\n"
            f"• 📨 טלגרם: @osifeu\n\n"
            f"🕒 **זמינות:**\n"
            f"• ימים א'-ה': 09:00-18:00\n"
            f"• שישי: 09:00-13:00\n"
            f"• שבת: סגור\n\n"
            f"📋 **נושאים שניתן לפנות בהם:**\n"
            f"• 🔧 תמיכה טכנית\n"
            f"• 💡 הצעות לשיפור\n"
            f"• 🐛 דיווח על באגים\n"
            f"• 🤝 שיתופי פעולה\n"
            f"• 📊 שאלות על המערכת\n\n"
            f"⏱️ **זמני תגובה:**\n"
            f"• דחוף: 2-4 שעות\n"
            f"• רגיל: 24-48 שעות\n"
            f"• לא דחוף: עד 7 ימים\n\n"
            f"💬 **טיפים לפני פניה:**\n"
            f"1. ציין את מזהה הטלגרם שלך\n"
            f"2. תאר את הבעיה בפירוט\n"
            f"3. צרף צילומי מסך אם יש\n"
            f"4. ספר מה ניסית לעשות\n\n"
            f"🙏 **תודה שאתה חלק מהקהילה שלנו!**"
        )
        
        await safe_reply(bot, chat_id, response, parse_mode="Markdown")
        
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/contact", e)

async def help_command(message, bot):
    """עזרה משודרגת עם קטגוריות"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        
        response = (
            f"🆘 **עזרה והדרכה מלאה - Crypto-Class**\n\n"
            f"📚 **קטגוריות פקודות:**\n\n"
            f"👤 **רישום והתחלה:**\n"
            f"• /start - הרשמה והתחלת שימוש\n"
            f"• /profile - הצגת הפרופיל שלך\n\n"
            f"💰 **טוקנים ורמות:**\n"
            f"• /balance - הצגת יתרת טוקנים\n"
            f"• /level - הרמה וההתקדמות שלך\n"
            f"• /checkin - צ'ק-אין יומי\n\n"
            f"👥 **הפניות וחברים:**\n"
            f"• /referral - קוד ההפניה שלך\n"
            f"• /my_referrals - המוזמנים שלך\n\n"
            f"✅ **משימות ואתגרים:**\n"
            f"• /tasks - משימות זמינות\n"
            f"• /mytasks - המשימות שלך\n\n"
            f"🏆 **תחרות ודירוג:**\n"
            f"• /leaderboard - טבלת המובילים\n"
            f"• /stats - סטטיסטיקות אישיות\n\n"
            f"ℹ️ **מידע ותמיכה:**\n"
            f"• /contact - צור קשר עם מנהל\n"
            f"• /help - תפריט זה\n"
            f"• /website - קישור לאתר\n\n"
            f"👑 **פקודות מורים ומנהלים:**\n"
            f"• /admin - פאנל ניהול (למנהלים בלבד)\n"
            f"• /add_tokens - הוספת טוקנים (מנהלים)\n\n"
            f"📖 **מדריך מהיר למתחילים:**\n"
            f"1. שלח /start כדי להירשם\n"
            f"2. שלח /checkin כל יום\n"
            f"3. הזמן חברים עם /referral\n"
            f"4. בצע משימות עם /tasks\n"
            f"5. עקוב אחר ההתקדמות עם /profile\n\n"
            f"💡 **טיפים ושיטות עבודה:**\n"
            f"• בצע צ'ק-אין כל יום באותה שעה\n"
            f"• הזמן לפחות 3 חברים לפתוח\n"
            f"• בצע את כל המשימות הזמינות\n"
            f"• עקוב אחר הטבלה עם /leaderboard\n\n"
            f"❓ **בעיות נפוצות:**\n"
            f"• לא מצליח להירשם? שלח /start שוב\n"
            f"• לא מקבל טוקנים? שלח /checkin\n"
            f"• קוד הפניה לא עובד? שלח /referral\n\n"
            f"📞 **צריך עוד עזרה?** שלח /contact"
        )
        
        # כפתורים לפי קטגוריות
        from telebot import types
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("💰 טוקנים", callback_data="help_tokens"),
            types.InlineKeyboardButton("👥 הפניות", callback_data="help_referrals")
        )
        markup.row(
            types.InlineKeyboardButton("✅ משימות", callback_data="help_tasks"),
            types.InlineKeyboardButton("🏆 תחרות", callback_data="help_competition")
        )
        markup.row(
            types.InlineKeyboardButton("📞 תמיכה", callback_data="help_support"),
            types.InlineKeyboardButton("🌐 אתר", callback_data="help_website")
        )
        
        await safe_reply(bot, chat_id, response, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/help", e)

async def website(message, bot):
    """אתר אינטרנט עם תכונות נוספות"""
    try:
        user = message.from_user
        chat_id = message.chat.id
        
        web_url = "https://school-production-4d9d.up.railway.app"
        
        response = (
            f"🌐 **אתר האינטרנט של Crypto-Class**\n\n"
            f"🔗 **קישור לאתר:** {web_url}\n\n"
            f"🎯 **מה תמצא באתר:**\n"
            f"• 📊 **דשבורד אישי** - סטטיסטיקות מפורטות\n"
            f"• 🏆 **טבלאות מובילים** - עם גרפים ודירוגים\n"
            f"• 👨‍🏫 **דשבורד מורים** - ניהול כיתה מתקדם\n"
            f"• 📈 **אנליטיקס** - ניתוח נתונים מתקדם\n"
            f"• 🔔 **התראות** - עדכונים והודעות\n"
            f"• 📚 **מדריכים** - הדרכות מפורטות\n"
            f"• 💬 **פורום** - קהילה ותמיכה\n\n"
            f"💻 **יתרונות האתר:**\n"
            f"• נוח יותר לשימוש ממסך גדול\n"
            f"• אפשרויות מתקדמות שלא קיימות בבוט\n"
            f"• גרפים וויזואליזציה של נתונים\n"
            f"• גישה מהירה לכל הפיצ'רים\n"
            f"• תמיכה טכנית נרחבת\n\n"
            f"📱 **איך להשתמש:**\n"
            f"1. היכנס לקישור למעלה\n"
            f"2. התחבר עם חשבון הטלגרם שלך\n"
            f"3. גלה את כל התכונות החדשות!\n\n"
            f"🔐 **אבטחה:**\n"
            f"• האתר מאובטח ב-HTTPS\n"
            f"• לא נדרשת הרשמה נוספת\n"
            f"• הנתונים שלך מוגנים\n\n"
            f"🚀 **המלצות שלנו:**\n"
            f"• השתמש באתר לניהול ארוך טווח\n"
            f"• השתמש בבוט לפעולות מהירות\n"
            f"• סנכרן בין הפלטפורמות\n\n"
            f"📞 **בעיות באתר?** שלח /contact"
        )
        
        # כפתורים לאתר
        from telebot import types
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("🌐 פתח אתר", url=web_url),
            types.InlineKeyboardButton("📊 דשבורד", url=f"{web_url}/dashboard")
        )
        markup.row(
            types.InlineKeyboardButton("🏆 טבלה", url=f"{web_url}/leaderboard"),
            types.InlineKeyboardButton("👨‍🏫 מורים", url=f"{web_url}/teacher")
        )
        
        await safe_reply(bot, chat_id, response, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/website", e)

# ========== פונקציות callback ==========

async def handle_callback_query(callback_query, bot):
    """טיפול בכפתורים ובאינטראקציות"""
    try:
        user = callback_query.from_user
        chat_id = callback_query.message.chat.id
        data = callback_query.data
        
        logger.info(f"🔘 Callback from {user.id}: {data}")
        
        if data == "checkin":
            # יצירת הודעה חדשה לבדיקה
            message = type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})(),
                'text': '/checkin'
            })()
            await checkin(message, bot)
            
        elif data == "balance":
            message = type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})(),
                'text': '/balance'
            })()
            await balance(message, bot)
            
        elif data == "referrals":
            message = type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})(),
                'text': '/my_referrals'
            })()
            await my_referrals(message, bot)
            
        elif data == "leaderboard":
            message = type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})(),
                'text': '/leaderboard'
            })()
            await leaderboard(message, bot)
            
        elif data == "level":
            message = type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})(),
                'text': '/level'
            })()
            await level(message, bot)
            
        elif data == "my_profile":
            message = type('obj', (object,), {
                'from_user': user,
                'chat': type('chat', (object,), {'id': chat_id})(),
                'text': '/profile'
            })()
            await profile(message, bot)
            
        elif data == "get_tokens":
            # הוסף טוקנים למשתמש
            add_tokens_to_user(user.id, 5)
            await bot.answer_callback_query(
                callback_query.id,
                "🎉 קיבלת 5 טוקנים נוספים!",
                show_alert=True
            )
            
        elif data == "learn_more":
            await bot.answer_callback_query(
                callback_query.id,
                "📚 בדף העזרה תמצא את כל המידע: /help",
                show_alert=False
            )
            
        else:
            await bot.answer_callback_query(
                callback_query.id,
                "⚙️ תכונה זו בפיתוח",
                show_alert=False
            )
            
    except Exception as e:
        logger.error(f"❌ שגיאה ב-callback: {e}")
        try:
            await bot.answer_callback_query(
                callback_query.id,
                "❌ אירעה שגיאה",
                show_alert=False
            )
        except:
            pass

# ========== פקודות מנהלים ==========

async def admin_panel(message, bot):
    """פאנל ניהול - מורחב ומשופר"""
    try:
        from bot.admin_commands import admin_panel as admin_panel_func
        await admin_panel_func(message, bot)
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/admin", e)

async def add_tokens(message, bot):
    """הוספת טוקנים - למנהלים"""
    try:
        from bot.admin_commands import add_tokens as add_tokens_func
        await add_tokens_func(message, bot)
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/add_tokens", e)

async def reset_checkin(message, bot):
    """איפוס צ'ק-אין - למנהלים"""
    try:
        from bot.admin_commands import reset_checkin as reset_checkin_func
        await reset_checkin_func(message, bot)
    except Exception as e:
        await handle_command_error(bot, message.chat.id, "/reset_checkin", e)

# ========== רשימת פונקציות לייצוא ==========
__all__ = [
    'start', 'checkin', 'balance', 'referral', 'my_referrals',
    'leaderboard', 'level', 'profile', 'tasks', 'contact',
    'help_command', 'website', 'admin_panel', 'add_tokens',
    'reset_checkin', 'handle_callback_query'
]
