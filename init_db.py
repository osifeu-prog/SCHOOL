#!/usr/bin/env python3
"""
קובץ לאתחול מסד הנתונים
"""

import os
import sys

# הוסף את התיקייה הנוכחית ל-PATH כדי שיוכל למצוא את המודולים
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database.db import init_database
    
    print("🔧 מאתחל מסד נתונים...")
    try:
        init_database()
        print("✅ מסד הנתונים אותחל בהצלחה!")
        print("📊 המשימות הבאות נוספו:")
        print("   • צ'ק-ין יומי")
        print("   • תרומה לפורום")
        print("   • סיוע לתלמיד")
        print("   • השתתפות בשיעור")
        print("   • הפניה של חבר")
    except Exception as e:
        print(f"❌ שגיאה באתחול מסד הנתונים: {e}")
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ שגיאה ביבוא מודולים: {e}")
    print("📦 ודא שהתלויות מותקנות: pip install -r requirements.txt")
    sys.exit(1)
