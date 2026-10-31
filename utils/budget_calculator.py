from datetime import datetime
from database import get_db

def calculate_budget_utilization(user_id, month=None):
    """
    Calculates spent, remaining, utilization percentage for each budget of a user,
    and updates/triggers budget alert notifications.
    """
    db = get_db()
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")

    budgets_cursor = db.budgets.find({"user_id": str(user_id), "month": month})
    budgets = list(budgets_cursor)

    results = []
    notifications_to_sync = []

    for budget in budgets:
        category = budget.get("category")
        limit_amount = float(budget.get("limit_amount", 0.0))

        # Query all expense transactions for this user, category, and month
        date_prefix = f"^{month}"
        expense_pipeline = [
            {
                "$match": {
                    "user_id": str(user_id),
                    "type": "Expense",
                    "category": category,
                    "date": {"$regex": date_prefix}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_spent": {"$sum": "$amount"}
                }
            }
        ]
        agg_res = list(db.transactions.aggregate(expense_pipeline))
        spent = float(agg_res[0]["total_spent"]) if agg_res else 0.0

        remaining = limit_amount - spent
        percentage = (spent / limit_amount * 100.0) if limit_amount > 0 else 0.0
        percentage_rounded = round(percentage, 1)

        # Determine alert level and status
        alert_info = None
        if percentage > 100.0:
            alert_info = {
                "level": "danger",
                "threshold": 105, # >100%
                "title": f"Overspending Alert: {category}",
                "message": f"You have exceeded your {category} budget by ${abs(remaining):.2f} ({percentage_rounded}% utilized)."
            }
        elif percentage == 100.0:
            alert_info = {
                "level": "danger",
                "threshold": 100,
                "title": f"Budget Limit Reached: {category}",
                "message": f"You have reached 100% of your ${limit_amount:.2f} budget for {category}."
            }
        elif percentage >= 80.0:
            alert_info = {
                "level": "warning",
                "threshold": 80,
                "title": f"Budget Warning: {category}",
                "message": f"Warning: {category} budget is at {percentage_rounded}% utilization (${spent:.2f} of ${limit_amount:.2f})."
            }
        elif percentage >= 50.0:
            alert_info = {
                "level": "info",
                "threshold": 50,
                "title": f"Budget Update: {category}",
                "message": f"Notice: {category} budget has crossed 50% utilization (${spent:.2f} of ${limit_amount:.2f})."
            }

        # Store / update notification if threshold is reached
        if alert_info:
            notif_doc = {
                "user_id": str(user_id),
                "budget_id": str(budget["_id"]),
                "category": category,
                "month": month,
                "threshold": alert_info["threshold"],
                "level": alert_info["level"],
                "title": alert_info["title"],
                "message": alert_info["message"],
                "spent": spent,
                "limit_amount": limit_amount,
                "percentage": percentage_rounded,
                "created_at": datetime.utcnow(),
                "read": False
            }
            # Update existing alert for this month/category/threshold or insert
            db.notifications.update_one(
                {
                    "user_id": str(user_id),
                    "category": category,
                    "month": month,
                    "threshold": alert_info["threshold"]
                },
                {"$set": notif_doc},
                upsert=True
            )

        budget_summary = {
            "id": str(budget["_id"]),
            "user_id": str(user_id),
            "month": month,
            "category": category,
            "limit_amount": limit_amount,
            "spent": round(spent, 2),
            "remaining": round(remaining, 2),
            "utilization_percentage": percentage_rounded,
            "status": "overspent" if percentage > 100 else ("danger" if percentage == 100 else ("warning" if percentage >= 80 else ("info" if percentage >= 50 else "normal")))
        }
        results.append(budget_summary)

    return results
