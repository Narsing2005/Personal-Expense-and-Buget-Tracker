from datetime import datetime, timedelta
from database import get_db
from utils.auth_helpers import hash_password
from utils.budget_calculator import calculate_budget_utilization

def seed_sample_data():
    db = get_db()
    
    # 1. Clear existing sample user if any
    demo_email = "alex@finora.io"
    db.users.delete_one({"email": demo_email})
    
    # Create demo user
    hashed_pw = hash_password("Finora2026!")
    user_res = db.users.insert_one({
        "name": "Alex Morgan",
        "email": demo_email,
        "password_hash": hashed_pw,
        "created_at": datetime.utcnow() - timedelta(days=90),
        "currency": "USD"
    })
    user_id = str(user_res.inserted_id)
    
    # Remove existing data for this user
    db.transactions.delete_many({"user_id": user_id})
    db.budgets.delete_many({"user_id": user_id})
    db.notifications.delete_many({"user_id": user_id})

    now = datetime.utcnow()
    current_month = now.strftime("%Y-%m")
    last_month = (now.replace(day=1) - timedelta(days=5)).strftime("%Y-%m")
    two_months_ago = (now.replace(day=1) - timedelta(days=35)).strftime("%Y-%m")

    # 2. Add Monthly Budgets for Current Month
    budgets = [
        {"category": "Food & Dining", "limit_amount": 600.0, "month": current_month, "notes": "Groceries and restaurant spending"},
        {"category": "Housing & Rent", "limit_amount": 1500.0, "month": current_month, "notes": "Monthly apartment lease"},
        {"category": "Transportation", "limit_amount": 250.0, "month": current_month, "notes": "Metro card and occasional taxi/fuel"},
        {"category": "Entertainment", "limit_amount": 200.0, "month": current_month, "notes": "Concerts, games, streaming"},
        {"category": "Utilities", "limit_amount": 180.0, "month": current_month, "notes": "Electricity, water, fiber internet"},
        {"category": "Shopping", "limit_amount": 300.0, "month": current_month, "notes": "Apparel, electronics, personal"}
    ]
    for b in budgets:
        b["user_id"] = user_id
        b["created_at"] = now - timedelta(days=20)
        db.budgets.insert_one(b)

    # 3. Add Sample Transactions
    # Current month transactions designed to trigger various alert thresholds:
    # - Food & Dining: $520 spent out of $600 (~86.7% -> WARNING alert)
    # - Entertainment: $230 spent out of $200 (115% -> OVERSPENDING alert)
    # - Utilities: $95 spent out of $180 (~52.8% -> INFO alert)
    # - Housing & Rent: $1500 spent out of $1500 (100% -> LIMIT REACHED alert)
    
    transactions = [
        # Current Month Incomes
        {"title": "Tech Corp Monthly Salary", "amount": 4850.00, "type": "Income", "category": "Salary", "date": f"{current_month}-01", "description": "Direct deposit salary"},
        {"title": "UI Design Freelance Project", "amount": 750.00, "type": "Income", "category": "Freelance", "date": f"{current_month}-12", "description": "Website redesign for fintech client"},
        {"title": "Dividend Payout", "amount": 120.00, "type": "Income", "category": "Investments", "date": f"{current_month}-18", "description": "Quarterly index fund dividend"},

        # Current Month Expenses
        {"title": "Monthly Apartment Rent", "amount": 1500.00, "type": "Expense", "category": "Housing & Rent", "date": f"{current_month}-02", "description": "Downtown apartment rent"},
        {"title": "Whole Foods Grocery", "amount": 185.50, "type": "Expense", "category": "Food & Dining", "date": f"{current_month}-04", "description": "Weekly pantry and fresh produce"},
        {"title": "Electric & Water Bill", "amount": 95.00, "type": "Expense", "category": "Utilities", "date": f"{current_month}-05", "description": "City Power and Water Co."},
        {"title": "Metro Monthly Pass", "amount": 110.00, "type": "Expense", "category": "Transportation", "date": f"{current_month}-06", "description": "Subway & bus unlimited pass"},
        {"title": "Dinner with Friends at Bistro", "amount": 142.30, "type": "Expense", "category": "Food & Dining", "date": f"{current_month}-09", "description": "Dinner party"},
        {"title": "Weekend Live Concert Tickets", "amount": 160.00, "type": "Expense", "category": "Entertainment", "date": f"{current_month}-11", "description": "Music festival passes"},
        {"title": "Trader Joe's Groceries", "amount": 112.20, "type": "Expense", "category": "Food & Dining", "date": f"{current_month}-15", "description": "Snacks and household items"},
        {"title": "Gaming & Movie Subscriptions", "amount": 70.00, "type": "Expense", "category": "Entertainment", "date": f"{current_month}-17", "description": "Netflix, Spotify, and Steam"},
        {"title": "Uber Rides", "amount": 45.00, "type": "Expense", "category": "Transportation", "date": f"{current_month}-20", "description": "Airport rides"},
        {"title": "Coffee Shop & Lunches", "amount": 80.00, "type": "Expense", "category": "Food & Dining", "date": f"{current_month}-22", "description": "Work week coffees"},

        # Last Month Transactions
        {"title": "Tech Corp Monthly Salary", "amount": 4850.00, "type": "Income", "category": "Salary", "date": f"{last_month}-01", "description": "Salary payment"},
        {"title": "Apartment Rent", "amount": 1500.00, "type": "Expense", "category": "Housing & Rent", "date": f"{last_month}-02", "description": "Rent"},
        {"title": "Supermarket Shopping", "amount": 480.00, "type": "Expense", "category": "Food & Dining", "date": f"{last_month}-08", "description": "Groceries"},
        {"title": "Utility Bills", "amount": 140.00, "type": "Expense", "category": "Utilities", "date": f"{last_month}-10", "description": "Utilities"},
        {"title": "Electronics Gadget", "amount": 220.00, "type": "Expense", "category": "Shopping", "date": f"{last_month}-16", "description": "Headphones"},
        {"title": "Fuel & Train", "amount": 130.00, "type": "Expense", "category": "Transportation", "date": f"{last_month}-20", "description": "Transit"},

        # Two Months Ago Transactions
        {"title": "Tech Corp Monthly Salary", "amount": 4850.00, "type": "Income", "category": "Salary", "date": f"{two_months_ago}-01", "description": "Salary payment"},
        {"title": "Consulting Stint", "amount": 900.00, "type": "Income", "category": "Freelance", "date": f"{two_months_ago}-15", "description": "Tech consultation"},
        {"title": "Apartment Rent", "amount": 1500.00, "type": "Expense", "category": "Housing & Rent", "date": f"{two_months_ago}-02", "description": "Rent"},
        {"title": "Groceries & Dining", "amount": 510.00, "type": "Expense", "category": "Food & Dining", "date": f"{two_months_ago}-12", "description": "Groceries"},
        {"title": "Flight Ticket", "amount": 340.00, "type": "Expense", "category": "Travel", "date": f"{two_months_ago}-22", "description": "Family visit"}
    ]

    for t in transactions:
        t["user_id"] = user_id
        t["created_at"] = datetime.strptime(t["date"], "%Y-%m-%d")
        db.transactions.insert_one(t)

    # Trigger alert calculation for current month
    calculate_budget_utilization(user_id, current_month)

    return {
        "success": True,
        "message": "Demo data populated successfully!",
        "demo_user": {
            "email": demo_email,
            "password": "Finora2026!"
        },
        "stats": {
            "transactions_created": len(transactions),
            "budgets_created": len(budgets)
        }
    }

if __name__ == "__main__":
    res = seed_sample_data()
    print(res)
