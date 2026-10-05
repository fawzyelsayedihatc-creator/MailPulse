import sqlite3

DB_NAME = "mailpulse.db"

def init_db(admin_email):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            role TEXT DEFAULT 'user',
            email_limit INTEGER DEFAULT 100,
            emails_sent INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS campaign_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            recipient_email TEXT,
            subject TEXT,
            status TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute("INSERT OR IGNORE INTO users (email, role, email_limit) VALUES (?, 'admin', 100000)", (admin_email.strip().lower(),))
    conn.commit()
    conn.close()

def get_or_create_user(email):
    email = email.strip().lower()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (email, role, email_limit, emails_sent, is_active) VALUES (?, 'user', 100, 0, 1)", (email,))
        conn.commit()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT email, role, email_limit, emails_sent, is_active FROM users")
    users = c.fetchall()
    conn.close()
    return users

def update_user_limit(email, new_limit):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET email_limit=? WHERE email=?", (new_limit, email))
    conn.commit()
    conn.close()

def update_sent_count(email, count):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET emails_sent = emails_sent + ? WHERE email=?", (count, email))
    conn.commit()
    conn.close()
