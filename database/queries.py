# database/queries.py
from .models import Session, User, Attendance, Task, TaskCompletion, UserDailyStats, Referral
from .models import TaskStatus, TaskFrequency, TaskType
from datetime import datetime, date, timedelta
import random
import string

# ===================== פונקציות עזר =====================

def generate_referral_code(length=8):
    """יצירת קוד הפניה ייחודי"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ===================== פונקציות אתחול =====================

def init_database():
    """אתחול מסד הנתונים והוספת משימות ברירת מחדל"""
    from .models import Base, engine
    
    try:
        Base.metadata.create_all(engine)
        print("✅ טבלאות נוצרו בהצלחה")
        
        session = Session()
        try:
            default_tasks = [
                {
                    "name": "צ'ק-ין יומי",
                    "description": "התחבר כל יום וקבל טוקן",
                    "task_type": TaskType.CLASS,
                    "frequency": TaskFrequency.DAILY,
                    "tokens_reward": 1,
                    "exp_reward": 10
                },
                {
                    "name": "תרומה לפורום",
                    "description": "פרסם תשובה או שאלה בפורום הקורס",
                    "task_type": TaskType.FORUM,
                    "frequency": TaskFrequency.DAILY,
                    "tokens_reward": 3,
                    "exp_reward": 25,
                    "requires_proof": True
                },
                {
                    "name": "סיוע לתלמיד",
                    "description": "עזור לתלמיד אחר בשאלה או בעיה",
                    "task_type": TaskType.HELP,
                    "frequency": TaskFrequency.DAILY,
                    "tokens_reward": 5,
                    "exp_reward": 50,
                    "requires_proof": True
                },
                {
                    "name": "הפניה של חבר",
                    "description": "הזמן חבר חדש למערכת",
                    "task_type": TaskType.REFERRAL,
                    "frequency": TaskFrequency.ONE_TIME,
                    "tokens_reward": 10,
                    "exp_reward": 100
                }
            ]
            
            for task_data in default_tasks:
                existing_task = session.query(Task).filter_by(name=task_data["name"]).first()
                if not existing_task:
                    task = Task(**task_data)
                    session.add(task)
                    print(f"✅ משימה נוצרה: {task_data['name']}")
            
            session.commit()
            print("✅ מסד הנתונים אותחל בהצלחה עם משימות ברירת מחדל")
            
        except Exception as e:
            session.rollback()
            print(f"❌ שגיאה באתחול משימות: {e}")
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ שגיאה ביצירת טבלאות: {e}")

# ===================== פונקציות משתמשים =====================

def register_user(telegram_id, username=None, first_name=None, last_name=None, referral_code=None):
    """רישום משתמש חדש עם הפניה"""
    session = Session()
    try:
        existing_user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if not existing_user:
            user_referral_code = generate_referral_code()
            while session.query(User).filter_by(referral_code=user_referral_code).first():
                user_referral_code = generate_referral_code()
            
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                tokens=0,
                referral_code=user_referral_code
            )
            session.add(user)
            
            if referral_code:
                referrer = session.query(User).filter_by(referral_code=referral_code).first()
                if referrer and referrer.telegram_id != telegram_id:
                    referral = Referral(
                        referrer_id=referrer.telegram_id,
                        referred_id=telegram_id,
                        referral_code=referral_code
                    )
                    session.add(referral)
                    
                    referrer.total_referrals += 1
                    referrer.tokens += 10
                    referrer.referral_tokens += 10
            
            session.commit()
            print(f"✅ משתמש נרשם: {telegram_id} עם קוד הפניה: {user_referral_code}")
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"❌ שגיאה ברישום משתמש: {e}")
        return False
    finally:
        session.close()

def checkin_user(telegram_id):
    """רישום נוכחות יומית"""
    session = Session()
    try:
        today = date.today()
        
        existing_checkin = session.query(Attendance).filter_by(
            telegram_id=telegram_id,
            date=today
        ).first()
        
        if existing_checkin:
            return False, "כבר ביצעת צ'ק-ין היום!"
        
        attendance = Attendance(
            telegram_id=telegram_id,
            date=today,
            tokens_earned=1
        )
        session.add(attendance)
        
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            user.tokens += 1
            user.last_checkin = today
            user.experience += 10
        
        session.commit()
        return True, "🎉 צ'ק-ין נרשם בהצלחה! קיבלת 1 טוקן!"
        
    except Exception as e:
        session.rollback()
        print(f"❌ שגיאה ברישום צ'ק-ין: {e}")
        return False, f"שגיאה: {str(e)}"
    finally:
        session.close()

def get_balance(telegram_id):
    """קבלת יתרת טוקנים"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user.tokens if user else 0
    except Exception as e:
        print(f"❌ שגיאה בקבלת יתרה: {e}")
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
        print(f"❌ שגיאה בקבלת משתמש: {e}")
        return None
    finally:
        session.close()

def get_all_users():
    """קבלת כל המשתמשים"""
    session = Session()
    try:
        users = session.query(User).order_by(User.created_at.desc()).all()
        return users
    except Exception as e:
        print(f"❌ שגיאה בקבלת כל המשתמשים: {e}")
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
        
        from sqlalchemy import func
        rank = session.query(User).filter(User.tokens > user.tokens).count() + 1
        
        progress_percentage = int((user.experience / user.next_level_exp) * 100) if user.next_level_exp > 0 else 0
        
        return {
            'level': user.level,
            'experience': user.experience,
            'next_level_exp': user.next_level_exp,
            'total_experience': user.total_experience,
            'progress_percentage': progress_percentage,
            'rank': rank
        }
        
    except Exception as e:
        print(f"❌ שגיאה בקבלת מידע רמה: {e}")
        return None
    finally:
        session.close()

def get_top_users(limit=10, order_by='tokens'):
    """קבלת רשימת המשתמשים המובילים"""
    session = Session()
    try:
        if order_by == 'tokens':
            users = session.query(User).order_by(User.tokens.desc()).limit(limit).all()
        elif order_by == 'level':
            users = session.query(User).order_by(User.level.desc(), User.experience.desc()).limit(limit).all()
        elif order_by == 'referrals':
            users = session.query(User).order_by(User.total_referrals.desc()).limit(limit).all()
        else:
            users = session.query(User).order_by(User.tokens.desc()).limit(limit).all()
        
        return users
    except Exception as e:
        print(f"❌ שגיאה בקבלת מובילים: {e}")
        return []
    finally:
        session.close()

def get_user_referrals(telegram_id, limit=10):
    """קבלת רשימת ההפניות של משתמש"""
    session = Session()
    try:
        referrals = session.query(Referral).filter_by(referrer_id=telegram_id).order_by(Referral.created_at.desc()).limit(limit).all()
        return referrals
    except Exception as e:
        print(f"❌ שגיאה בקבלת הפניות: {e}")
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
        print(f"❌ שגיאה בקבלת מספר הפניות: {e}")
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
        print(f"❌ שגיאה בקבלת מוזמנים: {e}")
        return []
    finally:
        session.close()

# ===================== פונקציות משימות =====================

def get_available_tasks(telegram_id):
    """קבלת רשימת משימות זמינות למשתמש"""
    session = Session()
    try:
        tasks = session.query(Task).filter_by(is_active=True).all()
        return tasks
    except Exception as e:
        print(f"❌ שגיאה בקבלת משימות: {e}")
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
        
        completion = TaskCompletion(
            telegram_id=telegram_id,
            task_id=task_id,
            tokens_earned=task.tokens_reward,
            exp_earned=task.exp_reward,
            status=TaskStatus.COMPLETED,
            proof_text=proof_text
        )
        
        user.tokens += task.tokens_reward
        user.experience += task.exp_reward
        
        session.add(completion)
        session.commit()
        
        return True, f"🎉 השלמת משימה! קיבלת {task.tokens_reward} טוקנים!"
            
    except Exception as e:
        session.rollback()
        print(f"❌ שגיאה בהשלמת משימה: {e}")
        return False, f"שגיאה: {str(e)}"
    finally:
        session.close()

# ===================== פונקציות סטטיסטיקה =====================

def get_system_stats():
    """קבלת סטטיסטיקות מערכת"""
    session = Session()
    try:
        from sqlalchemy import func
        total_users = session.query(User).count()
        active_today = session.query(Attendance).filter(
            Attendance.date == date.today()
        ).distinct(Attendance.telegram_id).count()
        total_tokens = session.query(func.sum(User.tokens)).scalar() or 0
        
        return {
            'total_users': total_users,
            'active_today': active_today,
            'total_tokens': total_tokens
        }
    except Exception as e:
        print(f"❌ שגיאה בקבלת סטטיסטיקות: {e}")
        return {'total_users': 0, 'active_today': 0, 'total_tokens': 0}
    finally:
        session.close()

def get_checkin_data(days=7):
    """קבלת נתוני צ'ק-אין ל-7 ימים אחרונים"""
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
        print(f"❌ שגיאה בקבלת נתוני צ'ק-אין: {e}")
        return []
    finally:
        session.close()

def get_activity_count():
    """קבלת מספר הפעילים היום"""
    session = Session()
    try:
        count = session.query(Attendance).filter(
            Attendance.date == date.today()
        ).distinct(Attendance.telegram_id).count()
        return count
    except Exception as e:
        print(f"❌ שגיאה בקבלת מספר פעילים: {e}")
        return 0
    finally:
        session.close()

# ===================== פונקציות אדמין =====================

def add_tokens_to_user(telegram_id, amount):
    """הוספת טוקנים למשתמש (פונקציית אדמין)"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return False, 0
        
        user.tokens += amount
        session.commit()
        
        return True, user.tokens
    except Exception as e:
        session.rollback()
        print(f"❌ שגיאה בהוספת טוקנים: {e}")
        return False, 0
    finally:
        session.close()

def reset_user_checkin(telegram_id):
    """איפוס צ'ק-אין של משתמש (פונקציית אדמין)"""
    session = Session()
    try:
        today = date.today()
        
        # מחק את רשומת הצ'ק-אין של היום
        attendance = session.query(Attendance).filter_by(
            telegram_id=telegram_id,
            date=today
        ).first()
        
        if attendance:
            session.delete(attendance)
            session.commit()
            return True
        
        return False
    except Exception as e:
        session.rollback()
        print(f"❌ שגיאה באיפוס צ'ק-אין: {e}")
        return False
    finally:
        session.close()

def broadcast_message_to_all(message):
    """שליחת הודעה לכל המשתמשים (פונקציית אדמין)"""
    session = Session()
    try:
        users = session.query(User).all()
        user_ids = [user.telegram_id for user in users]
        
        return user_ids
    except Exception as e:
        print(f"❌ שגיאה בקבלת רשימת משתמשים: {e}")
        return []
    finally:
        session.close()
