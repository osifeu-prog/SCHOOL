# database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Boolean, BigInteger, ForeignKey, JSON, Enum, Index, func, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, date
import os
import enum

# יצירת מסד נתונים SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'attendance.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f'sqlite:///{DB_PATH}')
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
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    last_checkin = Column(Date)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    next_level_exp = Column(Integer, default=100)
    total_experience = Column(Integer, default=0)
    referral_code = Column(String(20), unique=True, index=True)
    total_referrals = Column(Integer, default=0)
    referral_tokens = Column(Integer, default=0)
    
    # יחסים
    attendances = relationship("Attendance", back_populates="user")
    task_completions = relationship("TaskCompletion", back_populates="user")
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_received = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred")
    
    def __repr__(self):
        return f"<User {self.telegram_id} ({self.username})>"

class Attendance(Base):
    """מודל נוכחות"""
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=False, index=True)
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
    cooldown_hours = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    requires_proof = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    metadata_json = Column(JSON)
    
    # יחסים
    completions = relationship("TaskCompletion", back_populates="task")
    
    def __repr__(self):
        return f"<Task '{self.name}' ({self.tokens_reward} tokens)>"

class TaskCompletion(Base):
    """מודל השלמת משימה"""
    __tablename__ = 'task_completions'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=False, index=True)
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
    
    __table_args__ = (
        Index('idx_task_completion_user_task_date', 'telegram_id', 'task_id', func.date(completed_at)),
    )
    
    def __repr__(self):
        return f"<TaskCompletion user:{self.telegram_id} task:{self.task_id}>"

class UserDailyStats(Base):
    """סטטיסטיקות יומיות של משתמש"""
    __tablename__ = 'user_daily_stats'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=False, index=True)
    date = Column(Date, nullable=False, default=date.today)
    tasks_completed = Column(Integer, default=0)
    tokens_earned = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    
    # יחסים
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_user_daily', 'telegram_id', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<UserDailyStats {self.telegram_id} on {self.date}>"

class Referral(Base):
    """מודל הפניות"""
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True)
    referrer_id = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=False, index=True)
    referred_id = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=False, unique=True)
    referral_code = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='active')
    
    # יחסים
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")
    
    def __repr__(self):
        return f"<Referral {self.referrer_id} -> {self.referred_id}>"
