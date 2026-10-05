import sqlite3

DB_NAME = "mailpulse.db"

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_db(admin_email):
    conn = get_db()
    cursor = conn.cursor()
    
    # جدول اليوزرز
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            role TEXT DEFAULT 'user',
            email_limit INTEGER DEFAULT 100,
            emails_sent INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # تعيين حساب الأدمن الرئيسي تلقائياً
    admin_clean = admin_email.strip().lower()
    cursor.execute("""
        INSERT INTO users (email, role, email_limit, is_active)
        VALUES (?, 'admin', 999999, 1)
        ON CONFLICT(email) DO UPDATE SET role='admin', is_active=1
    """, (admin_clean,))
    
    conn.commit()
    conn.close()

def get_or_create_user(email):
    email_clean = email.strip().lower()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email, role, email_limit, emails_sent, is_active FROM users WHERE email = ?", (email_clean,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("INSERT INTO users (email, role, email_limit, emails_sent, is_active) VALUES (?, 'user', 100, 0, 1)", (email_clean,))
        conn.commit()
        cursor.execute("SELECT email, role, email_limit, emails_sent, is_active FROM users WHERE email = ?", (email_clean,))
        user = cursor.fetchone()
        
    conn.close()
    return user

def update_user_limit(email, new_limit):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email_limit = ? WHERE email = ?", (new_limit, email.strip().lower()))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email, role, email_limit, emails_sent, is_active FROM users")
    users = cursor.fetchall()
    conn.close()
    return users