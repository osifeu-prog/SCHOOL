#!/usr/bin/env python3
"""
פקודות אדמין - Crypto-Class
פקודות ניהול מתקדמות למנהלי המערכת
"""

import logging
import asyncio
from datetime import datetime
from database.queries import (
    get_user, get_all_users, get_top_users, get_system_stats,
    add_tokens_to_user, reset_user_checkin, broadcast_message_to_all
)

logger = logging.getLogger(__name__)

# רשימת אדמינים (ניתן גם להגדיר ב-env)
ADMIN_IDS = [224223270]  # החלף ל-telegram_id שלך

def is_admin(user_id):
    """בדיקה אם משתמש הוא אדמין"""
    return user_id in ADMIN_IDS

async def admin_panel(update, context):
    """פאנל ניהול למנהלי המערכת"""
    try:
        user = update.effective_user
        
        # בדוק אם המשתמש הוא אדמין
        if not is_admin(user.id):
            await update.message.reply_text(
                "❌ **אין לך הרשאות ניהול!**\n\n"
                "רק מנהלי המערכת יכולים להשתמש בפקודה זו.",
                parse_mode="Markdown"
            )
            return
        
        # קבל סטטיסטיקות מערכת
        stats = get_system_stats()
        
        response = (
            "👑 **פאנל ניהול - Crypto-Class**\n\n"
            "📊 **סטטיסטיקות מערכת:**\n"
            f"• 👥 משתמשים: {stats.get('total_users', 0):,}\n"
            f"• 📅 פעילים היום: {stats.get('active_today', 0):,}\n"
            f"• 💰 טוקנים כוללים: {stats.get('total_tokens', 0):,}\n\n"
            "⚙️ **פקודות ניהול:**\n"
            "• `/admin_stats` - סטטיסטיקות מפורטות\n"
            "• `/admin_users` - ניהול משתמשים\n"
            "• `/admin_broadcast` - שליחת הודעה לכולם\n"
            "• `/add_tokens <user_id> <amount>` - הוספת טוקנים\n"
            "• `/reset_checkin <user_id>` - איפוס צ'ק-אין\n\n"
            "🌐 **דשבורד אתר:**\n"
            "• אתר: https://school-production-4d9d.up.railway.app\n"
            "• דשבורד מורה: /teacher\n"
            "• סטטיסטיקות: /stats\n\n"
            "🆔 **מזהה האדמין שלך:** {user.id}"
        )
        
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת admin: {e}")
        await update.message.reply_text(
            "❌ אירעה שגיאה בגישה לפאנל הניהול.",
            parse_mode="Markdown"
        )

async def admin_stats(update, context):
    """סטטיסטיקות מפורטות למערכת"""
    try:
        user = update.effective_user
        
        # בדוק אם המשתמש הוא אדמין
        if not is_admin(user.id):
            await update.message.reply_text("❌ אין לך הרשאות ניהול.")
            return
        
        # קבל סטטיסטיקות
        stats = get_system_stats()
        top_users = get_top_users(5, 'tokens')
        all_users = get_all_users()
        
        response = (
            "📊 **סטטיסטיקות מפורטות - Crypto-Class**\n\n"
            f"👥 **משתמשים:** {stats.get('total_users', 0):,}\n"
            f"📅 **פעילים היום:** {stats.get('active_today', 0):,}\n"
            f"💰 **טוקנים כוללים:** {stats.get('total_tokens', 0):,}\n\n"
            "🏆 **5 המובילים:**\n"
        )
        
        for i, top_user in enumerate(top_users, 1):
            name = top_user.first_name or top_user.username or f"משתמש {top_user.telegram_id}"
            response += f"{i}. {name} - {top_user.tokens:,} טוקנים\n"
        
        # חישוב ממוצע טוקנים
        if all_users:
            avg_tokens = sum(u.tokens for u in all_users) / len(all_users)
            response += f"\n📈 **ממוצע טוקנים למשתמש:** {avg_tokens:.1f}"
        
        response += f"\n\n⏰ **זמן מערכת:** {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}"
        
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת admin_stats: {e}")
        await update.message.reply_text("❌ שגיאה בטעינת סטטיסטיקות.")

async def admin_users(update, context):
    """רשימת משתמשים למערכת"""
    try:
        user = update.effective_user
        
        # בדוק אם המשתמש הוא אדמין
        if not is_admin(user.id):
            await update.message.reply_text("❌ אין לך הרשאות ניהול.")
            return
        
        # קבל את כל המשתמשים
        all_users = get_all_users()
        
        if not all_users:
            await update.message.reply_text("📭 אין משתמשים רשומים במערכת.")
            return
        
        response = (
            "👥 **רשימת משתמשים - Crypto-Class**\n\n"
            f"📋 **סה\"כ משתמשים:** {len(all_users)}\n\n"
        )
        
        # הצג 10 משתמשים ראשונים
        for i, user_obj in enumerate(all_users[:10], 1):
            name = user_obj.first_name or user_obj.username or f"משתמש {user_obj.telegram_id}"
            created = user_obj.created_at.strftime('%d/%m/%Y') if user_obj.created_at else "לא ידוע"
            response += (
                f"{i}. **{name}**\n"
                f"   🆔: {user_obj.telegram_id}\n"
                f"   💰: {user_obj.tokens:,} טוקנים\n"
                f"   📅: {created}\n\n"
            )
        
        if len(all_users) > 10:
            response += f"\n... ועוד {len(all_users) - 10} משתמשים."
        
        response += (
            "\n⚙️ **פקודות ניהול משתמשים:**\n"
            "• `/add_tokens <user_id> <amount>` - הוספת טוקנים\n"
            "• `/reset_checkin <user_id>` - איפוס צ'ק-אין\n"
        )
        
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת admin_users: {e}")
        await update.message.reply_text("❌ שגיאה בטעינת רשימת משתמשים.")

async def admin_broadcast(update, context):
    """שליחת הודעה לכל המשתמשים"""
    try:
        user = update.effective_user
        
        # בדוק אם המשתמש הוא אדמין
        if not is_admin(user.id):
            await update.message.reply_text("❌ אין לך הרשאות ניהול.")
            return
        
        # בדוק אם יש טקסט בהודעה
        if not context.args:
            await update.message.reply_text(
                "📢 **שליחת הודעה לכולם**\n\n"
                "שימוש: `/admin_broadcast <הודעה>`\n\n"
                "דוגמה: `/admin_broadcast הודעה חשובה לכולם!`",
                parse_mode="Markdown"
            )
            return
        
        message = " ".join(context.args)
        
        # שליחה למשתמש הנוכחי
        await update.message.reply_text(
            f"📢 **מתחיל לשלוח הודעה לכולם...**\n\n"
            f"📝 **ההודעה:**\n{message}\n\n"
            f"⏳ נא להמתין...",
            parse_mode="Markdown"
        )
        
        # שליחה לכל המשתמשים (במקרה אמיתי, יש לעשות זאת ברקע)
        users = get_all_users()
        success_count = 0
        fail_count = 0
        
        for user_obj in users:
            try:
                await context.bot.send_message(
                    chat_id=user_obj.telegram_id,
                    text=f"📢 **הודעה מהמערכת:**\n\n{message}",
                    parse_mode="Markdown"
                )
                success_count += 1
            except Exception as e:
                logger.error(f"❌ שגיאה בשליחה למשתמש {user_obj.telegram_id}: {e}")
                fail_count += 1
        
        await update.message.reply_text(
            f"✅ **שליחת הודעה הושלמה!**\n\n"
            f"✅ נשלח בהצלחה ל: {success_count} משתמשים\n"
            f"❌ נכשל בשליחה ל: {fail_count} משתמשים",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת admin_broadcast: {e}")
        await update.message.reply_text("❌ שגיאה בשליחת הודעה לכולם.")

async def add_tokens(update, context):
    """הוספת טוקנים למשתמש"""
    try:
        user = update.effective_user
        
        # בדוק אם המשתמש הוא אדמין
        if not is_admin(user.id):
            await update.message.reply_text("❌ אין לך הרשאות ניהול.")
            return
        
        # בדוק את הפרמטרים
        if len(context.args) != 2:
            await update.message.reply_text(
                "💰 **הוספת טוקנים למשתמש**\n\n"
                "שימוש: `/add_tokens <user_id> <amount>`\n\n"
                "דוגמה: `/add_tokens 123456789 100`",
                parse_mode="Markdown"
            )
            return
        
        try:
            target_user_id = int(context.args[0])
            amount = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ מזהה משתמש או כמות לא חוקיים.")
            return
        
        # הוסף טוקנים
        success, new_balance = add_tokens_to_user(target_user_id, amount)
        
        if success:
            target_user = get_user(target_user_id)
            user_name = target_user.first_name if target_user else f"משתמש {target_user_id}"
            
            await update.message.reply_text(
                f"✅ **טוקנים נוספו בהצלחה!**\n\n"
                f"👤 **משתמש:** {user_name}\n"
                f"🆔 **מזהה:** {target_user_id}\n"
                f"➕ **נוספו:** {amount:,} טוקנים\n"
                f"💰 **יתרה חדשה:** {new_balance:,} טוקנים",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ לא ניתן להוסיף טוקנים למשתמש זה.\n"
                "ייתכן שהמשתמש לא קיים."
            )
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת add_tokens: {e}")
        await update.message.reply_text("❌ שגיאה בהוספת טוקנים.")

async def reset_checkin(update, context):
    """איפוס צ'ק-אין למשתמש"""
    try:
        user = update.effective_user
        
        # בדוק אם המשתמש הוא אדמין
        if not is_admin(user.id):
            await update.message.reply_text("❌ אין לך הרשאות ניהול.")
            return
        
        # בדוק את הפרמטרים
        if len(context.args) != 1:
            await update.message.reply_text(
                "🔄 **איפוס צ'ק-אין למשתמש**\n\n"
                "שימוש: `/reset_checkin <user_id>`\n\n"
                "דוגמה: `/reset_checkin 123456789`",
                parse_mode="Markdown"
            )
            return
        
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ מזהה משתמש לא חוקי.")
            return
        
        # אפס צ'ק-אין
        success = reset_user_checkin(target_user_id)
        
        if success:
            target_user = get_user(target_user_id)
            user_name = target_user.first_name if target_user else f"משתמש {target_user_id}"
            
            await update.message.reply_text(
                f"✅ **צ'ק-אין אופס בהצלחה!**\n\n"
                f"👤 **משתמש:** {user_name}\n"
                f"🆔 **מזהה:** {target_user_id}\n"
                f"🔄 **ניתן כעת לבצע צ'ק-אין יומי חדש**",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ לא ניתן לאפס צ'ק-אין למשתמש זה.\n"
                "ייתכן שהמשתמש לא קיים."
            )
        
    except Exception as e:
        logger.error(f"❌ שגיאה בפקודת reset_checkin: {e}")
        await update.message.reply_text("❌ שגיאה באיפוס צ'ק-אין.")
