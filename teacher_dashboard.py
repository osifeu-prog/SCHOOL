#!/usr/bin/env python3
"""
דשבורד למורים - Crypto-Class
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database.queries import get_system_stats, get_checkin_data, get_top_users
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('TEACHER_SECRET', 'default-secret-key-change-me')
TEACHER_PASSWORD = os.environ.get('TEACHER_PASSWORD', 'admin123')

# Middleware לאימות מורים
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'teacher_logged_in' not in session:
            return redirect(url_for('teacher_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """דף הבית הציבורי"""
    return redirect(url_for('public_stats'))

@app.route('/stats')
def public_stats():
    """דף סטטיסטיקות ציבורי"""
    stats = get_system_stats()
    checkin_data = get_checkin_data(7)
    top_users = get_top_users(10, 'tokens')
    
    return render_template('stats.html',
        top_users=top_users,
        total_users=stats.get('total_users', 0),
        active_today=stats.get('active_today', 0),
        checkin_data=checkin_data,
        now=datetime.now
    )

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == TEACHER_PASSWORD:
            session['teacher_logged_in'] = True
            return redirect(url_for('teacher_dashboard'))
        return render_template('teacher/login.html', error='סיסמה שגויה')
    
    return render_template('teacher/login.html')

@app.route('/teacher/logout')
def teacher_logout():
    session.pop('teacher_logged_in', None)
    return redirect(url_for('teacher_login'))

@app.route('/teacher')
@login_required
def teacher_dashboard():
    """דף הבית של המורה"""
    
    stats = get_system_stats()
    checkin_data = get_checkin_data(7)
    top_users = get_top_users(10, 'tokens')
    
    return render_template('teacher/dashboard.html',
        total_users=stats.get('total_users', 0),
        active_today=stats.get('active_today', 0),
        total_tokens=stats.get('total_tokens', 0),
        checkin_data=checkin_data,
        top_users=top_users
    )

@app.route('/teacher/api/stats')
@login_required
def api_stats():
    """API לסטטיסטיקות"""
    stats = get_system_stats()
    checkin_data = get_checkin_data(7)
    
    return jsonify({
        'stats': stats,
        'checkin_data': checkin_data
    })

if __name__ == '__main__':
    port = int(os.environ.get('TEACHER_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
