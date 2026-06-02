import os
import json
import random
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime

# ==========================================
# PART 2 - Custom Banking Exceptions
# ==========================================

class BankingException(Exception):
    """Base exception for all banking operations."""
    pass

class InsufficientFundsError(BankingException):
    """Raised when an account balance is below the requested withdrawal amount."""
    pass

class AccountFrozenError(BankingException):
    """Raised when operations are attempted on a frozen account."""
    pass

class InvalidAccountError(BankingException):
    """Raised when an account is not found or is invalid."""
    pass

class AuthenticationError(BankingException):
    """Raised on invalid credentials or security PIN failures."""
    pass

class DatabaseException(BankingException):
    """Raised when database connection or execution failures occur."""
    pass


# ==========================================
# PART 1 & 2 - OOP Core Models
# ==========================================

class Customer:
    """Represents a banking customer."""
    def __init__(self, customer_id, fullname, email, phone, password_hash, pin_hash, status='active', created_at=None):
        self.customer_id = customer_id
        self.fullname = fullname
        self.email = email
        self.phone = phone
        self.password_hash = password_hash
        self.pin_hash = pin_hash
        self.status = status  # 'active', 'suspended'
        self.created_at = created_at or datetime.utcnow().isoformat() + 'Z'
        self.accounts = []

    def add_account(self, account):
        """Associates an account with this customer."""
        self.accounts.append(account)

    def get_total_balance(self):
        """Polymorphically calculates total balance across all accounts."""
        return sum(account.balance for account in self.accounts if not account.is_frozen)


class Account(ABC):
    """Abstract Base Class representing a general Bank Account."""
    def __init__(self, account_id, customer_id, account_number, balance, is_frozen=0, branch_id=1, created_at=None):
        self._account_id = account_id
        self._customer_id = customer_id
        self._account_number = account_number
        self._balance = float(balance)
        self._is_frozen = int(is_frozen)
        self._branch_id = branch_id
        self._created_at = created_at or datetime.utcnow().isoformat() + 'Z'

    # --- Encapsulation: Getters and Setters ---
    @property
    def account_id(self):
        return self._account_id

    @property
    def customer_id(self):
        return self._customer_id

    @property
    def account_number(self):
        return self._account_number

    @property
    def balance(self):
        return self._balance

    @property
    def is_frozen(self):
        return bool(self._is_frozen)

    @property
    def branch_id(self):
        return self._branch_id

    @property
    def created_at(self):
        return self._created_at

    def freeze(self):
        """Freezes the account, blocking outgoing funds."""
        self._is_frozen = 1

    def unfreeze(self):
        """Unfreezes the account, permitting operations."""
        self._is_frozen = 0

    def deposit(self, amount):
        """Credits funds to the account."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self._balance += amount

    def withdraw(self, amount):
        """Debits funds from the account if validations pass."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if self.is_frozen:
            raise AccountFrozenError(f"Account {self.account_number} is frozen.")
        
        limit = self.get_withdrawal_limit()
        if amount > limit:
            raise InsufficientFundsError(f"Amount exceeds account single withdrawal limit of {limit}.")

        if self.balance - amount < self.get_minimum_balance_allowed():
            raise InsufficientFundsError("Insufficient funds to complete this withdrawal.")
        
        self._balance -= amount

    # --- Abstraction & Polymorphism ---
    @abstractmethod
    def get_account_type(self) -> str:
        """Returns account type string."""
        pass

    @abstractmethod
    def get_interest_rate(self) -> float:
        """Returns annual interest rate (e.g. 0.045 for 4.5%)."""
        pass

    @abstractmethod
    def get_withdrawal_limit(self) -> float:
        """Returns single transaction withdrawal limit."""
        pass

    @abstractmethod
    def get_minimum_balance_allowed(self) -> float:
        """Returns minimum balance floor (negative for overdraft)."""
        pass


class SavingsAccount(Account):
    """Represents a Savings Account with minimum balance criteria and interest rates."""
    def get_account_type(self) -> str:
        return 'savings'

    def get_interest_rate(self) -> float:
        return 0.15  # 15% interest p.a. (Swiss Sapphire Vault)

    def get_withdrawal_limit(self) -> float:
        return 50000.00  # ₦50,000 single transaction withdrawal limit

    def get_minimum_balance_allowed(self) -> float:
        return 5000.00  # Minimum ₦5,000 ledger balance requirement


class CurrentAccount(Account):
    """Represents a Current/Checking Account with overdraft limits."""
    def get_account_type(self) -> str:
        return 'current'

    def get_interest_rate(self) -> float:
        return 0.01  # 1% standard current account interest rate

    def get_withdrawal_limit(self) -> float:
        return 500000.00  # ₦500,000 single transaction withdrawal limit

    def get_minimum_balance_allowed(self) -> float:
        return -100000.00  # Overdraft limit allows balance to drop to -₦100,000


class Transaction:
    """Encapsulates transactional metadata and receipt formatting."""
    def __init__(self, transaction_id, account_id, txn_type, amount, title, description, reference, category, status='success', date=None, receipt_json=None):
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.type = txn_type  # 'income', 'expense'
        self.amount = float(amount)
        self.title = title
        self.description = description
        self.reference = reference
        self.category = category  # 'deposit', 'transfer', 'cards', etc.
        self.status = status  # 'success', 'failed'
        self.date = date or datetime.utcnow().isoformat() + 'Z'
        self.receipt_json = receipt_json

    def to_dict(self):
        """Converts model to dictionary representations."""
        return {
            "id": self.transaction_id,
            "account_id": self.account_id,
            "type": self.type,
            "amount": self.amount,
            "title": self.title,
            "description": self.description,
            "reference": self.reference,
            "category": self.category,
            "status": self.status,
            "date": self.date,
            "receipt_json": self.receipt_json
        }


class BankStaff:
    """Encapsulates bank employee/staff attributes."""
    def __init__(self, staff_id, fullname, email, role, password_hash, created_at=None):
        self.staff_id = staff_id
        self.fullname = fullname
        self.email = email
        self.role = role  # 'admin', 'support'
        self.password_hash = password_hash
        self.created_at = created_at or datetime.utcnow().isoformat() + 'Z'


class AuditLogger:
    """Class dedicated to recording security, transactional, and administrative logs."""
    @staticmethod
    def log_activity(db_manager, actor_id, actor_type, action, description, status='success'):
        """Logs security actions directly via the Database Manager."""
        db_manager.add_audit_log(actor_id, actor_type, action, description, status)


class TransferService:
    """Domain service managing transactional ledger movements between bank accounts."""
    @staticmethod
    def transfer_funds(db_manager, source_acc: Account, dest_acc: Account, amount: float, description: str):
        """Coordinates a fund transfer across two accounts under database isolation."""
        if source_acc.account_number == dest_acc.account_number:
            raise BankingException("Cannot transfer funds to the same account.")
        
        # Domain validation checks
        source_acc.withdraw(amount)
        dest_acc.deposit(amount)

        # Execute persistent database transaction
        ref = db_manager.transfer_funds(source_acc, dest_acc, amount, description)
        return ref


# ==========================================
# PART 3 & 5 - Relational Abstraction Layer
# ==========================================

class DatabaseManager(ABC):
    """Abstract Base Class specifying interfaces for persistent banking storage."""
    
    @abstractmethod
    def init_db(self):
        """Initializes tables, branches, and default data schema."""
        pass

    @abstractmethod
    def register_customer(self, fullname, email, phone, pwd_hash, pin_hash, account_type='savings') -> Customer:
        pass

    @abstractmethod
    def get_customer(self, email) -> Customer:
        pass

    @abstractmethod
    def get_customer_by_id(self, customer_id) -> Customer:
        pass

    @abstractmethod
    def get_account_by_number(self, account_number) -> Account:
        pass

    @abstractmethod
    def get_accounts_by_customer(self, customer_id) -> list:
        pass

    @abstractmethod
    def create_account(self, customer_id, account_type, balance, branch_id=1) -> Account:
        pass

    @abstractmethod
    def update_account_status(self, account_id, is_frozen) -> bool:
        pass

    @abstractmethod
    def add_transaction(self, account_id, txn_type, amount, title, desc, reference, category, status='success', receipt_data=None) -> int:
        pass

    @abstractmethod
    def get_transactions(self, account_id) -> list:
        pass

    @abstractmethod
    def get_all_transactions(self) -> list:
        pass

    @abstractmethod
    def get_all_customers(self) -> list:
        pass

    @abstractmethod
    def transfer_funds(self, source_acc: Account, dest_acc: Account, amount: float, description: str) -> str:
        """Executes persistent updates on both accounts and inserts transfer record atomically."""
        pass

    @abstractmethod
    def add_audit_log(self, actor_id, actor_type, action, description, status='success'):
        pass

    @abstractmethod
    def get_audit_logs(self) -> list:
        pass


# Helper function to convert DB rows into Account objects polymorphically
def row_to_account(row):
    if not row:
        return None
    acc_id, cust_id, acc_num, acc_type, bal, is_frozen, br_id, created = (
        row['account_id'], row['customer_id'], row['account_number'], 
        row['account_type'], row['balance'], row['is_frozen'], 
        row['branch_id'], row['created_at']
    )
    if acc_type == 'savings':
        return SavingsAccount(acc_id, cust_id, acc_num, bal, is_frozen, br_id, created)
    else:
        return CurrentAccount(acc_id, cust_id, acc_num, bal, is_frozen, br_id, created)





class OracleDatabaseManager(DatabaseManager):
    """
    Oracle implementation of DatabaseManager.
    Uses python-oracledb in thin mode — no Oracle Instant Client required.
    Matches the DDL in oracle_schema.sql (sequences + BEFORE INSERT triggers for PKs).
    """

    def __init__(self, dsn=None, user=None, password=None):
        self.dsn      = dsn      or os.environ.get("ORACLE_DSN",  "localhost:1521/XE")
        self.user     = user     or os.environ.get("ORACLE_USER", "system")
        self.password = password or os.environ.get("ORACLE_PWD",  "12345678")
        self._active  = False

        try:
            global oracledb
            import oracledb
            # thin mode – no need for init_oracle_client()
            self._active = True
        except ImportError:
            self._active = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def get_connection(self):
        if not self._active:
            raise DatabaseException(
                "oracledb driver is not installed. "
                "Run: pip install oracledb"
            )
        try:
            return oracledb.connect(
                user=self.user, password=self.password, dsn=self.dsn
            )
        except Exception as e:
            raise DatabaseException(f"Oracle connection failed: {e}")

    def _row_to_dict(self, cursor, row):
        """Convert a cursor row to a lowercase-keyed dict."""
        if row is None:
            return None
        return {
            col[0].lower(): val
            for col, val in zip(cursor.description, row)
        }

    def _fetchone_dict(self, cursor):
        row = cursor.fetchone()
        return self._row_to_dict(cursor, row) if row else None

    def _fetchall_dicts(self, cursor):
        rows = cursor.fetchall()
        return [self._row_to_dict(cursor, r) for r in rows]

    def _make_account(self, d) -> 'Account':
        """Build a SavingsAccount or CurrentAccount from a dict."""
        if d is None:
            return None
        acc_type = d.get('account_type', 'savings')
        cls = SavingsAccount if acc_type == 'savings' else CurrentAccount
        return cls(
            account_id     = d['account_id'],
            customer_id    = d['customer_id'],
            account_number = d['account_number'],
            balance        = float(d.get('balance', 0)),
            is_frozen      = int(d.get('is_frozen', 0)),
            branch_id      = d.get('branch_id', 1),
            created_at     = str(d.get('created_at', '')),
        )

    # ------------------------------------------------------------------
    # Schema bootstrap
    # ------------------------------------------------------------------

    def init_db(self):
        """Verify connectivity and seed default rows if needed."""
        if not self._active:
            raise RuntimeError("Oracle driver is not available. Install oracledb and ensure ORACLE_DSN, ORACLE_USER, ORACLE_PWD are configured.")
        try:
            conn = self.get_connection()
            cur  = conn.cursor()
            cur.execute("SELECT SYSDATE FROM dual")
            # Seed branches if empty
            cur.execute("SELECT COUNT(*) FROM branches")
            if cur.fetchone()[0] == 0:
                cur.execute(
                    "INSERT INTO branches (branch_name, location, branch_code) "
                    "VALUES ('Veritas Main Branch', 'Abuja HQ', 'BR-001')"
                )
                cur.execute(
                    "INSERT INTO branches (branch_name, location, branch_code) "
                    "VALUES ('University Desk Branch', 'Campus Block A', 'BR-002')"
                )
            # Seed admin staff if empty
            cur.execute("SELECT COUNT(*) FROM bank_staff")
            if cur.fetchone()[0] == 0:
                default_hash = hashlib.sha256(b"adminpassword").hexdigest()
                cur.execute(
                    "INSERT INTO bank_staff (fullname, email, role, password_hash) "
                    "VALUES ('Veritas Bank Admin', 'admin@veritasbank.edu.ng', 'admin', :1)",
                    (default_hash,)
                )
            conn.commit()
            conn.close()
            print("Oracle Database connectivity verified and schema seeded.")
        except Exception as e:
            print(f"Oracle init warning: {e}")

    # ------------------------------------------------------------------
    # Customer operations
    # ------------------------------------------------------------------

    def register_customer(self, fullname, email, phone, pwd_hash, pin_hash,
                          account_type='savings') -> 'Customer':
        conn = self.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO customers (fullname, email, phone, password_hash, pin_hash) "
                "VALUES (:1, :2, :3, :4, :5)",
                (fullname, email, phone, pwd_hash, pin_hash)
            )
            # Retrieve generated PK via sequence-powered trigger
            cur.execute("SELECT customer_id FROM customers WHERE email = :1", (email,))
            row = cur.fetchone()
            if not row:
                conn.rollback()
                return None
            cust_id = row[0]

            # Generate account number and create the account
            acc_num = "30" + "".join([str(random.randint(0, 9)) for _ in range(8)])
            cur.execute(
                "INSERT INTO accounts "
                "(customer_id, account_number, account_type, balance, branch_id) "
                "VALUES (:1, :2, :3, 150000.00, 1)",
                (cust_id, acc_num, account_type)
            )
            conn.commit()
            return self.get_customer(email)
        except Exception as e:
            conn.rollback()
            if "unique constraint" in str(e).lower() or "ORA-00001" in str(e):
                return None          # duplicate e-mail
            raise DatabaseException(f"register_customer failed: {e}")
        finally:
            conn.close()

    def get_customer(self, email) -> 'Customer':
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE email = :1", (email,))
        d = self._fetchone_dict(cur)
        conn.close()
        if not d:
            return None
        cust = Customer(
            d['customer_id'], d['fullname'], d['email'], d['phone'],
            d['password_hash'], d['pin_hash'], d.get('status', 'active'),
            str(d.get('created_at', ''))
        )
        cust.accounts = self.get_accounts_by_customer(cust.customer_id)
        return cust

    def get_customer_by_id(self, customer_id) -> 'Customer':
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE customer_id = :1", (customer_id,))
        d = self._fetchone_dict(cur)
        conn.close()
        if not d:
            return None
        cust = Customer(
            d['customer_id'], d['fullname'], d['email'], d['phone'],
            d['password_hash'], d['pin_hash'], d.get('status', 'active'),
            str(d.get('created_at', ''))
        )
        cust.accounts = self.get_accounts_by_customer(cust.customer_id)
        return cust

    def get_all_customers(self) -> list:
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT c.*, a.account_number, a.balance, a.is_frozen "
            "FROM customers c LEFT JOIN accounts a ON c.customer_id = a.customer_id "
            "ORDER BY c.customer_id"
        )
        rows = self._fetchall_dicts(cur)
        conn.close()
        result = []
        for r in rows:
            r['id'] = r['customer_id']
            result.append(r)
        return result

    # ------------------------------------------------------------------
    # Account operations
    # ------------------------------------------------------------------

    def get_account_by_number(self, account_number) -> 'Account':
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM accounts WHERE account_number = :1", (account_number,))
        d = self._fetchone_dict(cur)
        conn.close()
        return self._make_account(d)

    def get_accounts_by_customer(self, customer_id) -> list:
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM accounts WHERE customer_id = :1", (customer_id,))
        rows = self._fetchall_dicts(cur)
        conn.close()
        return [self._make_account(r) for r in rows]

    def create_account(self, customer_id, account_type, balance, branch_id=1) -> 'Account':
        conn = self.get_connection()
        cur  = conn.cursor()
        try:
            acc_num = "30" + "".join([str(random.randint(0, 9)) for _ in range(8)])
            cur.execute(
                "INSERT INTO accounts "
                "(customer_id, account_number, account_type, balance, branch_id) "
                "VALUES (:1, :2, :3, :4, :5)",
                (customer_id, acc_num, account_type, balance, branch_id)
            )
            conn.commit()
            return self.get_account_by_number(acc_num)
        except Exception as e:
            conn.rollback()
            raise DatabaseException(f"create_account failed: {e}")
        finally:
            conn.close()

    def update_account_status(self, account_id, is_frozen) -> bool:
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE accounts SET is_frozen = :1 WHERE account_id = :2",
            (is_frozen, account_id)
        )
        conn.commit()
        conn.close()
        return True

    # ------------------------------------------------------------------
    # Transaction operations
    # ------------------------------------------------------------------

    def add_transaction(self, account_id, txn_type, amount, title, desc,
                        reference, category, status='success',
                        receipt_data=None) -> int:
        conn = self.get_connection()
        cur  = conn.cursor()
        receipt_json = json.dumps(receipt_data) if receipt_data else None
        try:
            cur.execute(
                "INSERT INTO transactions "
                "(account_id, type, amount, title, description, reference, "
                " category, status, receipt_json) "
                "VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)",
                (account_id, txn_type, amount, title, desc,
                 reference, category, status, receipt_json)
            )
            conn.commit()
            # Retrieve the generated PK
            cur.execute(
                "SELECT transaction_id FROM transactions WHERE reference = :1",
                (reference,)
            )
            row = cur.fetchone()
            return row[0] if row else 0
        except Exception as e:
            conn.rollback()
            raise DatabaseException(f"add_transaction failed: {e}")
        finally:
            conn.close()

    def get_transactions(self, account_id) -> list:
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT * FROM transactions WHERE account_id = :1 "
            "ORDER BY transaction_id DESC",
            (account_id,)
        )
        rows = self._fetchall_dicts(cur)
        conn.close()
        result = []
        for r in rows:
            result.append(Transaction(
                r['transaction_id'], r['account_id'], r['type'],
                r['amount'], r['title'], r.get('description'),
                r['reference'], r['category'], r['status'],
                str(r.get('date_created', '')), r.get('receipt_json')
            ))
        return result

    def get_all_transactions(self) -> list:
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT t.*, c.fullname, a.account_number "
            "FROM transactions t "
            "JOIN accounts a ON t.account_id = a.account_id "
            "JOIN customers c ON a.customer_id = c.customer_id "
            "ORDER BY t.transaction_id DESC"
        )
        rows = self._fetchall_dicts(cur)
        conn.close()
        result = []
        for r in rows:
            r['id']      = r['transaction_id']
            r['user_id'] = r['account_id']
            result.append(r)
        return result

    def get_transaction_by_id(self, txn_id) -> dict:
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT * FROM transactions WHERE transaction_id = :1", (txn_id,)
        )
        d = self._fetchone_dict(cur)
        conn.close()
        if not d:
            return None
        d['id']      = d['transaction_id']
        d['user_id'] = d['account_id']
        return d

    # ------------------------------------------------------------------
    # Transfer funds (ACID – single connection, no autocommit)
    # ------------------------------------------------------------------

    def transfer_funds(self, source_acc: 'Account', dest_acc: 'Account',
                       amount: float, description: str) -> str:
        conn = self.get_connection()
        cur  = conn.cursor()
        ref = "PLK-" + "".join([str(random.randint(0, 9)) for _ in range(12)])
        try:
            # Persist updated balances
            cur.execute(
                "UPDATE accounts SET balance = :1 WHERE account_id = :2",
                (source_acc.balance, source_acc.account_id)
            )
            cur.execute(
                "UPDATE accounts SET balance = :1 WHERE account_id = :2",
                (dest_acc.balance, dest_acc.account_id)
            )
            # Debit leg
            cur.execute(
                "INSERT INTO transactions "
                "(account_id, type, amount, title, description, reference, category, status) "
                "VALUES (:1, 'expense', :2, :3, :4, :5, 'transfer', 'success')",
                (source_acc.account_id, amount,
                 f"Transfer to {dest_acc.account_number}", description, ref)
            )
            # Credit leg
            cur.execute(
                "INSERT INTO transactions "
                "(account_id, type, amount, title, description, reference, category, status) "
                "VALUES (:1, 'income', :2, :3, :4, :5, 'transfer', 'success')",
                (dest_acc.account_id, amount,
                 f"Funds from {source_acc.account_number}",
                 f"Ref: {ref}", ref + "R")
            )
            # Transfer ledger
            cur.execute(
                "INSERT INTO transfers "
                "(source_account_id, destination_account_id, amount, reference, description) "
                "VALUES (:1, :2, :3, :4, :5)",
                (source_acc.account_id, dest_acc.account_id, amount, ref, description)
            )
            conn.commit()
            return ref
        except Exception as e:
            conn.rollback()
            raise DatabaseException(f"Transfer rolled back: {e}")
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Audit logs
    # ------------------------------------------------------------------

    def add_audit_log(self, actor_id, actor_type, action, description,
                      status='success'):
        conn = self.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO audit_logs "
                "(actor_id, actor_type, action, description, status) "
                "VALUES (:1, :2, :3, :4, :5)",
                (actor_id, actor_type, action, description, status)
            )
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            conn.close()

    def get_audit_logs(self) -> list:
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM audit_logs ORDER BY log_id DESC")
        rows = self._fetchall_dicts(cur)
        conn.close()
        return rows

    # ------------------------------------------------------------------
    # Virtual Cards
    # ------------------------------------------------------------------

    def create_virtual_card(self, customer_id, card_number, card_holder,
                            expiry_date, cvv, balance) -> int:
        conn = self.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO virtual_cards "
                "(customer_id, card_number, card_holder, expiry_date, cvv, balance) "
                "VALUES (:1, :2, :3, :4, :5, :6)",
                (customer_id, card_number, card_holder, expiry_date, cvv, balance)
            )
            conn.commit()
            cur.execute(
                "SELECT card_id FROM virtual_cards WHERE card_number = :1",
                (card_number,)
            )
            row = cur.fetchone()
            return row[0] if row else None
        except Exception as e:
            conn.rollback()
            raise DatabaseException(f"create_virtual_card failed: {e}")
        finally:
            conn.close()

    def get_virtual_cards(self, customer_id) -> list:
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT * FROM virtual_cards WHERE customer_id = :1 ORDER BY card_id",
            (customer_id,)
        )
        rows = self._fetchall_dicts(cur)
        conn.close()
        # rename card_id -> id for backward compat with view layer
        for r in rows:
            r['id'] = r['card_id']
        return rows

    def toggle_card_freeze(self, card_id, status):
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE virtual_cards SET is_frozen = :1 WHERE card_id = :2",
            (status, card_id)
        )
        conn.commit()
        conn.close()

    def simulate_card_purchase(self, card_id, amount, merchant):
        conn = self.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT * FROM virtual_cards WHERE card_id = :1", (card_id,))
            card = self._fetchone_dict(cur)
            if not card:
                return False, "Card not found"
            if card['is_frozen']:
                return False, "Card is frozen"
            if float(card['balance']) < amount:
                cur.execute(
                    "INSERT INTO card_transactions "
                    "(card_id, amount, merchant, status) VALUES (:1, :2, :3, 'declined')",
                    (card_id, amount, merchant)
                )
                conn.commit()
                return False, "Insufficient card balance"
            cur.execute(
                "UPDATE virtual_cards SET balance = balance - :1 WHERE card_id = :2",
                (amount, card_id)
            )
            cur.execute(
                "INSERT INTO card_transactions "
                "(card_id, amount, merchant, status) VALUES (:1, :2, :3, 'approved')",
                (card_id, amount, merchant)
            )
            conn.commit()
            return True, "Purchase Approved", card['customer_id']
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    def get_card_transactions(self, card_id) -> list:
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT * FROM card_transactions WHERE card_id = :1 "
            "ORDER BY card_txn_id DESC",
            (card_id,)
        )
        rows = self._fetchall_dicts(cur)
        conn.close()
        for r in rows:
            r['id'] = r['card_txn_id']
        return rows

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def add_notification(self, customer_id, type_, title, message):
        conn = self.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO notifications "
                "(customer_id, type, title, message) VALUES (:1, :2, :3, :4)",
                (customer_id, type_, title, message)
            )
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            conn.close()

    def get_notifications(self, customer_id) -> list:
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT * FROM notifications WHERE customer_id = :1 "
            "ORDER BY notification_id DESC",
            (customer_id,)
        )
        rows = self._fetchall_dicts(cur)
        conn.close()
        for r in rows:
            r['id']      = r['notification_id']
            r['user_id'] = r['customer_id']
        return rows

    def mark_notifications_read(self, customer_id):
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE notifications SET is_read = 1 WHERE customer_id = :1",
            (customer_id,)
        )
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # Fraud Alerts
    # ------------------------------------------------------------------

    def add_fraud_alert(self, customer_id, type_, txn_id, description):
        conn = self.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO fraud_alerts "
                "(customer_id, type, transaction_id, description) "
                "VALUES (:1, :2, :3, :4)",
                (customer_id, type_, txn_id, description)
            )
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            conn.close()

    def get_fraud_alerts(self) -> list:
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT f.*, c.fullname, c.email "
            "FROM fraud_alerts f "
            "JOIN customers c ON f.customer_id = c.customer_id "
            "ORDER BY f.alert_id DESC"
        )
        rows = self._fetchall_dicts(cur)
        conn.close()
        for r in rows:
            r['id']      = r['alert_id']
            r['user_id'] = r['customer_id']
        return rows

    def resolve_fraud_alert(self, alert_id):
        conn = self.get_connection()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE fraud_alerts SET status = 'resolved' WHERE alert_id = :1",
            (alert_id,)
        )
        conn.commit()
        conn.close()


# ==========================================
# Factory Initialization
# ==========================================

_manager_instance = None

def get_db_manager() -> DatabaseManager:
    """Provider function returning the active DatabaseManager (always Oracle)."""
    global _manager_instance
    if _manager_instance is None:
        oracle_mgr = OracleDatabaseManager()
        if not oracle_mgr._active:
            raise RuntimeError(
                "Oracle driver is not installed or failed to initialize. "
                "Install oracledb and ensure ORACLE_DSN, ORACLE_USER, ORACLE_PWD are set."
            )
        _manager_instance = oracle_mgr
            
        # Guarantee schema setup
        _manager_instance.init_db()
        
    return _manager_instance
