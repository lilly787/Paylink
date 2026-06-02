from flask import Flask, render_template, request, jsonify, session
import database
import oracle
import oop_banking
import re
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'paylink_fintech_super_secret_key_2026'

# Initialize database tables and migrations
database.init_db()

# ---- UI ROUTES ----

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/onboarding')
def onboarding():
    return render_template('onboarding.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/otp')
def otp():
    return render_template('otp.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/transfer')
def transfer():
    return render_template('transfer.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/security')
def security():
    return render_template('security.html')

@app.route('/transaction_details')
def transaction_details():
    return render_template('transaction_details.html')

@app.route('/notifications')
def notifications():
    return render_template('notifications.html')

@app.route('/deposit')
def deposit():
    return render_template('deposit.html')

@app.route('/bills')
def bills():
    return render_template('bills.html')

@app.route('/personal_info')
def personal_info():
    return render_template('personal_info.html')

@app.route('/cards')
def cards():
    return render_template('cards.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/save')
def save():
    return render_template('save.html')

# ---- API ROUTES ----

# -- Auth API --

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    fullname = data.get('fullname')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password', 'password')
    pin = data.get('pin', '1234')
    account_type = data.get('account_type', 'savings')
    
    try:
        user = database.register_user(fullname, email, phone, password, pin, account_type)
        if user:
            return jsonify({"success": True, "user": user})
        return jsonify({"success": False, "message": "Email already exists"}), 400
    except oop_banking.BankingException as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "message": "Internal registration error"}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password', 'password')
    
    user = database.verify_user_password(email, password)
    if user:
        if user['is_frozen']:
            return jsonify({"success": False, "message": "Your account has been frozen by administration due to security concerns."}), 403
        return jsonify({"success": True, "user": dict(user)})
    return jsonify({"success": False, "message": "Invalid email or password"}), 401

@app.route('/api/verify-pin', methods=['POST'])
def api_verify_pin():
    data = request.json
    user_id = data.get('user_id')
    pin = data.get('pin')
    
    if database.verify_user_pin(user_id, pin):
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Incorrect Transaction PIN"}), 400

@app.route('/api/security/setup-pin', methods=['POST'])
def api_setup_pin():
    data = request.json
    user_id = data.get('user_id')
    pin = data.get('pin')
    
    conn = database.get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE customers SET pin_hash = ? WHERE customer_id = ?', (database.hash_sha256(pin), user_id))
    conn.commit()
    conn.close()
    
    updated_user = database.get_user_by_id(user_id)
    return jsonify({"success": True, "user": updated_user})

@app.route('/api/user/<int:user_id>')
def api_get_user(user_id):
    user = database.get_user_by_id(user_id)
    if user:
        if user['is_frozen']:
            return jsonify({"success": False, "message": "Account is frozen"}), 403
        return jsonify({"success": True, "user": user})
    return jsonify({"success": False}), 404

# -- Wallet & Transfer API with Fraud Detection --

@app.route('/api/transfer', methods=['POST'])
def api_transfer():
    data = request.json
    user_id = data.get('user_id')
    amount = float(data.get('amount'))
    desc = data.get('desc')
    recipient_acc = data.get('recipient_acc')
    recipient_name = data.get('recipient')
    pin = data.get('pin')
    category = data.get('category', 'transfer')
    
    try:
        # 1. Security Check: Block Frozen Account
        user = database.get_user_by_id(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        if user['is_frozen']:
            return jsonify({"success": False, "message": "Account is frozen. All outgoing transactions are blocked."}), 403
            
        # 2. PIN Verification
        if not database.verify_user_pin(user_id, pin):
            return jsonify({"success": False, "message": "Invalid security PIN"}), 400
            
        # 3. Fraud Detection Engine
        fraud_flagged = False
        fraud_reason = ""
        
        # A. Large Transfer Check (> ₦50,000)
        if amount > 50000.00:
            fraud_flagged = True
            fraud_reason = f"Large transfer flag: {amount:,.2f} Naira transferred to {recipient_name}."
            
        # B. Rapid Withdrawals Check (>3 transactions in 2 minutes)
        recent_txns = database.get_transactions(user_id)[:3]
        if len(recent_txns) >= 2:
            try:
                # Check relative dates
                now = datetime.utcnow()
                rapid_count = 0
                for rx in recent_txns:
                    rx_date = datetime.fromisoformat(rx['date'].replace('Z', ''))
                    if now - rx_date < timedelta(minutes=2):
                        rapid_count += 1
                if rapid_count >= 2:
                    fraud_flagged = True
                    fraud_reason = "Rapid withdrawals: Multiple rapid outlays flagged under 2 minutes."
            except Exception:
                pass
                
        # 4. Process Balance Deductions (invokes OOP validation)
        database.update_balance(user_id, amount, is_expense=True)
        
        # Record transaction receipt & references
        ref = database.generate_unique_ref()
        receipt_data = {
            "sender": user['fullname'],
            "recipient": recipient_name,
            "recipient_account": recipient_acc,
            "amount": amount,
            "date": datetime.utcnow().isoformat() + 'Z',
            "reference": ref,
            "category": category,
            "description": desc
        }
        
        txn_id = database.add_transaction(
            user_id=user_id, 
            type_='expense', 
            amount=amount, 
            title=f"Transfer to {recipient_name}", 
            desc=desc, 
            reference=ref, 
            category=category, 
            receipt_data=receipt_data
        )
        
        # 5. Process Recipient Increase (If it is an internal account number)
        recipient_user = database.get_user_by_account(recipient_acc)
        if recipient_user:
            database.update_balance(recipient_user['id'], amount, is_expense=False)
            database.add_transaction(
                user_id=recipient_user['id'],
                type_='income',
                amount=amount,
                title=f"Funds from {user['fullname']}",
                desc=f"Wallet transfer ref: {ref}",
                reference=database.generate_unique_ref(),
                category='transfer'
            )
            database.add_notification(recipient_user['id'], 'success', 'Funds Received', f'You received ₦{amount:,.2f} from {user["fullname"]}.')
    
        # Trigger Fraud Alerts
        if fraud_flagged:
            database.add_fraud_alert(user_id, 'suspicious_activity', txn_id, fraud_reason)
            database.add_notification(user_id, 'warning', 'Security Alert Triggered', f"Transaction of {amount:,.2f} flagged. Account under surveillance.")
    
        # Success notification
        database.add_notification(user_id, 'success', 'Transfer Successful', f"Sent ₦{amount:,.2f} to {recipient_name}.")
    
        # Load updated user info
        updated_user = database.get_user_by_id(user_id)
        return jsonify({"success": True, "balance": updated_user['balance'], "txn_id": txn_id})
    except oop_banking.BankingException as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        print(f"TRANSFER ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": "An error occurred during transfer."}), 500

@app.route('/api/transactions/<int:user_id>')
def api_transactions(user_id):
    txns = database.get_transactions(user_id)
    return jsonify({"success": True, "transactions": txns})

@app.route('/api/transaction/detail/<int:txn_id>')
def api_transaction_detail(txn_id):
    txn = database.get_transaction_by_id(txn_id)
    if txn:
        return jsonify({"success": True, "transaction": txn})
    return jsonify({"success": False}), 404

@app.route('/api/deposit', methods=['POST'])
def api_deposit():
    data = request.json
    user_id = data.get('user_id')
    amount = float(data.get('amount'))
    
    try:
        # Update balance (income)
        database.update_balance(user_id, amount, is_expense=False)
        # Record transaction
        ref = database.generate_unique_ref()
        database.add_transaction(user_id, 'income', amount, "Card Deposit", "Self-funded via debit card", reference=ref, category='deposit')
        database.add_notification(user_id, 'success', 'Funds Deposited', f"Deposited ₦{amount:,.2f} via debit card.")
        
        user = database.get_user_by_id(user_id)
        return jsonify({"success": True, "balance": user['balance']})
    except oop_banking.BankingException as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "message": "An error occurred during deposit."}), 500

# -- Virtual Card System API --

@app.route('/api/cards/<int:user_id>')
def api_get_cards(user_id):
    cards = database.get_virtual_cards(user_id)
    return jsonify({"success": True, "cards": cards})

@app.route('/api/cards/create', methods=['POST'])
def api_create_card():
    data = request.json
    user_id = data.get('user_id')
    funding = float(data.get('amount'))
    pin = data.get('pin')
    
    user = database.get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    if user['is_frozen']:
        return jsonify({"success": False, "message": "Cannot create card: Account is frozen"}), 403
        
    if not database.verify_user_pin(user_id, pin):
        return jsonify({"success": False, "message": "Incorrect Transaction PIN"}), 400
        
    if user['balance'] < funding:
        return jsonify({"success": False, "message": "Insufficient wallet balance to fund card"}), 400
        
    card_id = database.create_virtual_card(user_id, user['fullname'], funding)
    if card_id:
        return jsonify({"success": True, "card_id": card_id})
    return jsonify({"success": False, "message": "Failed to create card"}), 500

@app.route('/api/cards/toggle-freeze', methods=['POST'])
def api_toggle_card_freeze():
    data = request.json
    card_id = data.get('card_id')
    status = int(data.get('status')) # 1 or 0
    
    database.toggle_card_freeze(card_id, status)
    status_str = "frozen" if status == 1 else "unfrozen"
    return jsonify({"success": True, "message": f"Card successfully {status_str}."})

@app.route('/api/cards/simulate', methods=['POST'])
def api_simulate_card():
    data = request.json
    card_id = data.get('card_id')
    amount = float(data.get('amount'))
    merchant = data.get('merchant', 'Online Merchant')
    
    success, msg = database.simulate_card_purchase(card_id, amount, merchant)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@app.route('/api/cards/transactions/<int:card_id>')
def api_card_transactions(card_id):
    txns = database.get_card_transactions(card_id)
    return jsonify({"success": True, "transactions": txns})

# -- Bill Payments API --

@app.route('/api/bills/pay', methods=['POST'])
def api_pay_bills():
    data = request.json
    user_id = data.get('user_id')
    amount = float(data.get('amount'))
    phone = data.get('phone', '')
    bill_type = data.get('bill_type') # 'airtime', 'data', 'electricity', 'tv'
    provider = data.get('provider') # 'MTN', 'Glo', 'Airtel', 'DSTV', 'EKEDC'
    meter_number = data.get('meter_number', '')
    pin = data.get('pin')
    
    user = database.get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    if user['is_frozen']:
        return jsonify({"success": False, "message": "Account frozen"}), 403
    if not database.verify_user_pin(user_id, pin):
        return jsonify({"success": False, "message": "Incorrect security PIN"}), 400
    if user['balance'] < amount:
        return jsonify({"success": False, "message": "Insufficient wallet funds"}), 400
        
    # Process bill
    database.update_balance(user_id, amount, is_expense=True)
    
    ref = database.generate_unique_ref()
    desc = ""
    title = f"{provider} {bill_type.title()}"
    
    if bill_type == 'airtime' or bill_type == 'data':
        desc = f"To {phone}"
    elif bill_type == 'electricity':
        desc = f"Token generated for Meter: {meter_number}"
    elif bill_type == 'tv':
        desc = f"Subscription renewed for SmartCard: {meter_number}"
        
    receipt_data = {
        "bill_type": bill_type,
        "provider": provider,
        "amount": amount,
        "phone": phone,
        "meter_number": meter_number,
        "reference": ref,
        "date": datetime.utcnow().isoformat() + 'Z'
    }
    
    txn_id = database.add_transaction(user_id, 'expense', amount, title, desc, reference=ref, category=bill_type, receipt_data=receipt_data)
    database.add_notification(user_id, 'success', 'Bill Paid Successfully', f"Paid ₦{amount:,.2f} for {title}.")
    
    # For electricity, generate a visual random meter token to display on the receipt
    if bill_type == 'electricity':
        token = "-".join(["".join([str(random.randint(0, 9)) for _ in range(4)]) for _ in range(5)])
        receipt_data['token'] = token
        conn = database.get_db_connection()
        import json
        conn.execute("UPDATE transactions SET receipt_json = ? WHERE id = ?", (json.dumps(receipt_data), txn_id))
        conn.commit()
        conn.close()
        
    updated_user = database.get_user_by_id(user_id)
    return jsonify({"success": True, "balance": updated_user['balance'], "txn_id": txn_id})

# -- Oracle API --

@app.route('/api/oracle/rates')
def api_oracle_rates():
    oracle_payload = oracle.fetch_oracle_rates()
    return jsonify({"success": True, "oracle": oracle_payload})


# -- Notifications API --

@app.route('/api/notifications/<int:user_id>')
def api_get_notifications(user_id):
    notifs = database.get_notifications(user_id)
    return jsonify({"success": True, "notifications": notifs})

@app.route('/api/notifications/read', methods=['POST'])
def api_notifications_read():
    data = request.json
    user_id = data.get('user_id')
    database.mark_notifications_read(user_id)
    return jsonify({"success": True})

# -- Admin Control Panel API --

@app.route('/api/admin/users')
def api_admin_users():
    users = database.get_all_users()
    return jsonify({"success": True, "users": users})

@app.route('/api/admin/toggle-freeze', methods=['POST'])
def api_admin_toggle_freeze():
    data = request.json
    user_id = data.get('user_id')
    status = int(data.get('status')) # 1 for frozen, 0 for unfrozen
    
    database.toggle_user_freeze(user_id, status)
    status_str = "frozen" if status == 1 else "activated"
    database.add_notification(user_id, 'warning' if status == 1 else 'success', f'Account {status_str.title()}', f'Your banking account has been {status_str} by administration.')
    return jsonify({"success": True, "message": f"User status successfully updated to: {status_str}"})

@app.route('/api/admin/transactions')
def api_admin_transactions():
    txns = database.get_all_transactions()
    return jsonify({"success": True, "transactions": txns})

@app.route('/api/admin/fraud')
def api_admin_fraud():
    alerts = database.get_fraud_alerts()
    return jsonify({"success": True, "alerts": alerts})

@app.route('/api/admin/audit-logs')
def api_admin_audit_logs():
    mgr = oop_banking.get_db_manager()
    logs = mgr.get_audit_logs()
    return jsonify({"success": True, "logs": logs})

@app.route('/api/admin/fraud/resolve', methods=['POST'])
def api_admin_fraud_resolve():
    data = request.json
    alert_id = data.get('alert_id')
    database.resolve_fraud_alert(alert_id)
    return jsonify({"success": True})

# -- AI Natural Language Parser endpoint --

@app.route('/api/ai-interpret', methods=['POST'])
def api_ai_interpret():
    data = request.json
    text = data.get('text', '').lower().strip()
    user_id = data.get('user_id')
    
    def parse_amount(amt_str):
        amt_str = amt_str.replace(',', '').strip()
        if 'k' in amt_str:
            try:
                return float(amt_str.replace('k', '')) * 1000
            except:
                pass
        try:
            return float(amt_str)
        except:
            return None

    # NLP parse transfers: e.g. "send 5000 to John", "transfer 5k to David", "pay David 10,000"
    transfer_match = re.search(r'(?:send|transfer|pay|wire)\s+([\d,.]+(?:\s*k)?)\s+to\s+([a-zA-Z\s]+)', text)
    if not transfer_match:
        # Alternately check "pay David 10,000"
        transfer_match = re.search(r'(?:pay|send)\s+([a-zA-Z\s]+)\s+([\d,.]+(?:\s*k)?)', text)
        if transfer_match:
            name = transfer_match.group(1).strip()
            amount_str = transfer_match.group(2).strip()
        else:
            name = None
            amount_str = None
    else:
        amount_str = transfer_match.group(1).strip()
        name = transfer_match.group(2).strip()
        
    if name and amount_str:
        amount = parse_amount(amount_str)
        if amount:
            conn = database.get_db_connection()
            # fuzzy match names in 3NF schema
            matched_user = conn.execute('''
                SELECT customers.customer_id AS id, customers.fullname, accounts.account_number
                FROM customers
                JOIN accounts ON customers.customer_id = accounts.customer_id
                WHERE customers.fullname LIKE ? AND customers.customer_id != ?
            ''', (f"%{name}%", user_id)).fetchone()
            conn.close()
            
            if matched_user:
                matched_user = dict(matched_user)
                return jsonify({
                    "success": True,
                    "action": "transfer",
                    "amount": amount,
                    "recipient_name": matched_user['fullname'],
                    "recipient_account": matched_user['account_number'],
                    "recipient_id": matched_user['id'],
                    "summary": f"Send ₦{amount:,.2f} to {matched_user['fullname']} ({matched_user['account_number']})"
                })
            else:
                return jsonify({
                    "success": True,
                    "action": "transfer",
                    "amount": amount,
                    "recipient_name": name.title(),
                    "recipient_account": "30" + "".join([str(random.randint(0, 9)) for _ in range(8)]),
                    "recipient_id": None,
                    "summary": f"Send ₦{amount:,.2f} to {name.title()} (New Recipient)"
                })
                
    # NLP parse airtime: e.g. "buy 1k airtime to 08012345678", "buy airtime 500 on 080333..."
    airtime_match = re.search(r'(?:buy|recharge|airtime|topup)\s+([\d,.]+(?:\s*k)?)\s+(?:airtime\s+)?(?:to|for|on)?\s*(mtn|glo|airtel|9mobile)?\s*(\d{10,11})', text)
    if airtime_match:
        amount_str = airtime_match.group(1)
        network = airtime_match.group(2) or 'MTN'
        phone = airtime_match.group(3)
        amount = parse_amount(amount_str)
        if amount and phone:
            return jsonify({
                "success": True,
                "action": "airtime",
                "amount": amount,
                "network": network.upper(),
                "phone": phone,
                "summary": f"Buy {amount:,.2f} {network.upper()} Airtime for {phone}"
            })
            
    # NLP parse electricity: e.g. "pay electricity 5000", "buy electricity 10k"
    elec_match = re.search(r'(?:pay|buy)\s+electricity\s+([\d,.]+(?:\s*k)?)', text)
    if elec_match:
        amount_str = elec_match.group(1)
        amount = parse_amount(amount_str)
        if amount:
            meter = "".join([str(random.randint(0, 9)) for _ in range(11)])
            return jsonify({
                "success": True,
                "action": "electricity",
                "amount": amount,
                "meter_number": meter,
                "summary": f"Pay ₦{amount:,.2f} for Electricity (Meter: {meter})"
            })
            
    return jsonify({"success": False, "message": "Could not parse instruction. Try: 'send 5k to David', 'recharge 1000 Glo 08123456789', or 'pay electricity 5k'"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
