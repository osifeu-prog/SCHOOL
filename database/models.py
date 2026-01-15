#!/usr/bin/env python3
"""
מודלים של מסד הנתונים
גרסה מעודכנת ופשוטה
"""

from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Boolean, BigInteger, ForeignKey, JSON, Enum, Text, Float
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, date
import os
import enum

# יצירת מסד נתונים SQLite
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'attendance.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ===================== ENUMS =====================

class TaskFrequency(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ONE_TIME = "one_time"

class TaskType(enum.Enum):
    FORUM = "forum"
    CLASS = "class"
    HELP = "help"
    QUIZ = "quiz"
    REFERRAL = "referral"
    OTHER = "other"

class TaskStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    LOCKED = "locked"
    PENDING = "pending"

# ===================== MODELS =====================

class User(Base):
    """מודל משתמש"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    last_checkin = Column(Date)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    next_level_exp = Column(Integer, default=100)
    referral_code = Column(String(20), unique=True)
    total_referrals = Column(Integer, default=0)
    referral_tokens = Column(Integer, default=0)
    total_experience = Column(Integer, default=0)
    
    # יחסים
    attendances = relationship("Attendance", back_populates="user", cascade="all, delete-orphan")
    task_completions = relationship("TaskCompletion", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.telegram_id} ({self.username})>"

class Attendance(Base):
    """מודל נוכחות"""
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=False)
    date = Column(Date, nullable=False)
    checkin_time = Column(DateTime, default=datetime.now)
    tokens_earned = Column(Integer, default=1)
    
    # יחסים
    user = relationship("User", back_populates="attendances")
    
    def __repr__(self):
        return f"<Attendance {self.telegram_id} on {self.date}>"

class Task(Base):
    """מודל משימה"""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    instructions = Column(Text)
    task_type = Column(Enum(TaskType), nullable=False, default=TaskType.OTHER)
    frequency = Column(Enum(TaskFrequency), nullable=False, default=TaskFrequency.DAILY)
    tokens_reward = Column(Integer, nullable=False, default=1)
    exp_reward = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    requires_proof = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # יחסים
    completions = relationship("TaskCompletion", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task '{self.name}' ({self.tokens_reward} tokens)>"

class TaskCompletion(Base):
    """מודל השלמת משימה"""
    __tablename__ = 'task_completions'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    completed_at = Column(DateTime, default=datetime.now)
    tokens_earned = Column(Integer, nullable=False)
    exp_earned = Column(Integer, default=0)
    status = Column(Enum(TaskStatus), default=TaskStatus.COMPLETED)
    proof_text = Column(Text)
    verified_by = Column(BigInteger)
    
    # יחסים
    user = relationship("User", back_populates="task_completions")
    task = relationship("Task", back_populates="completions")
    
    def __repr__(self):
        return f"<TaskCompletion user:{self.telegram_id} task:{self.task_id}>"

class UserDailyStats(Base):
    """סטטיסטיקות יומיות של משתמש"""
    __tablename__ = 'user_daily_stats'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    tasks_completed = Column(Integer, default=0)
    tokens_earned = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    
    # יחסים
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserDailyStats {self.telegram_id} on {self.date}>"

class Referral(Base):
    """מודל הפניות"""
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True)
    referrer_id = Column(BigInteger, nullable=False)
    referred_id = Column(BigInteger, unique=True, nullable=False)
    referral_code = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='active')
    
    def __repr__(self):
        return f"<Referral {self.referrer_id} -> {self.referred_id}>"

# יצירת הטבלאות
def create_tables():
    """יצירת כל הטבלאות במסד הנתונים"""
    Base.metadata.create_all(engine)
    print("✅ טבלאות נוצרו בהצלחה")

if __name__ == "__main__":
    create_tables()
