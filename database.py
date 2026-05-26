import sqlite3
import os
import json
import hashlib
import random
from datetime import datetime

DB_FILE = 'paylink.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Create Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            balance REAL DEFAULT 150000.00,
            password_hash TEXT,
            pin_hash TEXT,
            is_frozen INTEGER DEFAULT 0,
            account_number TEXT UNIQUE
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            title TEXT,
            description TEXT,
            reference TEXT UNIQUE,
            category TEXT DEFAULT 'transfer',
            date TEXT,
            receipt_json TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS virtual_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_number TEXT UNIQUE NOT NULL,
            card_holder TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv TEXT NOT NULL,
            balance REAL DEFAULT 10000.00,
            is_frozen INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS card_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER,
            amount REAL NOT NULL,
            merchant TEXT NOT NULL,
            status TEXT NOT NULL,
            date TEXT,
            FOREIGN KEY (card_id) REFERENCES virtual_cards (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT NOT NULL, -- 'success', 'warning', 'info'
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS fraud_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT NOT NULL, -- 'large_transfer', 'rapid_withdrawals', 'suspicious_activity'
            transaction_id INTEGER,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending', -- 'pending', 'resolved'
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 2. Database Migrations (Run ALTER TABLE commands inside try/except to upgrade existing databases)
    migrations = [
        ("ALTER TABLE users ADD COLUMN password_hash TEXT", "password_hash"),
        ("ALTER TABLE users ADD COLUMN pin_hash TEXT", "pin_hash"),
        ("ALTER TABLE users ADD COLUMN is_frozen INTEGER DEFAULT 0", "is_frozen"),
        ("ALTER TABLE users ADD COLUMN account_number TEXT", "account_number"),
        ("ALTER TABLE transactions ADD COLUMN reference TEXT", "reference"),
        ("ALTER TABLE transactions ADD COLUMN category TEXT DEFAULT 'transfer'", "category"),
        ("ALTER TABLE transactions ADD COLUMN receipt_json TEXT", "receipt_json")
    ]
    
    for sql, col in migrations:
        try:
            c.execute(sql)
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass
            
    # Seed default Nigerian bank users if users table is empty
    count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        seed_users = [
            ("Fatima Bello", "fatima@novapay.ng", "08022223333", "3055448822"),
            ("Chidera Okafor", "chidera@novapay.ng", "08033334444", "3011223344"),
            ("Emeka Nwosu", "emeka@novapay.ng", "0809876543", "3098765432"),
            ("Sarah Musa", "sarah@novapay.ng", "0802938475", "3029384756"),
            ("Aisha Ibrahim", "aisha@novapay.ng", "0807766554", "3077665544")
        ]
        default_pwd = hash_sha256("password")
        default_pin = hash_sha256("1234")
        for name, email, phone, acc_num in seed_users:
            c.execute('''
                INSERT INTO users (fullname, email, phone, balance, password_hash, pin_hash, is_frozen, account_number)
                VALUES (?, ?, ?, 150000.00, ?, ?, 0, ?)
            ''', (name, email, phone, default_pwd, default_pin, acc_num))
            
            user_id = c.lastrowid
            date_str = datetime.utcnow().isoformat() + 'Z'
            c.execute('''
                INSERT INTO notifications (user_id, type, title, message, date)
                VALUES (?, 'success', 'Welcome to NovaPay', ?, ?)
            ''', (user_id, f'Hello {name}, welcome to your premium digital bank account {acc_num}.', date_str))
            
    conn.commit()
    conn.close()

# ---- HELPERS ----

def hash_sha256(val):
    if not val:
        return None
    return hashlib.sha256(val.encode('utf-8')).hexdigest()

def generate_unique_account_num(cursor):
    while True:
        acc = "30" + "".join([str(random.randint(0, 9)) for _ in range(8)])
        cursor.execute("SELECT id FROM users WHERE account_number = ?", (acc,))
        if cursor.fetchone() is None:
            return acc

def generate_unique_ref():
    return "PLK-" + "".join([str(random.randint(0, 9)) for _ in range(12)])

# ---- USER FUNCTIONS ----

def register_user(fullname, email, phone, password="password", pin="1234"):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        acc_num = generate_unique_account_num(c)
        pwd_hash = hash_sha256(password)
        pin_hash = hash_sha256(pin)
        
        c.execute('''
            INSERT INTO users (fullname, email, phone, balance, password_hash, pin_hash, is_frozen, account_number) 
            VALUES (?, ?, ?, 150000.00, ?, ?, 0, ?)
        ''', (fullname, email, phone, pwd_hash, pin_hash, acc_num))
        conn.commit()
        user_id = c.lastrowid
        
        # Send initial registration notification
        add_notification_direct(c, user_id, 'success', 'Welcome to Paylink!', f'Hello {fullname}, your account {acc_num} has been created successfully.')
        conn.commit()
        
        return {
            "id": user_id, 
            "fullname": fullname, 
            "email": email, 
            "phone": phone, 
            "balance": 150000.00,
            "account_number": acc_num,
            "is_frozen": 0
        }
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_account(account_number):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE account_number = ?', (account_number,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY id DESC').fetchall()
    conn.close()
    return [dict(u) for u in users]

def verify_user_password(email, password):
    user = get_user(email)
    if not user:
        return None
    if user['password_hash'] == hash_sha256(password):
        return user
    return None

def verify_user_pin(user_id, pin):
    user = get_user_by_id(user_id)
    if not user:
        return False
    return user['pin_hash'] == hash_sha256(pin)

def update_balance(user_id, amount, is_expense=True):
    conn = get_db_connection()
    c = conn.cursor()
    if is_expense:
        c.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, user_id))
    else:
        c.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def toggle_user_freeze(user_id, status):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET is_frozen = ? WHERE id = ?', (status, user_id))
    conn.commit()
    conn.close()

# ---- TRANSACTION FUNCTIONS ----

def add_transaction(user_id, type_, amount, title, desc, reference=None, category='transfer', receipt_data=None):
    conn = get_db_connection()
    c = conn.cursor()
    date_str = datetime.utcnow().isoformat() + 'Z'
    ref = reference if reference else generate_unique_ref()
    receipt_json = json.dumps(receipt_data) if receipt_data else None
    
    c.execute('''
        INSERT INTO transactions (user_id, type, amount, title, description, reference, category, date, receipt_json) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, type_, amount, title, desc, ref, category, date_str, receipt_json))
    conn.commit()
    txn_id = c.lastrowid
    conn.close()
    return txn_id

def get_transactions(user_id):
    conn = get_db_connection()
    txns = conn.execute('SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
    conn.close()
    return [dict(t) for t in txns]

def get_all_transactions():
    conn = get_db_connection()
    txns = conn.execute('SELECT transactions.*, users.fullname FROM transactions JOIN users ON transactions.user_id = users.id ORDER BY transactions.id DESC').fetchall()
    conn.close()
    return [dict(t) for t in txns]

def get_transaction_by_id(txn_id):
    conn = get_db_connection()
    txn = conn.execute('SELECT * FROM transactions WHERE id = ?', (txn_id,)).fetchone()
    conn.close()
    return dict(txn) if txn else None

# ---- VIRTUAL CARD FUNCTIONS ----

def create_virtual_card(user_id, card_holder, funding_amount):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Generate card details
        card_num = "5399" + "".join([str(random.randint(0, 9)) for _ in range(12)])
        cvv_code = "".join([str(random.randint(0, 9)) for _ in range(3)])
        # Expiry 3 years from now (MM/YY)
        now = datetime.now()
        exp_year = str((now.year + 3) % 100).zfill(2)
        exp_month = str(now.month).zfill(2)
        expiry = f"{exp_month}/{exp_year}"
        
        # Deduct wallet balance
        c.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (funding_amount, user_id))
        
        # Insert Card
        c.execute('''
            INSERT INTO virtual_cards (user_id, card_number, card_holder, expiry_date, cvv, balance, is_frozen)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (user_id, card_num, card_holder, expiry, cvv_code, funding_amount))
        card_id = c.lastrowid
        
        # Record Transaction
        ref = generate_unique_ref()
        date_str = datetime.utcnow().isoformat() + 'Z'
        c.execute('''
            INSERT INTO transactions (user_id, type, amount, title, description, reference, category, date)
            VALUES (?, 'expense', ?, 'Virtual Card Created', ?, ?, 'cards', ?)
        ''', (user_id, funding_amount, f"Card funded with {funding_amount}", ref, date_str))
        
        add_notification_direct(c, user_id, 'success', 'Virtual Card Created', f'Your Virtual Mastercard •••• {card_num[-4:]} has been created.')
        conn.commit()
        return card_id
    except Exception as e:
        conn.rollback()
        return None
    finally:
        conn.close()

def get_virtual_cards(user_id):
    conn = get_db_connection()
    cards = conn.execute('SELECT * FROM virtual_cards WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return [dict(cd) for cd in cards]

def toggle_card_freeze(card_id, status):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE virtual_cards SET is_frozen = ? WHERE id = ?', (status, card_id))
    conn.commit()
    conn.close()

def simulate_card_purchase(card_id, amount, merchant):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        card = c.execute('SELECT * FROM virtual_cards WHERE id = ?', (card_id,)).fetchone()
        if not card:
            return False, "Card not found"
        card = dict(card)
        if card['is_frozen']:
            return False, "Card is frozen"
        if card['balance'] < amount:
            # Log declined card transaction
            date_str = datetime.utcnow().isoformat() + 'Z'
            c.execute('''
                INSERT INTO card_transactions (card_id, amount, merchant, status, date)
                VALUES (?, ?, ?, 'declined', ?)
            ''', (card_id, amount, merchant, date_str))
            conn.commit()
            return False, "Insufficient card balance"
        
        # Update card balance
        c.execute('UPDATE virtual_cards SET balance = balance - ? WHERE id = ?', (amount, card_id))
        
        # Log card transaction
        date_str = datetime.utcnow().isoformat() + 'Z'
        c.execute('''
            INSERT INTO card_transactions (card_id, amount, merchant, status, date)
            VALUES (?, ?, ?, 'approved', ?)
        ''', (card_id, amount, merchant, date_str))
        
        # Create user transaction entry
        ref = generate_unique_ref()
        c.execute('''
            INSERT INTO transactions (user_id, type, amount, title, description, reference, category, date)
            VALUES (?, 'expense', ?, ?, ?, ?, 'cards', ?)
        ''', (card['user_id'], amount, f"Card: {merchant}", f"Paid using Card •••• {card['card_number'][-4:]}", ref, date_str))
        
        add_notification_direct(c, card['user_id'], 'info', 'Card Charge', f'Card •••• {card["card_number"][-4:]} charged {amount} at {merchant}.')
        conn.commit()
        return True, "Purchase Approved"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_card_transactions(card_id):
    conn = get_db_connection()
    txns = conn.execute('SELECT * FROM card_transactions WHERE card_id = ? ORDER BY id DESC', (card_id,)).fetchall()
    conn.close()
    return [dict(t) for t in txns]

# ---- NOTIFICATIONS FUNCTIONS ----

def add_notification_direct(cursor, user_id, type_, title, message):
    date_str = datetime.utcnow().isoformat() + 'Z'
    cursor.execute('''
        INSERT INTO notifications (user_id, type, title, message, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, type_, title, message, date_str))

def add_notification(user_id, type_, title, message):
    conn = get_db_connection()
    c = conn.cursor()
    add_notification_direct(c, user_id, type_, title, message)
    conn.commit()
    conn.close()

def get_notifications(user_id):
    conn = get_db_connection()
    notifs = conn.execute('SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
    conn.close()
    return [dict(n) for n in notifs]

def mark_notifications_read(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# ---- FRAUD SYSTEM FUNCTIONS ----

def add_fraud_alert(user_id, type_, txn_id, desc):
    conn = get_db_connection()
    c = conn.cursor()
    date_str = datetime.utcnow().isoformat() + 'Z'
    c.execute('''
        INSERT INTO fraud_alerts (user_id, type, transaction_id, description, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, type_, txn_id, desc, date_str))
    
    # Also drop a system security warning in user notification center
    add_notification_direct(c, user_id, 'warning', 'Security Alert: Suspicious Activity', desc)
    conn.commit()
    conn.close()

def get_fraud_alerts():
    conn = get_db_connection()
    alerts = conn.execute('''
        SELECT fraud_alerts.*, users.fullname, users.email 
        FROM fraud_alerts 
        JOIN users ON fraud_alerts.user_id = users.id 
        ORDER BY fraud_alerts.id DESC
    ''').fetchall()
    conn.close()
    return [dict(a) for a in alerts]

def resolve_fraud_alert(alert_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE fraud_alerts SET status = 'resolved' WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
