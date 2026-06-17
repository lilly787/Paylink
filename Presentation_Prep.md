# CSC 302: OOP Banking System Presentation Prep Guide

Good evening! This document is designed to help you prepare for your 10:00 AM presentation tomorrow. It covers everything you need to know about Object-Oriented Programming (OOP) concepts, the 4 Pillars, the Entity-Relationship Diagram (ERD), and a complete, easy-to-understand breakdown of how your web app actually works.

---

## 1. Meaning of Object-Oriented Programming (OOP)

**Concept:** Object-Oriented Programming (OOP) is a programming paradigm based on the concept of "objects". Instead of just writing functions and logic top-to-bottom, OOP bundles data (attributes/properties) and behavior (functions/methods) into self-contained units called objects.
* **Why we use it:** It models real-world entities. In a banking system, instead of having raw variables scattered everywhere, we create physical blueprints (Classes) for things like `Customer`, `Account`, and `Transaction`.

---

## 2. The Four Pillars of OOP

You need to know the concept, how it's coded in your app, and its practical use.

### A. Abstraction
* **Concept:** Hiding the complex reality while exposing only the necessary parts. It means defining a general "template" that dictates what something *should* do, without actually writing *how* it does it.
* **How it's coded:** Look in `oop_banking.py`. We created an abstract base class `Account(ABC)`. It contains `@abstractmethod` functions like `get_account_type()` and `get_withdrawal_limit()`. The `Account` class itself cannot be instantiated directly; it forces its subclasses to implement these methods.
* **Practical Use:** Ensures that any new account type added to the bank in the future (like a `StudentAccount` or `FixedDepositAccount`) strictly follows the bank's rules by implementing those required methods.

### B. Encapsulation
* **Concept:** Bundling data and the methods that act on that data into a single unit (class), and restricting direct access to some of the object's components. It acts as a protective shield.
* **How it's coded:** In `oop_banking.py` inside the `Account` class, the balance is stored as `self._balance` (the underscore denotes it's protected). The outside world cannot do `account._balance = 10000000`. They can only view it using a getter method (`@property def balance(self)`), and they can only change it by calling the `deposit(amount)` or `withdraw(amount)` methods, which contain validation logic.
* **Practical Use:** Security and data integrity. It prevents a hacker or a buggy piece of code from arbitrarily changing an account balance without passing through the proper deposit/withdrawal security checks.

### C. Inheritance
* **Concept:** A mechanism where one class (the child) acquires the properties and methods of another class (the parent). This promotes code reusability.
* **How it's coded:** In `oop_banking.py`, `SavingsAccount` and `CurrentAccount` inherit from the parent `Account` class. Instead of rewriting the logic for freezing an account or depositing money twice, both child classes inherit those methods automatically from `Account`.
* **Practical Use:** DRY (Don't Repeat Yourself). It keeps the codebase clean and manageable. If the bank updates how deposits work, you only change the code in the parent `Account` class, and all child accounts inherit the fix.

### D. Polymorphism
* **Concept:** Meaning "many forms", it allows methods to do different things based on the object it is acting upon, even if they share the same name.
* **How it's coded:** In `oop_banking.py`, both `SavingsAccount` and `CurrentAccount` have a method called `get_withdrawal_limit()`. However, the Savings account returns `50000.00` while the Current account returns `500000.00`. When the code calls `account.withdraw(amount)`, the system dynamically knows which limit to enforce based on what specific account object is making the call.
* **Practical Use:** Flexibility. The `TransferService` can process a transfer between *any* two accounts without needing to write `if account == 'savings': do this else: do that`. It just calls `account.withdraw()` and relies on the object to behave correctly.

---

## 3. The Entity-Relationship Diagram (ERD)

**Concept:** An ERD is a structural diagram used in database design. It shows the entities (tables) in a database and how they relate to one another.

**How it's implemented in your app:**
* **Customers Table:** Stores user data (PK: `customer_id`).
* **Accounts Table:** Stores account ledgers (PK: `account_id`, FK: `customer_id`). This defines a **1-to-Many** relationship (One customer can own many accounts).
* **Transactions Table:** Stores financial history (PK: `transaction_id`, FK: `account_id`). This is also a **1-to-Many** relationship (One account has many transactions).
* **Branches Table:** Stores bank branches. An account belongs to a branch.

**Practical Use:** By separating data into different tables and linking them with Foreign Keys (FK), we achieve **Database Normalization**. This prevents data redundancy. For example, if a customer changes their phone number, we only update the `Customers` table once, rather than updating every single transaction record they've ever made.

---

## 4. How the Web App Actually Works (Simple Explanation)

If anyone asks how the whole system connects together, explain it like this:

Your app has a **3-Tier Architecture**:

1. **The Frontend (Browser/UI):**
   * Found in the `templates/` and `static/` folders.
   * This is what the user sees. It's written in HTML/CSS/JS. When a user clicks "Transfer Money", their browser sends a request to the backend.

2. **The Backend Controller (Flask Web Framework):**
   * Found in `app.py`.
   * Flask acts as the middleman. It receives the "Transfer Money" request from the frontend.
   * It then calls the banking logic found in `database.py` and `oop_banking.py`.

3. **The OOP Logic & Database Layer (Oracle DB):**
   * Found in `oop_banking.py` and your Oracle Database.
   * The `TransferService.transfer_funds()` method runs. It treats the accounts as **Objects**. It calls `source_acc.withdraw()` and `dest_acc.deposit()`.
   * Once the Objects approve the math (checking limits, checking if frozen, etc.), the `OracleDatabaseManager` takes the final numbers and permanently saves them to the Oracle Database using SQL queries (`UPDATE accounts SET balance = ...`).
   * The database also uses **Triggers** to automatically write to the `Audit Logs` so every action is tracked for security.

### Live Exchange Rates (Bonus Feature)
The app doesn't just do basic math; it has an integration in `oracle.py` that fetches **live exchange rates** from the internet (an external API) and displays them on the dashboard, making it a modern, real-world banking simulation.

---

### Tips for the Presentation
* **Speak confidently:** When talking about Encapsulation, emphasize "Security". When talking about Inheritance, emphasize "Reusability".
* **Keep it simple:** You don't need to read code line-by-line to the audience. Just say "We created an Account parent class, and Savings/Current child classes inherit from it."
* **Best of luck!** You have a solid, enterprise-grade architecture here. You're going to do great tomorrow!
