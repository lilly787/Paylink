import oracledb

def create_schema():
    conn = oracledb.connect(user='system', password='12345678', dsn='localhost:1521/XE')
    cursor = conn.cursor()

    # Drop existing tables and sequences (ignore errors if they don't exist)
    drops = [
        "DROP TABLE transfers CASCADE CONSTRAINTS",
        "DROP TABLE transactions CASCADE CONSTRAINTS",
        "DROP TABLE accounts CASCADE CONSTRAINTS",
        "DROP TABLE fraud_alerts CASCADE CONSTRAINTS",
        "DROP TABLE notifications CASCADE CONSTRAINTS",
        "DROP TABLE card_transactions CASCADE CONSTRAINTS",
        "DROP TABLE virtual_cards CASCADE CONSTRAINTS",
        "DROP TABLE customers CASCADE CONSTRAINTS",
        "DROP TABLE branches CASCADE CONSTRAINTS",
        "DROP TABLE bank_staff CASCADE CONSTRAINTS",
        "DROP TABLE audit_logs CASCADE CONSTRAINTS",
        "DROP SEQUENCE branches_seq",
        "DROP SEQUENCE customers_seq",
        "DROP SEQUENCE accounts_seq",
        "DROP SEQUENCE transactions_seq",
        "DROP SEQUENCE transfers_seq",
        "DROP SEQUENCE audit_logs_seq",
        "DROP SEQUENCE bank_staff_seq",
        "DROP SEQUENCE virtual_cards_seq",
        "DROP SEQUENCE card_txns_seq",
        "DROP SEQUENCE notifications_seq",
        "DROP SEQUENCE fraud_alerts_seq"
    ]
    for d in drops:
        try: cursor.execute(d)
        except: pass

    # Create Tables
    tables = [
        """CREATE TABLE branches (
            branch_id NUMBER PRIMARY KEY,
            branch_name VARCHAR2(100) NOT NULL,
            location VARCHAR2(150) NOT NULL,
            branch_code VARCHAR2(10) UNIQUE NOT NULL
        )""",
        """CREATE TABLE customers (
            customer_id NUMBER PRIMARY KEY,
            fullname VARCHAR2(100) NOT NULL,
            email VARCHAR2(100) UNIQUE NOT NULL,
            phone VARCHAR2(20),
            password_hash VARCHAR2(64) NOT NULL,
            pin_hash VARCHAR2(64) NOT NULL,
            status VARCHAR2(15) DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )""",
        """CREATE TABLE accounts (
            account_id NUMBER PRIMARY KEY,
            customer_id NUMBER NOT NULL,
            account_number VARCHAR2(10) UNIQUE NOT NULL,
            account_type VARCHAR2(10) NOT NULL CHECK (account_type IN ('savings', 'current')),
            balance NUMBER(15,2) DEFAULT 0.00 NOT NULL,
            is_frozen NUMBER(1) DEFAULT 0 NOT NULL CHECK (is_frozen IN (0,1)),
            branch_id NUMBER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT fk_acc_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
            CONSTRAINT fk_acc_branch FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
        )""",
        """CREATE TABLE transactions (
            transaction_id NUMBER PRIMARY KEY,
            account_id NUMBER NOT NULL,
            type VARCHAR2(10) NOT NULL CHECK (type IN ('income', 'expense')),
            amount NUMBER(15,2) NOT NULL CHECK (amount > 0),
            title VARCHAR2(100) NOT NULL,
            description VARCHAR2(250),
            reference VARCHAR2(20) UNIQUE NOT NULL,
            category VARCHAR2(30) DEFAULT 'transfer' NOT NULL,
            status VARCHAR2(10) DEFAULT 'success' NOT NULL CHECK (status IN ('success', 'failed')),
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            receipt_json VARCHAR2(2000),
            CONSTRAINT fk_txn_account FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
        )""",
        """CREATE TABLE transfers (
            transfer_id NUMBER PRIMARY KEY,
            source_account_id NUMBER NOT NULL,
            destination_account_id NUMBER NOT NULL,
            amount NUMBER(15,2) NOT NULL CHECK (amount > 0),
            reference VARCHAR2(20) UNIQUE NOT NULL,
            description VARCHAR2(250),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT fk_trf_source FOREIGN KEY (source_account_id) REFERENCES accounts(account_id),
            CONSTRAINT fk_trf_dest FOREIGN KEY (destination_account_id) REFERENCES accounts(account_id)
        )""",
        """CREATE TABLE audit_logs (
            log_id NUMBER PRIMARY KEY,
            actor_id NUMBER,
            actor_type VARCHAR2(15) CHECK (actor_type IN ('customer', 'staff', 'system')),
            action VARCHAR2(50) NOT NULL,
            description VARCHAR2(500) NOT NULL,
            status VARCHAR2(10) DEFAULT 'success' NOT NULL CHECK (status IN ('success', 'failed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )""",
        """CREATE TABLE bank_staff (
            staff_id NUMBER PRIMARY KEY,
            fullname VARCHAR2(100) NOT NULL,
            email VARCHAR2(100) UNIQUE NOT NULL,
            role VARCHAR2(15) CHECK (role IN ('admin', 'support')),
            password_hash VARCHAR2(64) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )""",
        """CREATE TABLE virtual_cards (
            card_id NUMBER PRIMARY KEY,
            customer_id NUMBER NOT NULL,
            card_number VARCHAR2(16) UNIQUE NOT NULL,
            card_holder VARCHAR2(100) NOT NULL,
            expiry_date VARCHAR2(5) NOT NULL,
            cvv VARCHAR2(3) NOT NULL,
            balance NUMBER(15,2) DEFAULT 0.00 NOT NULL,
            is_frozen NUMBER(1) DEFAULT 0 NOT NULL CHECK (is_frozen IN (0,1)),
            CONSTRAINT fk_card_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
        )""",
        """CREATE TABLE card_transactions (
            card_txn_id NUMBER PRIMARY KEY,
            card_id NUMBER NOT NULL,
            amount NUMBER(15,2) NOT NULL CHECK (amount > 0),
            merchant VARCHAR2(100) NOT NULL,
            status VARCHAR2(10) NOT NULL CHECK (status IN ('approved', 'declined')),
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT fk_card_txn FOREIGN KEY (card_id) REFERENCES virtual_cards(card_id) ON DELETE CASCADE
        )""",
        """CREATE TABLE notifications (
            notification_id NUMBER PRIMARY KEY,
            customer_id NUMBER NOT NULL,
            type VARCHAR2(10) NOT NULL CHECK (type IN ('success', 'warning', 'info')),
            title VARCHAR2(100) NOT NULL,
            message VARCHAR2(500) NOT NULL,
            is_read NUMBER(1) DEFAULT 0 NOT NULL CHECK (is_read IN (0,1)),
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT fk_notif_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
        )""",
        """CREATE TABLE fraud_alerts (
            alert_id NUMBER PRIMARY KEY,
            customer_id NUMBER NOT NULL,
            type VARCHAR2(30) NOT NULL CHECK (type IN ('large_transfer', 'rapid_withdrawals', 'suspicious_activity')),
            transaction_id NUMBER,
            description VARCHAR2(500) NOT NULL,
            status VARCHAR2(10) DEFAULT 'pending' NOT NULL CHECK (status IN ('pending', 'resolved')),
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT fk_fraud_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
        )"""
    ]

    for t in tables:
        try: cursor.execute(t)
        except Exception as e: print(f"Error creating table: {e}")

    # Create Sequences
    sequences = [
        "CREATE SEQUENCE branches_seq START WITH 1 INCREMENT BY 1 NOCACHE",
        "CREATE SEQUENCE customers_seq START WITH 1 INCREMENT BY 1 NOCACHE",
        "CREATE SEQUENCE accounts_seq START WITH 1 INCREMENT BY 1 NOCACHE",
        "CREATE SEQUENCE transactions_seq START WITH 1 INCREMENT BY 1 NOCACHE",
        "CREATE SEQUENCE transfers_seq START WITH 1 INCREMENT BY 1 NOCACHE",
        "CREATE SEQUENCE audit_logs_seq START WITH 1 INCREMENT BY 1 NOCACHE",
        "CREATE SEQUENCE bank_staff_seq START WITH 1 INCREMENT BY 1 NOCACHE",
        "CREATE SEQUENCE virtual_cards_seq START WITH 1 INCREMENT BY 1 NOCACHE",
        "CREATE SEQUENCE card_txns_seq START WITH 1 INCREMENT BY 1 NOCACHE",
        "CREATE SEQUENCE notifications_seq START WITH 1 INCREMENT BY 1 NOCACHE",
        "CREATE SEQUENCE fraud_alerts_seq START WITH 1 INCREMENT BY 1 NOCACHE"
    ]
    for s in sequences:
        try: cursor.execute(s)
        except Exception as e: print(f"Error creating sequence: {e}")

    # Create Triggers
    triggers = [
        "CREATE OR REPLACE TRIGGER branches_bi_trg BEFORE INSERT ON branches FOR EACH ROW BEGIN IF :new.branch_id IS NULL THEN SELECT branches_seq.NEXTVAL INTO :new.branch_id FROM dual; END IF; END;",
        "CREATE OR REPLACE TRIGGER customers_bi_trg BEFORE INSERT ON customers FOR EACH ROW BEGIN IF :new.customer_id IS NULL THEN SELECT customers_seq.NEXTVAL INTO :new.customer_id FROM dual; END IF; END;",
        "CREATE OR REPLACE TRIGGER accounts_bi_trg BEFORE INSERT ON accounts FOR EACH ROW BEGIN IF :new.account_id IS NULL THEN SELECT accounts_seq.NEXTVAL INTO :new.account_id FROM dual; END IF; END;",
        "CREATE OR REPLACE TRIGGER transactions_bi_trg BEFORE INSERT ON transactions FOR EACH ROW BEGIN IF :new.transaction_id IS NULL THEN SELECT transactions_seq.NEXTVAL INTO :new.transaction_id FROM dual; END IF; END;",
        "CREATE OR REPLACE TRIGGER transfers_bi_trg BEFORE INSERT ON transfers FOR EACH ROW BEGIN IF :new.transfer_id IS NULL THEN SELECT transfers_seq.NEXTVAL INTO :new.transfer_id FROM dual; END IF; END;",
        "CREATE OR REPLACE TRIGGER audit_logs_bi_trg BEFORE INSERT ON audit_logs FOR EACH ROW BEGIN IF :new.log_id IS NULL THEN SELECT audit_logs_seq.NEXTVAL INTO :new.log_id FROM dual; END IF; END;",
        "CREATE OR REPLACE TRIGGER bank_staff_bi_trg BEFORE INSERT ON bank_staff FOR EACH ROW BEGIN IF :new.staff_id IS NULL THEN SELECT bank_staff_seq.NEXTVAL INTO :new.staff_id FROM dual; END IF; END;",
        "CREATE OR REPLACE TRIGGER virtual_cards_bi_trg BEFORE INSERT ON virtual_cards FOR EACH ROW BEGIN IF :new.card_id IS NULL THEN SELECT virtual_cards_seq.NEXTVAL INTO :new.card_id FROM dual; END IF; END;",
        "CREATE OR REPLACE TRIGGER card_txns_bi_trg BEFORE INSERT ON card_transactions FOR EACH ROW BEGIN IF :new.card_txn_id IS NULL THEN SELECT card_txns_seq.NEXTVAL INTO :new.card_txn_id FROM dual; END IF; END;",
        "CREATE OR REPLACE TRIGGER notifications_bi_trg BEFORE INSERT ON notifications FOR EACH ROW BEGIN IF :new.notification_id IS NULL THEN SELECT notifications_seq.NEXTVAL INTO :new.notification_id FROM dual; END IF; END;",
        "CREATE OR REPLACE TRIGGER fraud_alerts_bi_trg BEFORE INSERT ON fraud_alerts FOR EACH ROW BEGIN IF :new.alert_id IS NULL THEN SELECT fraud_alerts_seq.NEXTVAL INTO :new.alert_id FROM dual; END IF; END;"
    ]
    for trg in triggers:
        try: cursor.execute(trg)
        except Exception as e: print(f"Error creating trigger: {e}")

    conn.commit()
    conn.close()
    print("ALL ORACLE SCHEMA OBJECTS CREATED SAFELY!")

if __name__ == '__main__':
    create_schema()
