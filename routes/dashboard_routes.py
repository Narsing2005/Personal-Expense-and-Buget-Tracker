from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
from utils.auth_helpers import serialize_doc
from utils.budget_calculator import calculate_budget_utilization

dashboard_bp = Blueprint("dashboard_bp", __name__, url_prefix="/api/dashboard")

@dashboard_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_dashboard_summary():
    user_id = get_jwt_identity()
    db = get_db()

    target_month = request.args.get("month", "").strip()
    if not target_month:
        target_month = datetime.utcnow().strftime("%Y-%m")

    # All-time transactions aggregation
    all_time_pipeline = [
        {"$match": {"user_id": str(user_id)}},
        {"$group": {
            "_id": "$type",
            "total": {"$sum": "$amount"}
        }}
    ]
    all_time_res = {item["_id"]: item["total"] for item in db.transactions.aggregate(all_time_pipeline)}
    all_income = float(all_time_res.get("Income", 0.0))
    all_expense = float(all_time_res.get("Expense", 0.0))
    current_balance = all_income - all_expense

    # Current month aggregation
    monthly_pipeline = [
        {
            "$match": {
                "user_id": str(user_id),
                "date": {"$regex": f"^{target_month}"}
            }
        },
        {
            "$group": {
                "_id": "$type",
                "total": {"$sum": "$amount"}
            }
        }
    ]
    monthly_res = {item["_id"]: item["total"] for item in db.transactions.aggregate(monthly_pipeline)}
    monthly_income = float(monthly_res.get("Income", 0.0))
    monthly_expense = float(monthly_res.get("Expense", 0.0))
    monthly_savings = monthly_income - monthly_expense
    savings_rate = round((monthly_savings / monthly_income * 100.0), 1) if monthly_income > 0 else 0.0

    # Budget metrics for the month
    budgets = calculate_budget_utilization(user_id, target_month)
    total_budgeted = sum(b["limit_amount"] for b in budgets)
    total_budget_spent = sum(b["spent"] for b in budgets)
    budget_utilization = round((total_budget_spent / total_budgeted * 100.0), 1) if total_budgeted > 0 else 0.0

    # Recent transactions (top 5 sorted by date desc, _id desc)
    recent_cursor = db.transactions.find({"user_id": str(user_id)}).sort([("date", -1), ("_id", -1)]).limit(5)
    recent_transactions = [serialize_doc(doc) for doc in recent_cursor]

    # Active alerts count
    unread_alerts = db.notifications.count_documents({"user_id": str(user_id), "read": False})

    return jsonify({
        "success": True,
        "month": target_month,
        "summary": {
            "total_income": round(all_income, 2),
            "total_expenses": round(all_expense, 2),
            "current_balance": round(current_balance, 2),
            "monthly_income": round(monthly_income, 2),
            "monthly_expenses": round(monthly_expense, 2),
            "monthly_savings": round(monthly_savings, 2),
            "savings_rate": savings_rate,
            "total_budgeted": round(total_budgeted, 2),
            "budget_spent": round(total_budget_spent, 2),
            "budget_utilization": budget_utilization,
            "unread_alerts": unread_alerts
        },
        "recent_transactions": recent_transactions
    }), 200

@dashboard_bp.route("/analytics", methods=["GET"])
@jwt_required()
def get_dashboard_analytics():
    user_id = get_jwt_identity()
    db = get_db()

    target_month = request.args.get("month", "").strip()
    if not target_month:
        target_month = datetime.utcnow().strftime("%Y-%m")

    # 1. Income vs Expense for last 6 months
    now = datetime.utcnow()
    month_keys = []
    month_labels = []
    for i in range(5, -1, -1):
        dt = (now.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        key = dt.strftime("%Y-%m")
        if key not in month_keys:
            month_keys.append(key)
            month_labels.append(dt.strftime("%b %Y"))

    # Fetch transactions for these 6 months
    earliest_prefix = month_keys[0]
    multi_month_pipeline = [
        {
            "$match": {
                "user_id": str(user_id),
                "date": {"$gte": f"{earliest_prefix}-01"}
            }
        },
        {
            "$project": {
                "month": {"$substr": ["$date", 0, 7]},
                "type": "$type",
                "amount": "$amount"
            }
        },
        {
            "$group": {
                "_id": {"month": "$month", "type": "$type"},
                "total": {"$sum": "$amount"}
            }
        }
    ]
    multi_res = list(db.transactions.aggregate(multi_month_pipeline))

    income_by_month = {k: 0.0 for k in month_keys}
    expense_by_month = {k: 0.0 for k in month_keys}

    for item in multi_res:
        m = item["_id"].get("month")
        t = item["_id"].get("type")
        val = float(item["total"])
        if m in income_by_month:
            if t == "Income":
                income_by_month[m] = round(val, 2)
            elif t == "Expense":
                expense_by_month[m] = round(val, 2)

    income_series = [income_by_month[m] for m in month_keys]
    expense_series = [expense_by_month[m] for m in month_keys]
    savings_series = [round(income_series[i] - expense_series[i], 2) for i in range(len(month_keys))]

    # 2. Category-wise expense breakdown for selected month
    cat_pipeline = [
        {
            "$match": {
                "user_id": str(user_id),
                "type": "Expense",
                "date": {"$regex": f"^{target_month}"}
            }
        },
        {
            "$group": {
                "_id": "$category",
                "total": {"$sum": "$amount"}
            }
        },
        {"$sort": {"total": -1}}
    ]
    cat_res = list(db.transactions.aggregate(cat_pipeline))
    category_labels = [c["_id"] for c in cat_res]
    category_data = [round(float(c["total"]), 2) for c in cat_res]

    # 3. Daily spending trend for selected month
    daily_pipeline = [
        {
            "$match": {
                "user_id": str(user_id),
                "type": "Expense",
                "date": {"$regex": f"^{target_month}"}
            }
        },
        {
            "$group": {
                "_id": "$date",
                "total": {"$sum": "$amount"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    daily_res = list(db.transactions.aggregate(daily_pipeline))
    daily_labels = [d["_id"] for d in daily_res]
    daily_data = [round(float(d["total"]), 2) for d in daily_res]

    return jsonify({
        "success": True,
        "month": target_month,
        "income_vs_expense": {
            "labels": month_labels,
            "months": month_keys,
            "income": income_series,
            "expense": expense_series,
            "savings": savings_series
        },
        "category_breakdown": {
            "labels": category_labels,
            "data": category_data
        },
        "monthly_trend": {
            "labels": month_labels,
            "expense": expense_series
        },
        "daily_trend": {
            "labels": daily_labels,
            "data": daily_data
        }
    }), 200
