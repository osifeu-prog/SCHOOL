#!/usr/bin/env python3
"""
קובץ לאתחול מסד הנתונים
"""

import sys
import os

# הוסף את התיקייה הנוכחית ל-PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔧 מאתחל מסד נתונים...")

try:
    from database.queries import init_database
    
    try:
        init_database()
        print("✅ מסד הנתונים אותחל בהצלחה!")
        print("\n📊 טבלאות שנוצרו:")
        print("   • users - משתמשים")
        print("   • attendance - נוכחות")
        print("   • tasks - משימות")
        print("   • task_completions - השלמת משימות")
        print("   • user_daily_stats - סטטיסטיקות יומיות")
        print("   • referrals - הפניות")
        
        print("\n🎯 משימות ברירת מחדל שנוספו:")
        print("   • צ'ק-אין יומי")
        print("   • תרומה לפורום")
        print("   • סיוע לתלמיד")
        print("   • הפניה של חבר")
        
        print("\n👤 משתמש דמו נוסף:")
        print("   • ID: 123456789")
        print("   • שם: משתמש דמו")
        print("   • טוקנים: 100")
        print("   • רמה: 3")
        
        print("\n🚀 המערכת מוכנה לשימוש!")
        
    except Exception as e:
        print(f"❌ שגיאה באתחול מסד הנתונים: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ שגיאה ביבוא מודולים: {e}")
    print("📦 ודא שהתלויות מותקנות: pip install -r requirements.txt")
    sys.exit(1)
