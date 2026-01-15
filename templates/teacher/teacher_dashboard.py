<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>דשבורד מורה - Crypto-Class</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <style>
        .teacher-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            border-radius: 0 0 20px 20px;
            margin-bottom: 30px;
        }
        
        .teacher-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .teacher-nav h1 {
            margin: 0;
            font-size: 1.8rem;
        }
        
        .nav-links {
            display: flex;
            gap: 15px;
        }
        
        .nav-link {
            color: white;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 5px;
            transition: background 0.3s;
        }
        
        .nav-link:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            transition: transform 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
            display: block;
        }
        
        .stat-number {
            font-size: 2.2rem;
            font-weight: bold;
            color: #4c51bf;
            margin: 10px 0;
        }
        
        .stat-label {
            color: #718096;
            font-size: 0.95rem;
        }
        
        .top-users {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin: 30px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        
        .user-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #f1f1f1;
        }
        
        .user-item:last-child {
            border-bottom: none;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .user-avatar {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        
        .user-name {
            font-weight: bold;
            color: #2d3748;
        }
        
        .user-details {
            font-size: 0.9rem;
            color: #718096;
        }
        
        .user-tokens {
            font-weight: bold;
            color: #4c51bf;
            font-size: 1.1rem;
        }
        
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }
        
        .action-btn {
            background: white;
            border: 2px solid #4c51bf;
            color: #4c51bf;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .action-btn:hover {
            background: #4c51bf;
            color: white;
        }
        
        .logout-btn {
            background: #f56565;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
        }
        
        .logout-btn:hover {
            background: #e53e3e;
        }
        
        @media (max-width: 768px) {
            .teacher-nav {
                flex-direction: column;
                gap: 15px;
            }
            
            .nav-links {
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .quick-actions {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="teacher-header">
        <div class="container">
            <div class="teacher-nav">
                <h1>👨‍🏫 דשבורד מורה - Crypto-Class</h1>
                <div class="nav-links">
                    <a href="/teacher" class="nav-link">🏠 דשבורד</a>
                    <a href="/teacher/users" class="nav-link">👥 משתמשים</a>
                    <a href="/" class="nav-link">🌐 אתר ראשי</a>
                    <a href="/teacher/logout" class="logout-btn">🚪 יציאה</a>
                </div>
            </div>
            
            <p>ניהול כיתה מתקדם מבוסס טוקנים</p>
        </div>
    </div>
    
    <div class="container">
        <!-- סטטיסטיקות מהירות -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-number">{{ stats.total_users|default(0)|intcomma }}</div>
                <div class="stat-label">משתמשים רשומים</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">📅</div>
                <div class="stat-number">{{ stats.active_today|default(0)|intcomma }}</div>
                <div class="stat-label">פעילים היום</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">💰</div>
                <div class="stat-number">{{ stats.total_tokens|default(0)|intcomma }}</div>
                <div class="stat-label">טוקנים כוללים</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">📈</div>
                <div class="stat-number">{{ stats.avg_tokens|default(0)|round(1) }}</div>
                <div class="stat-label">טוקנים ממוצע</div>
            </div>
        </div>
        
        <!-- פעולות מהירות -->
        <div class="quick-actions">
            <a href="/teacher/users" class="action-btn">👥 ניהול משתמשים</a>
            <a href="/stats" class="action-btn">📊 סטטיסטיקות מלאות</a>
            <a href="/health" class="action-btn">🩺 בריאות מערכת</a>
            <a href="/setwebhook" class="action-btn">🔗 הגדרות Webhook</a>
        </div>
        
        <!-- משתמשים מובילים -->
        <div class="top-users">
            <h2 style="color: #2d3748; margin-bottom: 20px;">🏆 5 המובילים בטוקנים</h2>
            
            {% if top_users %}
                {% for user in top_users[:5] %}
                <div class="user-item">
                    <div class="user-info">
                        <div class="user-avatar">
                            {{ user.first_name[0] if user.first_name else '?' }}
                        </div>
                        <div>
                            <div class="user-name">
                                {{ user.first_name or user.username or ("משתמש " ~ user.telegram_id) }}
                            </div>
                            <div class="user-details">
                                רמה {{ user.level }} • {{ user.total_referrals }} הפניות
                            </div>
                        </div>
                    </div>
                    <div class="user-tokens">
                        {{ user.tokens|intcomma }} טוקנים
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div style="text-align: center; padding: 40px; color: #718096;">
                    <div style="font-size: 3rem; margin-bottom: 20px;">📭</div>
                    <h3 style="color: #2d3748;">אין משתמשים עדיין</h3>
                    <p>המערכת מחכה למשתמשים הראשונים שיצטרפו.</p>
                </div>
            {% endif %}
        </div>
        
        <!-- מידע טכני -->
        <div style="background: #f8f9fa; border-radius: 15px; padding: 25px; margin: 30px 0;">
            <h3 style="color: #2d3748; margin-bottom: 20px;">ℹ️ מידע טכני</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                <div>
                    <h4 style="color: #4c51bf; font-size: 1rem; margin-bottom: 10px;">📊 סטטיסטיקות</h4>
                    <p style="color: #718096; font-size: 0.9rem;">
                        • משתמשים: {{ stats.total_users|default(0) }}<br>
                        • פעילים היום: {{ stats.active_today|default(0) }}<br>
                        • טוקנים כוללים: {{ stats.total_tokens|default(0) }}
                    </p>
                </div>
                
                <div>
                    <h4 style="color: #4c51bf; font-size: 1rem; margin-bottom: 10px;">🔗 קישורים מהירים</h4>
                    <p style="color: #718096; font-size: 0.9rem;">
                        <a href="/api/v1/stats" style="color: #667eea;">API סטטיסטיקות</a><br>
                        <a href="/api/v1/checkin_data/7" style="color: #667eea;">API צ'ק-אין</a><br>
                        <a href="/health" style="color: #667eea;">בריאות מערכת</a>
                    </p>
                </div>
                
                <div>
                    <h4 style="color: #4c51bf; font-size: 1rem; margin-bottom: 10px;">⚙️ ניהול</h4>
                    <p style="color: #718096; font-size: 0.9rem;">
                        • סיסמת מורה: ******<br>
                        • גרסה: 2.2.0<br>
                        • סביבה: {{ 'Production' if stats.total_users else 'Development' }}
                    </p>
                </div>
            </div>
        </div>
    </div>
    
    <div style="text-align: center; padding: 40px; color: #718096; border-top: 1px solid #e2e8f0; margin-top: 40px;">
        <p>Crypto-Class © 2026 | דשבורד מורים | גרסה 2.2.0</p>
        <p style="margin-top: 10px; font-size: 0.9rem;">
            זמין גם בבוט הטלגרם ובאתר הראשי
        </p>
    </div>
    
    <script>
        // פונקציית עזר לפורמט מספרים
        function intcomma(x) {
            return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }
        
        // החל פורמט מספרים על כל המספרים בדף
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.stat-number').forEach(el => {
                const text = el.textContent;
                const number = text.replace(/,/g, '');
                if (!isNaN(number) && number.trim() !== '') {
                    el.textContent = intcomma(parseInt(number));
                }
            });
            
            document.querySelectorAll('.user-tokens').forEach(el => {
                const text = el.textContent;
                const number = text.match(/\d+/g);
                if (number) {
                    el.textContent = intcomma(number[0]) + ' טוקנים';
                }
            });
        });
    </script>
</body>
</html>
