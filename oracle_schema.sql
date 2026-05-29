-- ====================================================================
-- CSC 302: Enterprise Banking Relational Schema & Database Engineering
-- Veritas Microfinance Bank SQL & PL/SQL DDL Script
-- ====================================================================

-- 1. DROP EXISTING CONSTRAINTS AND TABLES (FOR CLEAN RE-RUNS)
BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE transfers CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE transactions CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE accounts CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE fraud_alerts CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE notifications CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE card_transactions CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE virtual_cards CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE customers CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE branches CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE bank_staff CASCADE CONSTRAINTS';
   EXECUTE IMMEDIATE 'DROP TABLE audit_logs CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN NULL;
END;
/

BEGIN
   EXECUTE IMMEDIATE 'DROP SEQUENCE branches_seq';
   EXECUTE IMMEDIATE 'DROP SEQUENCE customers_seq';
   EXECUTE IMMEDIATE 'DROP SEQUENCE accounts_seq';
   EXECUTE IMMEDIATE 'DROP SEQUENCE transactions_seq';
   EXECUTE IMMEDIATE 'DROP SEQUENCE transfers_seq';
   EXECUTE IMMEDIATE 'DROP SEQUENCE audit_logs_seq';
   EXECUTE IMMEDIATE 'DROP SEQUENCE bank_staff_seq';
   EXECUTE IMMEDIATE 'DROP SEQUENCE virtual_cards_seq';
   EXECUTE IMMEDIATE 'DROP SEQUENCE card_txns_seq';
   EXECUTE IMMEDIATE 'DROP SEQUENCE notifications_seq';
   EXECUTE IMMEDIATE 'DROP SEQUENCE fraud_alerts_seq';
EXCEPTION WHEN OTHERS THEN NULL;
END;
/


-- ====================================================================
-- PART 3 & PART 5: Relational Design (3NF tables)
-- ====================================================================

-- A. Branches Table (Resolves transitive dependencies from Accounts)
CREATE TABLE branches (
    branch_id NUMBER PRIMARY KEY,
    branch_name VARCHAR2(100) NOT NULL,
    location VARCHAR2(150) NOT NULL,
    branch_code VARCHAR2(10) UNIQUE NOT NULL
);

-- B. Customers Table
CREATE TABLE customers (
    customer_id NUMBER PRIMARY KEY,
    fullname VARCHAR2(100) NOT NULL,
    email VARCHAR2(100) UNIQUE NOT NULL,
    phone VARCHAR2(20),
    password_hash VARCHAR2(64) NOT NULL,
    pin_hash VARCHAR2(64) NOT NULL,
    status VARCHAR2(15) DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- C. Accounts Table (FK to Customers & Branches)
CREATE TABLE accounts (
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
);

-- D. Transactions Table (FK to Accounts)
CREATE TABLE transactions (
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
);

-- E. Transfers Table (Inter-account Ledger entries)
CREATE TABLE transfers (
    transfer_id NUMBER PRIMARY KEY,
    source_account_id NUMBER NOT NULL,
    destination_account_id NUMBER NOT NULL,
    amount NUMBER(15,2) NOT NULL CHECK (amount > 0),
    reference VARCHAR2(20) UNIQUE NOT NULL,
    description VARCHAR2(250),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_trf_source FOREIGN KEY (source_account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_trf_dest FOREIGN KEY (destination_account_id) REFERENCES accounts(account_id)
);

-- F. AuditLogs Table (Independent audit tracking)
CREATE TABLE audit_logs (
    log_id NUMBER PRIMARY KEY,
    actor_id NUMBER,
    actor_type VARCHAR2(15) CHECK (actor_type IN ('customer', 'staff', 'system')),
    action VARCHAR2(50) NOT NULL,
    description VARCHAR2(500) NOT NULL,
    status VARCHAR2(10) DEFAULT 'success' NOT NULL CHECK (status IN ('success', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- G. BankStaff Table
CREATE TABLE bank_staff (
    staff_id NUMBER PRIMARY KEY,
    fullname VARCHAR2(100) NOT NULL,
    email VARCHAR2(100) UNIQUE NOT NULL,
    role VARCHAR2(15) CHECK (role IN ('admin', 'support')),
    password_hash VARCHAR2(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- H. Virtual Cards Table
CREATE TABLE virtual_cards (
    card_id NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL,
    card_number VARCHAR2(16) UNIQUE NOT NULL,
    card_holder VARCHAR2(100) NOT NULL,
    expiry_date VARCHAR2(5) NOT NULL,
    cvv VARCHAR2(3) NOT NULL,
    balance NUMBER(15,2) DEFAULT 0.00 NOT NULL,
    is_frozen NUMBER(1) DEFAULT 0 NOT NULL CHECK (is_frozen IN (0,1)),
    CONSTRAINT fk_card_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- I. Card Transactions Table
CREATE TABLE card_transactions (
    card_txn_id NUMBER PRIMARY KEY,
    card_id NUMBER NOT NULL,
    amount NUMBER(15,2) NOT NULL CHECK (amount > 0),
    merchant VARCHAR2(100) NOT NULL,
    status VARCHAR2(10) NOT NULL CHECK (status IN ('approved', 'declined')),
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_card_txn FOREIGN KEY (card_id) REFERENCES virtual_cards(card_id) ON DELETE CASCADE
);

-- J. Notifications Table
CREATE TABLE notifications (
    notification_id NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL,
    type VARCHAR2(10) NOT NULL CHECK (type IN ('success', 'warning', 'info')),
    title VARCHAR2(100) NOT NULL,
    message VARCHAR2(500) NOT NULL,
    is_read NUMBER(1) DEFAULT 0 NOT NULL CHECK (is_read IN (0,1)),
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_notif_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- K. Fraud Alerts Table
CREATE TABLE fraud_alerts (
    alert_id NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL,
    type VARCHAR2(30) NOT NULL CHECK (type IN ('large_transfer', 'rapid_withdrawals', 'suspicious_activity')),
    transaction_id NUMBER,
    description VARCHAR2(500) NOT NULL,
    status VARCHAR2(10) DEFAULT 'pending' NOT NULL CHECK (status IN ('pending', 'resolved')),
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_fraud_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);


-- ====================================================================
-- PART 5: Sequences & Key Autoincrement Triggers
-- ====================================================================

CREATE SEQUENCE branches_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE customers_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE accounts_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE transactions_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE transfers_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE audit_logs_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE bank_staff_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE virtual_cards_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE card_txns_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE notifications_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE fraud_alerts_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE OR REPLACE TRIGGER branches_bi_trg BEFORE INSERT ON branches FOR EACH ROW
BEGIN IF :new.branch_id IS NULL THEN SELECT branches_seq.NEXTVAL INTO :new.branch_id FROM dual; END IF; END;
/
CREATE OR REPLACE TRIGGER customers_bi_trg BEFORE INSERT ON customers FOR EACH ROW
BEGIN IF :new.customer_id IS NULL THEN SELECT customers_seq.NEXTVAL INTO :new.customer_id FROM dual; END IF; END;
/
CREATE OR REPLACE TRIGGER accounts_bi_trg BEFORE INSERT ON accounts FOR EACH ROW
BEGIN IF :new.account_id IS NULL THEN SELECT accounts_seq.NEXTVAL INTO :new.account_id FROM dual; END IF; END;
/
CREATE OR REPLACE TRIGGER transactions_bi_trg BEFORE INSERT ON transactions FOR EACH ROW
BEGIN IF :new.transaction_id IS NULL THEN SELECT transactions_seq.NEXTVAL INTO :new.transaction_id FROM dual; END IF; END;
/
CREATE OR REPLACE TRIGGER transfers_bi_trg BEFORE INSERT ON transfers FOR EACH ROW
BEGIN IF :new.transfer_id IS NULL THEN SELECT transfers_seq.NEXTVAL INTO :new.transfer_id FROM dual; END IF; END;
/
CREATE OR REPLACE TRIGGER audit_logs_bi_trg BEFORE INSERT ON audit_logs FOR EACH ROW
BEGIN IF :new.log_id IS NULL THEN SELECT audit_logs_seq.NEXTVAL INTO :new.log_id FROM dual; END IF; END;
/
CREATE OR REPLACE TRIGGER bank_staff_bi_trg BEFORE INSERT ON bank_staff FOR EACH ROW
BEGIN IF :new.staff_id IS NULL THEN SELECT bank_staff_seq.NEXTVAL INTO :new.staff_id FROM dual; END IF; END;
/
CREATE OR REPLACE TRIGGER virtual_cards_bi_trg BEFORE INSERT ON virtual_cards FOR EACH ROW
BEGIN IF :new.card_id IS NULL THEN SELECT virtual_cards_seq.NEXTVAL INTO :new.card_id FROM dual; END IF; END;
/
CREATE OR REPLACE TRIGGER card_txns_bi_trg BEFORE INSERT ON card_transactions FOR EACH ROW
BEGIN IF :new.card_txn_id IS NULL THEN SELECT card_txns_seq.NEXTVAL INTO :new.card_txn_id FROM dual; END IF; END;
/
CREATE OR REPLACE TRIGGER notifications_bi_trg BEFORE INSERT ON notifications FOR EACH ROW
BEGIN IF :new.notification_id IS NULL THEN SELECT notifications_seq.NEXTVAL INTO :new.notification_id FROM dual; END IF; END;
/
CREATE OR REPLACE TRIGGER fraud_alerts_bi_trg BEFORE INSERT ON fraud_alerts FOR EACH ROW
BEGIN IF :new.alert_id IS NULL THEN SELECT fraud_alerts_seq.NEXTVAL INTO :new.alert_id FROM dual; END IF; END;
/


-- ====================================================================
-- PART 8: Automated Triggers for Security and Auditing
-- ====================================================================

-- Trigger: Audit balance updates and freeze actions automatically on accounts
CREATE OR REPLACE TRIGGER audit_accounts_updates_trg
AFTER UPDATE ON accounts FOR EACH ROW
BEGIN
    -- Log balance fluctuations
    IF :old.balance != :new.balance THEN
        INSERT INTO audit_logs (actor_id, actor_type, action, description, status, created_at)
        VALUES (:new.customer_id, 'customer', 'BALANCE_UPDATE', 
                'Account ' || :new.account_number || ' balance updated from ₦' || 
                TO_CHAR(:old.balance, '999,999,990.99') || ' to ₦' || TO_CHAR(:new.balance, '999,999,990.99'),
                'success', CURRENT_TIMESTAMP);
    END IF;

    -- Log account freezes or activations
    IF :old.is_frozen != :new.is_frozen THEN
        DECLARE
            v_action VARCHAR2(30);
            v_desc VARCHAR2(100);
        BEGIN
            IF :new.is_frozen = 1 THEN
                v_action := 'ACCOUNT_FREEZE';
                v_desc := 'Account ' || :new.account_number || ' has been suspended and frozen.';
            ELSE
                v_action := 'ACCOUNT_UNFREEZE';
                v_desc := 'Account ' || :new.account_number || ' has been reactivated.';
            END IF;

            INSERT INTO audit_logs (actor_id, actor_type, action, description, status, created_at)
            VALUES (:new.customer_id, 'customer', v_action, v_desc, 'success', CURRENT_TIMESTAMP);
        END;
    END IF;
END;
/


-- ====================================================================
-- PART 7: PL/SQL Stored Procedures (ACID Transaction handling)
-- ====================================================================

-- 1. Stored Procedure: DEPOSIT_PROC
CREATE OR REPLACE PROCEDURE DEPOSIT_PROC (
    p_account_number IN VARCHAR2,
    p_amount IN NUMBER,
    p_title IN VARCHAR2,
    p_description IN VARCHAR2,
    p_category IN VARCHAR2,
    p_reference IN VARCHAR2
) AS
    v_account_id NUMBER;
    v_frozen NUMBER(1);
BEGIN
    -- Validate amount
    IF p_amount <= 0 THEN
        raise_application_error(-20001, 'Deposit amount must be positive.');
    END IF;

    -- Retrieve account parameters
    SELECT account_id, is_frozen INTO v_account_id, v_frozen 
    FROM accounts WHERE account_number = p_account_number;

    -- Validate frozen status
    IF v_frozen = 1 THEN
        raise_application_error(-20002, 'Cannot deposit to a frozen account.');
    END IF;

    -- Perform balance increment
    UPDATE accounts SET balance = balance + p_amount WHERE account_id = v_account_id;

    -- Write Transaction entry
    INSERT INTO transactions (account_id, type, amount, title, description, reference, category, status, date_created)
    VALUES (v_account_id, 'income', p_amount, p_title, p_description, p_reference, p_category, 'success', CURRENT_TIMESTAMP);

    COMMIT;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        raise_application_error(-20003, 'Account not found: ' || p_account_number);
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END DEPOSIT_PROC;
/

-- 2. Stored Procedure: WITHDRAW_PROC
CREATE OR REPLACE PROCEDURE WITHDRAW_PROC (
    p_account_number IN VARCHAR2,
    p_amount IN NUMBER,
    p_title IN VARCHAR2,
    p_description IN VARCHAR2,
    p_category IN VARCHAR2,
    p_reference IN VARCHAR2
) AS
    v_account_id NUMBER;
    v_balance NUMBER(15,2);
    v_frozen NUMBER(1);
    v_type VARCHAR2(10);
    v_min_allowed NUMBER(15,2);
BEGIN
    -- Validate amount
    IF p_amount <= 0 THEN
        raise_application_error(-20001, 'Withdrawal amount must be positive.');
    END IF;

    -- Retrieve account parameters
    SELECT account_id, balance, is_frozen, account_type INTO v_account_id, v_balance, v_frozen, v_type
    FROM accounts WHERE account_number = p_account_number;

    -- Validate frozen status
    IF v_frozen = 1 THEN
        raise_application_error(-20002, 'Withdrawal blocked: Account is frozen.');
    END IF;

    -- Enforce account limits polymorphically in PL/SQL
    IF v_type = 'savings' THEN
        v_min_allowed := 5000.00; -- Savings account minimum floor
        IF p_amount > 50000.00 THEN
            raise_application_error(-20004, 'Savings account limit exceeded (Max ₦50,000 per transaction).');
        END IF;
    ELSE
        v_min_allowed := -100000.00; -- Current account overdraft floor
        IF p_amount > 500000.00 THEN
            raise_application_error(-20005, 'Current account limit exceeded (Max ₦500,000 per transaction).');
        END IF;
    END IF;

    -- Enforce balance limits
    IF (v_balance - p_amount) < v_min_allowed THEN
        raise_application_error(-20006, 'Insufficient funds: Transaction would exceed allowed account limits.');
    END IF;

    -- Execute balance decrement
    UPDATE accounts SET balance = balance - p_amount WHERE account_id = v_account_id;

    -- Write Transaction entry
    INSERT INTO transactions (account_id, type, amount, title, description, reference, category, status, date_created)
    VALUES (v_account_id, 'expense', p_amount, p_title, p_description, p_reference, p_category, 'success', CURRENT_TIMESTAMP);

    COMMIT;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        raise_application_error(-20003, 'Account not found: ' || p_account_number);
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END WITHDRAW_PROC;
/

-- 3. Stored Procedure: TRANSFER_PROC (Guarantees ACID transactions across accounts)
CREATE OR REPLACE PROCEDURE TRANSFER_PROC (
    p_src_acc_num IN VARCHAR2,
    p_dest_acc_num IN VARCHAR2,
    p_amount IN NUMBER,
    p_description IN VARCHAR2,
    p_reference IN VARCHAR2
) AS
    v_src_id NUMBER;
    v_dest_id NUMBER;
    v_src_bal NUMBER(15,2);
    v_dest_bal NUMBER(15,2);
    v_src_frozen NUMBER(1);
    v_dest_frozen NUMBER(1);
    v_src_type VARCHAR2(10);
    v_min_allowed NUMBER(15,2);
BEGIN
    -- Prevent transfers to the same account
    IF p_src_acc_num = p_dest_acc_num THEN
        raise_application_error(-20007, 'Cannot transfer funds to the same account.');
    END IF;

    -- Validate amount
    IF p_amount <= 0 THEN
        raise_application_error(-20001, 'Transfer amount must be positive.');
    END IF;

    -- Load source accounts details
    SELECT account_id, balance, is_frozen, account_type INTO v_src_id, v_src_bal, v_src_frozen, v_src_type
    FROM accounts WHERE account_number = p_src_acc_num;

    -- Load destination accounts details
    SELECT account_id, balance, is_frozen INTO v_dest_id, v_dest_bal, v_dest_frozen
    FROM accounts WHERE account_number = p_dest_acc_num;

    -- Validate frozen status
    IF v_src_frozen = 1 THEN
        raise_application_error(-20002, 'Transfer blocked: Source account is frozen.');
    END IF;
    IF v_dest_frozen = 1 THEN
        raise_application_error(-20002, 'Transfer blocked: Recipient account is frozen.');
    END IF;

    -- Determine source minimum allowed balance
    IF v_src_type = 'savings' THEN
        v_min_allowed := 5000.00;
        IF p_amount > 50000.00 THEN
            raise_application_error(-20004, 'Savings account limit exceeded (Max ₦50,000 per transaction).');
        END IF;
    ELSE
        v_min_allowed := -100000.00;
        IF p_amount > 500000.00 THEN
            raise_application_error(-20005, 'Current account limit exceeded (Max ₦500,000 per transaction).');
        END IF;
    END IF;

    -- Check source balance
    IF (v_src_bal - p_amount) < v_min_allowed THEN
        raise_application_error(-20006, 'Insufficient funds: Transfer exceeds allowed account balance limit.');
    END IF;

    -- EXECUTE Ledgers adjustments (ACID updates)
    UPDATE accounts SET balance = balance - p_amount WHERE account_id = v_src_id;
    UPDATE accounts SET balance = balance + p_amount WHERE account_id = v_dest_id;

    -- Record transaction receipts on both ledgers
    INSERT INTO transactions (account_id, type, amount, title, description, reference, category, status, date_created)
    VALUES (v_src_id, 'expense', p_amount, 'Transfer to ' || p_dest_acc_num, p_description, p_reference, 'transfer', 'success', CURRENT_TIMESTAMP);

    INSERT INTO transactions (account_id, type, amount, title, description, reference, category, status, date_created)
    VALUES (v_dest_id, 'income', p_amount, 'Funds from ' || p_src_acc_num, 'Transfer Ref: ' || p_reference, p_reference || 'R', 'transfer', 'success', CURRENT_TIMESTAMP);

    -- Insert central transfer tracking entry
    INSERT INTO transfers (source_account_id, destination_account_id, amount, reference, description, created_at)
    VALUES (v_src_id, v_dest_id, p_amount, p_reference, p_description, CURRENT_TIMESTAMP);

    COMMIT;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        raise_application_error(-20003, 'Source or destination account number not valid.');
    WHEN OTHERS THEN
        ROLLBACK; -- ACID Rollback ensures data consistency
        RAISE;
END TRANSFER_PROC;
/


-- ====================================================================
-- PART 9: Query Optimization (Secondary Indexes)
-- ====================================================================

CREATE INDEX idx_accounts_num ON accounts(account_number);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_transactions_ref ON transactions(reference);
CREATE INDEX idx_transfers_ref ON transfers(reference);

-- Composite index for fast dashboard transaction history loads
CREATE INDEX idx_transactions_dashboard ON transactions(account_id, date_created DESC);


-- ====================================================================
-- SEED INITIAL BRANCHES DATA
-- ====================================================================
INSERT INTO branches (branch_name, location, branch_code) VALUES ('Veritas Main Branch', 'Abuja HQ', 'BR-001');
INSERT INTO branches (branch_name, location, branch_code) VALUES ('University Desk Branch', 'Campus Block A', 'BR-002');
COMMIT;
