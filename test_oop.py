import os
import sys
import io
# Force UTF-8 encoding for Windows consoles printing currency symbols
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import oop_banking
import database

def run_tests():
    print("--- Starting Paylink OOP Integration Tests (Oracle Database) ---")
    
    # Verify Oracle environment
    dsn = os.environ.get("ORACLE_DSN", "localhost:1521/XE")
    user = os.environ.get("ORACLE_USER", "system")
    print(f"Target Oracle database: {dsn} as user: {user}")
    
    print("\n[Test 1] Initializing Database Schema...")
    try:
        database.init_db()
        mgr = oop_banking.get_db_manager()
        print("Successfully connected and initialized Oracle Database schema.")
    except Exception as e:
        print(f"FAIL: Oracle Database initialization failed: {e}")
        print("Please ensure your Oracle XE instance is running and your ORACLE_DSN, ORACLE_USER, and ORACLE_PWD environment variables are set correctly.")
        sys.exit(1)

    print("\n[Test 2] Testing Customer Registration...")
    email = "test_student@veritas.edu.ng"
    user = database.register_user(
        fullname="John Test Student",
        email=email,
        phone="08011223344",
        password="studentpassword",
        pin="4321",
        account_type="savings"
    )
    if not user:
        print("FAIL: Registration returned None.")
        sys.exit(1)
        
    print(f"PASS: Customer registered successfully. Assigned Account: {user['account_number']}, Balance: ₦{user['balance']:,.2f}")

    print("\n[Test 3] Testing Customer Login and Password Verification...")
    login_user = database.verify_user_password(email, "studentpassword")
    if not login_user or login_user['fullname'] != "John Test Student":
        print("FAIL: Password verification failed.")
        sys.exit(1)
    print("PASS: Password verification succeeded.")

    print("\n[Test 4] Testing PIN Verification...")
    if not database.verify_user_pin(login_user['id'], "4321"):
        print("FAIL: PIN verification failed.")
        sys.exit(1)
    print("PASS: PIN verification succeeded.")

    print("\n[Test 5] Testing Polymorphic Account Limits (Savings Account Limit = ₦50,000)...")
    try:
        # Try to withdraw ₦60,000 in one transaction (Savings limit is ₦50,000)
        database.update_balance(login_user['id'], 60000.00, is_expense=True)
        print("FAIL: Allowed withdrawal of ₦60,000 from Savings account without exception.")
        sys.exit(1)
    except oop_banking.InsufficientFundsError as e:
        print(f"PASS: Correctly threw InsufficientFundsError: {e}")
    except Exception as e:
        print(f"FAIL: Threw wrong exception type: {type(e).__name__} - {e}")
        sys.exit(1)

    print("\n[Test 6] Testing Valid Withdrawal (₦10,000)...")
    try:
        database.update_balance(login_user['id'], 10000.00, is_expense=True)
        updated_user = database.get_user(email)
        print(f"PASS: Valid withdrawal succeeded. New Balance: ₦{updated_user['balance']:,.2f}")
    except Exception as e:
        print(f"FAIL: Valid withdrawal threw exception: {e}")
        sys.exit(1)

    print("\n[Test 7] Testing Savings Minimum Balance Floor Constraint (₦5,000)...")
    try:
        # Current balance is ₦140,000. Let's try to withdraw ₦136,000 (leaves ₦4,000, violating the ₦5,000 floor)
        # Note: A single withdrawal limit is ₦50,000, so let's do two ₦48,000 withdrawals to get down, or update balance directly
        # Let's perform two withdrawals of ₦45,000
        database.update_balance(login_user['id'], 45000.00, is_expense=True)
        database.update_balance(login_user['id'], 45000.00, is_expense=True)
        # Balance is now ₦50,000. Let's try to withdraw ₦46,000 (leaves ₦4,000)
        database.update_balance(login_user['id'], 46000.00, is_expense=True)
        print("FAIL: Allowed account balance to fall below ₦5,000 Savings floor.")
        sys.exit(1)
    except oop_banking.InsufficientFundsError as e:
        print(f"PASS: Correctly prevented falling below floor: {e}")
    except Exception as e:
        print(f"FAIL: Threw wrong exception: {e}")
        sys.exit(1)

    print("\n[Test 8] Registering Current Account (Allows Overdraft down to -₦100,000)...")
    current_email = "test_current@veritas.edu.ng"
    cur_user = database.register_user(
        fullname="Alice Current Student",
        email=current_email,
        phone="08022334455",
        password="currentpassword",
        pin="1234",
        account_type="current"
    )
    # Alice starts with ₦150,000.
    print(f"PASS: Current Account registered. Account: {cur_user['account_number']}, Balance: ₦{cur_user['balance']:,.2f}")

    print("\n[Test 9] Testing Overdraft Withdrawal on Current Account...")
    try:
        # Let's withdraw ₦200,000 (Alice has ₦150,000, so balance goes to -₦50,000. This is allowed since limit is -₦100,000)
        # Since single withdrawal limit for Current is ₦500,000, this is one transaction
        database.update_balance(cur_user['id'], 20000.00, is_expense=True) # balance = 130k
        database.update_balance(cur_user['id'], 170000.00, is_expense=True) # balance = -40k
        updated_cur = database.get_user(current_email)
        print(f"PASS: Overdraft succeeded. New Balance: ₦{updated_cur['balance']:,.2f}")
    except Exception as e:
        print(f"FAIL: Overdraft failed: {e}")
        sys.exit(1)

    print("\n[Test 10] Testing Overdraft limit violation...")
    try:
        # Alice is at -₦40,000. Let's try to withdraw ₦70,000 (goes to -₦110,000, violating -₦100,000 limit)
        database.update_balance(cur_user['id'], 70000.00, is_expense=True)
        print("FAIL: Allowed balance to go past -₦100,000 overdraft limit.")
        sys.exit(1)
    except oop_banking.InsufficientFundsError as e:
        print(f"PASS: Correctly blocked overdraft limit: {e}")
    except Exception as e:
        print(f"FAIL: Threw wrong exception: {e}")
        sys.exit(1)

    print("\n[Test 11] Testing Fund Transfer Service...")
    # John is at ₦50,000. Alice is at -₦40,000.
    # John transfers ₦20,000 to Alice.
    john_acc = mgr.get_account_by_number(user['account_number'])
    alice_acc = mgr.get_account_by_number(cur_user['account_number'])
    
    try:
        ref = oop_banking.TransferService.transfer_funds(mgr, john_acc, alice_acc, 20000.00, "Rent Payment")
        john_updated = database.get_user(email)
        alice_updated = database.get_user(current_email)
        print(f"PASS: Transfer completed. Ref: {ref}")
        print(f"      John's New Balance: ₦{john_updated['balance']:,.2f} (Expected: ₦30,000)")
        print(f"      Alice's New Balance: ₦{alice_updated['balance']:,.2f} (Expected: -₦20,000)")
        if john_updated['balance'] != 30000.00 or alice_updated['balance'] != -20000.00:
            print("FAIL: Balances not updated correctly.")
            sys.exit(1)
    except Exception as e:
        print(f"FAIL: Fund transfer failed: {e}")
        sys.exit(1)

    print("\n[Test 12] Testing Audit Logs verification...")
    logs = mgr.get_audit_logs()
    print(f"PASS: Successfully retrieved {len(logs)} audit logs from 3NF table.")
    print("      Latest audit action:", logs[0]['action'], "-", logs[0]['description'])

    print("\n--- ALL TESTS COMPLETED SUCCESSFULLY ---")

if __name__ == '__main__':
    run_tests()
