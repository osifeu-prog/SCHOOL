#!/usr/bin/env python3
"""
Crypto-Class - בוט טלגרם פשוט ובדוק
"""

import os
import sys
import logging
from flask import Flask, request, jsonify

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

logger.info("🚀 מאתחל את המערכת...")

# ========== הגדרות מערכת ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 5000))

# ========== יצירת Flask app ==========
flask_app = Flask(__name__)

# ========== Webhook Endpoint ==========
@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """טיפול בפקודות מטלגרם"""
    try:
        update_data = request.get_json()
        
        if not update_data:
            return jsonify({"error": "No data"}), 400
            
        # הדפס לוג פשוט
        if 'message' in update_data and 'text' in update_data['message']:
            text = update_data['message']['text']
            user_id = update_data['message']['from']['id'] if 'from' in update_data['message'] else 'unknown'
            logger.info(f"📩 הודעה ממשתמש {user_id}: {text}")
        
        # תמיד החזר OK
        return 'OK'
        
    except Exception as e:
        logger.error(f"❌ שגיאה: {e}")
        return jsonify({"error": str(e)}), 500

# ========== דפים נוספים ==========
@flask_app.route('/')
def index():
    return '<h1>Crypto-Class Bot</h1><p>המערכת עובדת!</p>'

@flask_app.route('/health')
def health():
    return jsonify({
        "status": "healthy", 
        "bot": "active" if BOT_TOKEN else "inactive",
        "message": "✅ גרסה פשוטה ובדוקה"
    })

# ========== הרצה ==========
if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=PORT, debug=False)