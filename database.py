"""
database.py – Bridge module for Paylink.

ALL persistence is routed through oop_banking.get_db_manager(), which returns
an OracleDatabaseManager. There is zero local database fallback here.
"""

import os
import hashlib
import random
from datetime import datetime
import oop_banking


# ---- HELPERS ----

def hash_sha256(val):
    if not val:
        return None
    return hashlib.sha256(val.encode('utf-8')).hexdigest()


def generate_unique_ref():
    return "PLK-" + "".join([str(random.randint(0, 9)) for _ in range(12)])


def _adapt_customer_to_user_dict(customer, account):
    """Adapts normalized Customer + Account objects into the legacy user-dict format for the view layer."""
    if not customer:
        return None
    acc_num = account.account_number if account else "3000000000"
    bal     = account.balance        if account else 0.0
    frozen  = 1 if (account and account.is_frozen) else 0
    return {
        "id":            customer.customer_id,
        "fullname":      customer.fullname,
        "email":         customer.email,
        "phone":         customer.phone,
        "balance":       bal,
        "password_hash": customer.password_hash,
        "pin_hash":      customer.pin_hash,
        "is_frozen":     frozen,
        "account_number": acc_num,
    }


# ---- DATABASE INIT ----

def init_db():
    """Initialises the schema via the polymorphic OOP manager."""
    mgr = oop_banking.get_db_manager()
    # Oracle schema is expected to be provisioned externally via oracle_schema.sql.
    # init_db seeds default branches and staff if needed.
    mgr.init_db()


# ---- USER FUNCTIONS ----

def register_user(fullname, email, phone, password="password", pin="1234", account_type="savings"):
    mgr      = oop_banking.get_db_manager()
    pwd_hash = hash_sha256(password)
    pin_hash = hash_sha256(pin)

    customer = mgr.register_customer(fullname, email, phone, pwd_hash, pin_hash, account_type)
    if customer:
        account  = customer.accounts[0] if customer.accounts else None
        user_dict = _adapt_customer_to_user_dict(customer, account)

        oop_banking.AuditLogger.log_activity(
            mgr, customer.customer_id, 'customer',
            'CUSTOMER_REGISTRATION',
            f"New account registered: {user_dict['account_number']}"
        )
        add_notification(
            customer.customer_id, 'success',
            'Welcome to Paylink!',
            f"Hello {fullname}, your account {user_dict['account_number']} has been created successfully."
        )
        return user_dict
    return None


def get_user(email):
    mgr      = oop_banking.get_db_manager()
    customer = mgr.get_customer(email)
    if customer:
        account = customer.accounts[0] if customer.accounts else None
        return _adapt_customer_to_user_dict(customer, account)
    return None


def get_user_by_id(user_id):
    mgr      = oop_banking.get_db_manager()
    customer = mgr.get_customer_by_id(user_id)
    if customer:
        account = customer.accounts[0] if customer.accounts else None
        return _adapt_customer_to_user_dict(customer, account)
    return None


def get_user_by_account(account_number):
    mgr     = oop_banking.get_db_manager()
    account = mgr.get_account_by_number(account_number)
    if account:
        customer = mgr.get_customer_by_id(account.customer_id)
        return _adapt_customer_to_user_dict(customer, account)
    return None


def get_all_users():
    mgr = oop_banking.get_db_manager()
    return mgr.get_all_customers()


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
    """Updates account balance via OOP models and persists to Oracle."""
    mgr      = oop_banking.get_db_manager()
    customer = mgr.get_customer_by_id(user_id)
    if not customer or not customer.accounts:
        raise oop_banking.InvalidAccountError("No account found for user.")

    account = customer.accounts[0]
    if is_expense:
        account.withdraw(amount)
    else:
        account.deposit(amount)

    # Persist the new balance through the manager
    mgr.update_account_status(account.account_id, int(account.is_frozen))  # touch row to fire trigger
    _persist_balance(mgr, account)


def _persist_balance(mgr, account):
    """Saves the in-memory account balance back to the database."""
    conn = mgr.get_connection()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE accounts SET balance = :1 WHERE account_id = :2",
        (account.balance, account.account_id)
    )
    conn.commit()
    conn.close()


def toggle_user_freeze(user_id, status):
    mgr      = oop_banking.get_db_manager()
    customer = mgr.get_customer_by_id(user_id)
    if customer and customer.accounts:
        for acc in customer.accounts:
            mgr.update_account_status(acc.account_id, status)
            oop_banking.AuditLogger.log_activity(
                mgr, user_id, 'customer',
                'ACCOUNT_FREEZE' if status == 1 else 'ACCOUNT_UNFREEZE',
                f"Account status updated for {acc.account_number}."
            )


# ---- TRANSACTION FUNCTIONS ----

def add_transaction(user_id, type_, amount, title, desc,
                    reference=None, category='transfer', receipt_data=None):
    mgr      = oop_banking.get_db_manager()
    customer = mgr.get_customer_by_id(user_id)
    if not customer or not customer.accounts:
        return None

    account = customer.accounts[0]
    ref     = reference if reference else generate_unique_ref()

    txn_id = mgr.add_transaction(
        account_id   = account.account_id,
        txn_type     = type_,
        amount       = amount,
        title        = title,
        desc         = desc,
        reference    = ref,
        category     = category,
        status       = 'success',
        receipt_data = receipt_data,
    )
    return txn_id


def get_transactions(user_id):
    mgr      = oop_banking.get_db_manager()
    customer = mgr.get_customer_by_id(user_id)
    if not customer or not customer.accounts:
        return []
    account = customer.accounts[0]
    txns    = mgr.get_transactions(account.account_id)
    return [t.to_dict() for t in txns]


def get_all_transactions():
    mgr = oop_banking.get_db_manager()
    return mgr.get_all_transactions()


def get_transaction_by_id(txn_id):
    mgr = oop_banking.get_db_manager()
    return mgr.get_transaction_by_id(txn_id)


# ---- VIRTUAL CARD FUNCTIONS ----

def create_virtual_card(user_id, card_holder, funding_amount):
    mgr = oop_banking.get_db_manager()
    try:
        card_num  = "5399" + "".join([str(random.randint(0, 9)) for _ in range(12)])
        cvv_code  = "".join([str(random.randint(0, 9)) for _ in range(3)])
        now       = datetime.now()
        exp_year  = str((now.year + 3) % 100).zfill(2)
        exp_month = str(now.month).zfill(2)
        expiry    = f"{exp_month}/{exp_year}"

        # Deduct wallet balance
        update_balance(user_id, funding_amount, is_expense=True)

        card_id = mgr.create_virtual_card(
            user_id, card_num, card_holder, expiry, cvv_code, funding_amount
        )

        add_transaction(user_id, 'expense', funding_amount,
                        'Virtual Card Created', f"Card funded with {funding_amount}",
                        category='cards')
        add_notification(user_id, 'success',
                         'Virtual Card Created',
                         f'Your Virtual Mastercard \u2022\u2022\u2022\u2022 {card_num[-4:]} has been created.')
        return card_id
    except Exception:
        return None


def get_virtual_cards(user_id):
    mgr = oop_banking.get_db_manager()
    return mgr.get_virtual_cards(user_id)


def toggle_card_freeze(card_id, status):
    mgr = oop_banking.get_db_manager()
    mgr.toggle_card_freeze(card_id, status)


def simulate_card_purchase(card_id, amount, merchant):
    mgr    = oop_banking.get_db_manager()
    result = mgr.simulate_card_purchase(card_id, amount, merchant)
    if result[0]:  # success
        customer_id = result[2]
        add_transaction(customer_id, 'expense', amount,
                        f"Card: {merchant}", f"Paid using Card",
                        category='cards')
        add_notification(customer_id, 'info',
                         'Card Charge',
                         f'Card charged {amount} at {merchant}.')
    return result[0], result[1]


def get_card_transactions(card_id):
    mgr = oop_banking.get_db_manager()
    return mgr.get_card_transactions(card_id)


# ---- NOTIFICATIONS FUNCTIONS ----

def add_notification(user_id, type_, title, message):
    mgr = oop_banking.get_db_manager()
    mgr.add_notification(user_id, type_, title, message)


def get_notifications(user_id):
    mgr = oop_banking.get_db_manager()
    return mgr.get_notifications(user_id)


def mark_notifications_read(user_id):
    mgr = oop_banking.get_db_manager()
    mgr.mark_notifications_read(user_id)


# ---- FRAUD SYSTEM FUNCTIONS ----

def add_fraud_alert(user_id, type_, txn_id, desc):
    mgr = oop_banking.get_db_manager()
    mgr.add_fraud_alert(user_id, type_, txn_id, desc)
    add_notification(user_id, 'warning',
                     'Security Alert: Suspicious Activity', desc)


def get_fraud_alerts():
    mgr = oop_banking.get_db_manager()
    return mgr.get_fraud_alerts()


def resolve_fraud_alert(alert_id):
    mgr = oop_banking.get_db_manager()
    mgr.resolve_fraud_alert(alert_id)


# ---- PURE ORACLE DB HELPERS FOR ROUTER ----

def get_db_connection():
    """Returns an active Oracle database connection from the manager."""
    return oop_banking.get_db_manager().get_connection()


def setup_pin(user_id, pin):
    """Securely updates the customer's PIN hash in the Oracle database."""
    mgr = oop_banking.get_db_manager()
    conn = mgr.get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE customers SET pin_hash = :1 WHERE customer_id = :2", (hash_sha256(pin), user_id))
    conn.commit()
    conn.close()


def update_transaction_receipt(txn_id, receipt_data):
    """Updates the JSON receipt metadata of a transaction in Oracle."""
    import json
    mgr = oop_banking.get_db_manager()
    conn = mgr.get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE transactions SET receipt_json = :1 WHERE transaction_id = :2", (json.dumps(receipt_data), txn_id))
    conn.commit()
    conn.close()


def find_user_by_fuzzy_name(name, user_id):
    """Finds a customer by fuzzy name match in Oracle, returning standard dict details."""
    mgr = oop_banking.get_db_manager()
    conn = mgr.get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT c.customer_id, c.fullname, a.account_number
        FROM customers c
        JOIN accounts a ON c.customer_id = a.customer_id
        WHERE UPPER(c.fullname) LIKE UPPER(:1) AND c.customer_id != :2
    ''', (f"%{name}%", user_id))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "fullname": row[1],
            "account_number": row[2]
        }
    return None
