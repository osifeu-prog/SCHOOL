#!/usr/bin/env python3
"""
מסד נתונים משודרג עם תכונות חדשות
גרסה מלאה ומוכנה להפעלה
"""

import logging
from .models import Session, User, Attendance, Task, TaskCompletion, UserDailyStats, Referral
from .models import TaskStatus, TaskFrequency, TaskType
from datetime import datetime, date, timedelta
import random
import string
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# ========== פונקציות עזר ==========

def generate_referral_code(length=8):
    """יצירת קוד הפניה ייחודי עם בדיקת כפילויות"""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        # בדוק אם הקוד כבר קיים
        session = Session()
        try:
            existing = session.query(User).filter_by(referral_code=code).first()
            if not existing:
                return code
        finally:
            session.close()

# ========== פונקציות אתחול ==========

def init_database():
    """אתחול מסד הנתונים עם נתונים ראשוניים"""
    from .models import Base, engine
    
    try:
        Base.metadata.create_all(engine)
        logger.info("✅ טבלאות נוצרו בהצלחה")
        
        session = Session()
        try:
            # משימות ברירת מחדל
            default_tasks = [
                {
                    "name": "צ'ק-אין יומי",
                    "description": "התחבר כל יום וקבל טוקן",
                    "task_type": TaskType.CLASS,
                    "frequency": TaskFrequency.DAILY,
                    "tokens_reward": 1,
                    "exp_reward": 10,
                    "is_active": True
                },
                {
                    "name": "תרומה לפורום",
                    "description": "פרסם תשובה או שאלה בפורום הקורס",
                    "task_type": TaskType.FORUM,
                    "frequency": TaskFrequency.DAILY,
                    "tokens_reward": 3,
                    "exp_reward": 25,
                    "requires_proof": True,
                    "is_active": True
                },
                {
                    "name": "סיוע לתלמיד",
                    "description": "עזור לתלמיד אחר בשאלה או בעיה",
                    "task_type": TaskType.HELP,
                    "frequency": TaskFrequency.DAILY,
                    "tokens_reward": 5,
                    "exp_reward": 50,
                    "requires_proof": True,
                    "is_active": True
                },
                {
                    "name": "הפניה של חבר",
                    "description": "הזמן חבר חדש למערכת",
                    "task_type": TaskType.REFERRAL,
                    "frequency": TaskFrequency.ONE_TIME,
                    "tokens_reward": 10,
                    "exp_reward": 100,
                    "is_active": True
                }
            ]
            
            for task_data in default_tasks:
                existing_task = session.query(Task).filter_by(name=task_data["name"]).first()
                if not existing_task:
                    task = Task(**task_data)
                    session.add(task)
                    logger.info(f"✅ משימה נוצרה: {task_data['name']}")
            
            session.commit()
            logger.info("✅ מסד הנתונים אותחל בהצלחה עם משימות ברירת מחדל")
            
            # הוספת משתמש דמו אם אין משתמשים
            user_count = session.query(User).count()
            if user_count == 0:
                demo_user = User(
                    telegram_id=123456789,
                    username="demo_user",
                    first_name="משתמש",
                    last_name="דמו",
                    tokens=100,
                    level=3,
                    experience=150,
                    next_level_exp=200,
                    referral_code=generate_referral_code(),
                    total_referrals=2,
                    referral_tokens=20
                )
                session.add(demo_user)
                
                # הוספת צ'ק-אין לדמו
                for i in range(5):
                    checkin_date = date.today() - timedelta(days=i)
                    attendance = Attendance(
                        telegram_id=123456789,
                        date=checkin_date,
                        tokens_earned=1
                    )
                    session.add(attendance)
                
                session.commit()
                logger.info("✅ משתמש דמו נוסף עם היסטוריית צ'ק-אין")
                
        except Exception as e:
            session.rollback()
            logger.error(f"❌ שגיאה באתחול משימות: {e}")
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"❌ שגיאה ביצירת טבלאות: {e}")
        raise

# ========== פונקציות משתמשים ==========

def register_user(telegram_id, username=None, first_name=None, last_name=None, referral_code=None):
    """רישום משתמש חדש עם הפניה"""
    session = Session()
    try:
        existing_user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if existing_user:
            logger.info(f"ℹ️ משתמש {telegram_id} כבר קיים")
            return False
        
        # יצירת קוד הפניה ייחודי
        user_referral_code = generate_referral_code()
        
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            tokens=10,  # בונוס הרשמה
            referral_code=user_referral_code,
            level=1,
            experience=0,
            next_level_exp=100,
            total_referrals=0,
            referral_tokens=0,
            created_at=datetime.now()
        )
        session.add(user)
        
        # טיפול בהפניה אם קיים
        if referral_code:
            referrer = session.query(User).filter_by(referral_code=referral_code).first()
            if referrer and referrer.telegram_id != telegram_id:
                # בדוק אם כבר קיימת הפניה
                existing_ref = session.query(Referral).filter_by(
                    referrer_id=referrer.telegram_id,
                    referred_id=telegram_id
                ).first()
                
                if not existing_ref:
                    referral = Referral(
                        referrer_id=referrer.telegram_id,
                        referred_id=telegram_id,
                        referral_code=referral_code,
                        status='active',
                        created_at=datetime.now()
                    )
                    session.add(referral)
                    
                    # עדכון המזמין
                    referrer.total_referrals += 1
                    referrer.tokens += 10
                    referrer.referral_tokens += 10
                    
                    # הודעה למזמין
                    user.tokens += 5  # בונוס למצטרף דרך הפניה
        
        session.commit()
        logger.info(f"✅ משתמש נרשם: {telegram_id} עם קוד הפניה: {user_referral_code}")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה ברישום משתמש: {e}")
        return False
    finally:
        session.close()

def checkin_user(telegram_id):
    """צ'ק-אין יומי"""
    session = Session()
    try:
        today = date.today()
        
        # בדוק אם כבר ביצע צ'ק-אין היום
        existing_checkin = session.query(Attendance).filter_by(
            telegram_id=telegram_id,
            date=today
        ).first()
        
        if existing_checkin:
            return False, "כבר ביצעת צ'ק-אין היום!"
        
        # קבל את המשתמש
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return False, "משתמש לא נמצא. שלח /start כדי להירשם"
        
        # חישוב טוקנים בסיסיים
        tokens_earned = 1
        
        # בונוס רמה
        level_bonus = user.level // 3  # כל 3 רמות בונוס נוסף
        tokens_earned += level_bonus
        
        # יצירת רשומת נוכחות
        attendance = Attendance(
            telegram_id=telegram_id,
            date=today,
            tokens_earned=tokens_earned,
            checkin_time=datetime.now()
        )
        session.add(attendance)
        
        # עדכון המשתמש
        user.tokens += tokens_earned
        user.last_checkin = today
        user.experience += (tokens_earned * 10)
        
        # עדכון רמה אם צריך
        update_user_level(user)
        
        session.commit()
        
        # יצירת הודעה
        message = f"🎉 צ'ק-אין נרשם בהצלחה! קיבלת {tokens_earned} טוקנים!"
        if level_bonus > 0:
            message += f" (בונוס רמה: +{level_bonus})"
        
        return True, message
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה ברישום צ'ק-אין: {e}")
        return False, f"שגיאה: {str(e)}"
    finally:
        session.close()

def update_user_level(user):
    """עדכון רמת המשתמש לפי הניסיון"""
    # נוסחת רמות פשוטה
    if user.experience >= 10000:
        new_level = 10
    elif user.experience >= 5000:
        new_level = 9
    elif user.experience >= 2000:
        new_level = 8
    elif user.experience >= 1000:
        new_level = 7
    elif user.experience >= 500:
        new_level = 6
    elif user.experience >= 200:
        new_level = 5
    elif user.experience >= 100:
        new_level = 4
    elif user.experience >= 50:
        new_level = 3
    elif user.experience >= 20:
        new_level = 2
    else:
        new_level = 1
    
    if new_level > user.level:
        user.level = new_level
        user.next_level_exp = user.experience * 2  # יעד פשוט להמשך
        
        # בונוס עלייה ברמה
        user.tokens += new_level * 5
        return True
    
    return False

def get_balance(telegram_id):
    """קבלת יתרת טוקנים"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user.tokens if user else 0
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת יתרה: {e}")
        return 0
    finally:
        session.close()

def get_user(telegram_id):
    """קבלת משתמש לפי ID"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת משתמש: {e}")
        return None
    finally:
        session.close()

def get_all_users(limit=None, offset=0):
    """קבלת כל המשתמשים"""
    session = Session()
    try:
        query = session.query(User).order_by(desc(User.created_at))
        if limit:
            query = query.limit(limit).offset(offset)
        users = query.all()
        return users
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת כל המשתמשים: {e}")
        return []
    finally:
        session.close()

def get_user_level_info(telegram_id):
    """קבלת מידע על רמת המשתמש"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return None
        
        # חישוב דירוג
        rank = session.query(User).filter(User.tokens > user.tokens).count() + 1
        
        # חישוב אחוזי התקדמות
        progress_percentage = int((user.experience / user.next_level_exp) * 100) if user.next_level_exp > 0 else 0
        
        return {
            'level': user.level,
            'experience': user.experience,
            'next_level_exp': user.next_level_exp,
            'total_experience': user.experience,
            'progress_percentage': progress_percentage,
            'rank': rank
        }
        
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת מידע רמה: {e}")
        return None
    finally:
        session.close()

def get_top_users(limit=10, order_by='tokens'):
    """קבלת רשימת המשתמשים המובילים"""
    session = Session()
    try:
        if order_by == 'tokens':
            users = session.query(User).order_by(desc(User.tokens)).limit(limit).all()
        elif order_by == 'level':
            users = session.query(User).order_by(desc(User.level), desc(User.experience)).limit(limit).all()
        elif order_by == 'referrals':
            users = session.query(User).order_by(desc(User.total_referrals)).limit(limit).all()
        else:
            users = session.query(User).order_by(desc(User.tokens)).limit(limit).all()
        
        return users
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת מובילים: {e}")
        return []
    finally:
        session.close()

def get_user_referrals(telegram_id, limit=10):
    """קבלת רשימת ההפניות של משתמש"""
    session = Session()
    try:
        referrals = session.query(Referral).filter_by(
            referrer_id=telegram_id
        ).order_by(desc(Referral.created_at)).limit(limit).all()
        return referrals
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת הפניות: {e}")
        return []
    finally:
        session.close()

def get_total_referrals(telegram_id):
    """קבלת מספר ההפניות הכולל של משתמש"""
    session = Session()
    try:
        count = session.query(Referral).filter_by(referrer_id=telegram_id).count()
        return count
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת מספר הפניות: {e}")
        return 0
    finally:
        session.close()

def get_referred_users(telegram_id):
    """קבלת רשימת המוזמנים של משתמש"""
    session = Session()
    try:
        referrals = session.query(Referral).filter_by(referrer_id=telegram_id).all()
        referred_ids = [r.referred_id for r in referrals]
        
        if not referred_ids:
            return []
        
        users = session.query(User).filter(User.telegram_id.in_(referred_ids)).all()
        return users
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת מוזמנים: {e}")
        return []
    finally:
        session.close()

def get_user_attendance_history(telegram_id, days=30):
    """קבלת היסטוריית נוכחות של משתמש"""
    session = Session()
    try:
        start_date = date.today() - timedelta(days=days)
        attendances = session.query(Attendance).filter(
            Attendance.telegram_id == telegram_id,
            Attendance.date >= start_date
        ).order_by(desc(Attendance.date)).all()
        
        return attendances
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת היסטוריית נוכחות: {e}")
        return []
    finally:
        session.close()

# ========== פונקציות משימות ==========

def get_available_tasks(telegram_id):
    """קבלת רשימת משימות זמינות למשתמש"""
    session = Session()
    try:
        # קבל את כל המשימות הפעילות
        tasks = session.query(Task).filter_by(is_active=True).all()
        return tasks
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת משימות: {e}")
        return []
    finally:
        session.close()

def get_user_tasks(telegram_id):
    """קבלת רשימת המשימות של משתמש"""
    session = Session()
    try:
        tasks = session.query(TaskCompletion).filter_by(
            telegram_id=telegram_id
        ).order_by(desc(TaskCompletion.completed_at)).all()
        return tasks
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת משימות משתמש: {e}")
        return []
    finally:
        session.close()

def complete_task(telegram_id, task_id, proof_text=None):
    """השלמת משימה"""
    session = Session()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task or not task.is_active:
            return False, "המשימה לא קיימת או לא פעילה"
        
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return False, "משתמש לא נמצא"
        
        # יצירת רשומת השלמה
        completion = TaskCompletion(
            telegram_id=telegram_id,
            task_id=task_id,
            tokens_earned=task.tokens_reward,
            exp_earned=task.exp_reward,
            status=TaskStatus.COMPLETED,
            proof_text=proof_text,
            completed_at=datetime.now()
        )
        
        user.tokens += task.tokens_reward
        user.experience += task.exp_reward
        update_user_level(user)
        
        session.add(completion)
        session.commit()
        
        return True, f"🎉 השלמת משימה! קיבלת {task.tokens_reward} טוקנים!"
            
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה בהשלמת משימה: {e}")
        return False, f"שגיאה: {str(e)}"
    finally:
        session.close()

# ========== פונקציות סטטיסטיקה ==========

def get_system_stats():
    """קבלת סטטיסטיקות מערכת"""
    session = Session()
    try:
        total_users = session.query(User).count()
        today = date.today()
        active_today = session.query(Attendance).filter(
            Attendance.date == today
        ).distinct(Attendance.telegram_id).count()
        total_tokens = session.query(func.sum(User.tokens)).scalar() or 0
        
        # חישוב מתקדמים נוספים
        total_referrals = session.query(Referral).count()
        total_tasks_completed = session.query(TaskCompletion).filter_by(
            status=TaskStatus.COMPLETED
        ).count()
        
        # חישוב ממוצעים
        avg_tokens = total_tokens / total_users if total_users > 0 else 0
        avg_level = session.query(func.avg(User.level)).scalar() or 0
        
        return {
            'total_users': total_users,
            'active_today': active_today,
            'total_tokens': total_tokens,
            'total_referrals': total_referrals,
            'total_tasks_completed': total_tasks_completed,
            'avg_tokens': round(avg_tokens, 2),
            'avg_level': round(avg_level, 2),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת סטטיסטיקות: {e}")
        return {
            'total_users': 0,
            'active_today': 0,
            'total_tokens': 0,
            'total_referrals': 0,
            'total_tasks_completed': 0,
            'avg_tokens': 0,
            'avg_level': 0,
            'timestamp': datetime.now().isoformat()
        }
    finally:
        session.close()

def get_checkin_data(days=7):
    """קבלת נתוני צ'ק-אין לימים אחרונים"""
    session = Session()
    try:
        data = []
        for i in range(days):
            day = date.today() - timedelta(days=i)
            count = session.query(Attendance).filter(Attendance.date == day).count()
            data.append({
                'date': day.strftime('%Y-%m-%d'),
                'day_name': day.strftime('%a'),
                'count': count
            })
        return list(reversed(data))
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת נתוני צ'ק-אין: {e}")
        return []
    finally:
        session.close()

def get_activity_count():
    """קבלת מספר הפעילים היום"""
    session = Session()
    try:
        today = date.today()
        count = session.query(Attendance).filter(
            Attendance.date == today
        ).distinct(Attendance.telegram_id).count()
        return count
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת מספר פעילים: {e}")
        return 0
    finally:
        session.close()

# ========== פונקציות אדמין ==========

def add_tokens_to_user(telegram_id, amount, reason=None):
    """הוספת טוקנים למשתמש"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return False, 0, "משתמש לא נמצא"
        
        user.tokens += amount
        session.commit()
        
        return True, user.tokens, f"✅ נוספו {amount} טוקנים"
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה בהוספת טוקנים: {e}")
        return False, 0, f"שגיאה: {str(e)}"
    finally:
        session.close()

def reset_user_checkin(telegram_id):
    """איפוס צ'ק-אין של משתמש"""
    session = Session()
    try:
        today = date.today()
        
        # מחק את רשומת הצ'ק-אין של היום
        attendance = session.query(Attendance).filter_by(
            telegram_id=telegram_id,
            date=today
        ).first()
        
        if attendance:
            # החזר את הטוקנים
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.tokens -= attendance.tokens_earned
                if user.tokens < 0:
                    user.tokens = 0
            
            session.delete(attendance)
            session.commit()
            return True, "✅ צ'ק-אין אופס בהצלחה"
        
        return False, "לא נמצא צ'ק-אין לאיפוס"
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה באיפוס צ'ק-אין: {e}")
        return False, f"שגיאה: {str(e)}"
    finally:
        session.close()

def broadcast_message_to_all():
    """קבלת כל משתמשי המערכת לשידור"""
    session = Session()
    try:
        users = session.query(User).all()
        user_ids = [user.telegram_id for user in users]
        return user_ids
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת רשימת משתמשים: {e}")
        return []
    finally:
        session.close()

# ========== פונקציות נוספות ==========

def search_users(query, limit=20):
    """חיפוש משתמשים"""
    session = Session()
    try:
        users = session.query(User).filter(
            or_(
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%"),
                User.username.ilike(f"%{query}%")
            )
        ).limit(limit).all()
        
        return users
    except Exception as e:
        logger.error(f"❌ שגיאה בחיפוש משתמשים: {e}")
        return []
    finally:
        session.close()

def get_daily_stats():
    """קבלת סטטיסטיקות יומיות"""
    session = Session()
    try:
        today = date.today()
        
        # משתמשים חדשים היום
        new_users_today = session.query(User).filter(
            func.date(User.created_at) == today
        ).count()
        
        # צ'ק-אין היום
        checkins_today = session.query(Attendance).filter(
            Attendance.date == today
        ).count()
        
        # משימות שהושלמו היום
        tasks_today = session.query(TaskCompletion).filter(
            func.date(TaskCompletion.completed_at) == today
        ).count()
        
        return {
            'new_users_today': new_users_today,
            'checkins_today': checkins_today,
            'tasks_today': tasks_today,
            'date': today.isoformat()
        }
    except Exception as e:
        logger.error(f"❌ שגיאה בקבלת סטטיסטיקות יומיות: {e}")
        return {}
    finally:
        session.close()

def cleanup_old_data(days_to_keep=90):
    """ניקוי נתונים ישנים"""
    session = Session()
    try:
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        # מחק נתוני נוכחות ישנים
        old_attendances = session.query(Attendance).filter(
            Attendance.date < cutoff_date
        ).delete(synchronize_session=False)
        
        # מחק נתוני השלמת משימות ישנים
        old_completions = session.query(TaskCompletion).filter(
            TaskCompletion.completed_at < cutoff_date
        ).delete(synchronize_session=False)
        
        session.commit()
        
        logger.info(f"🧹 נוקו {old_attendances} רשומות נוכחות ו-{old_completions} רשומות השלמה")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"❌ שגיאה בניקוי נתונים ישנים: {e}")
        return False
    finally:
        session.close()

# ========== ייצוא פונקציות ==========
__all__ = [
    'init_database',
    'register_user', 'checkin_user', 'get_user', 'get_all_users',
    'get_balance', 'get_user_level_info', 'update_user_level',
    'get_top_users', 'get_user_referrals', 'get_total_referrals', 
    'get_referred_users', 'get_user_attendance_history',
    'get_available_tasks', 'get_user_tasks', 'complete_task',
    'get_system_stats', 'get_checkin_data', 'get_activity_count',
    'add_tokens_to_user', 'reset_user_checkin', 'broadcast_message_to_all',
    'search_users', 'get_daily_stats', 'cleanup_old_data'
]
