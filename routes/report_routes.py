from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db

report_bp = Blueprint("report_bp", __name__, url_prefix="/api/reports")

@report_bp.route("/monthly", methods=["GET"])
@jwt_required()
def get_monthly_report():
    user_id = get_jwt_identity()
    db = get_db()

    year = request.args.get("year", datetime.utcnow().strftime("%Y"))

    pipeline = [
        {
            "$match": {
                "user_id": str(user_id),
                "date": {"$regex": f"^{year}-"}
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
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id.month": 1}}
    ]

    results = list(db.transactions.aggregate(pipeline))
    months_data = {}
    for i in range(1, 13):
        m_str = f"{year}-{i:02d}"
        months_data[m_str] = {
            "month": m_str,
            "income": 0.0,
            "expenses": 0.0,
            "savings": 0.0,
            "savings_rate": 0.0,
            "transaction_count": 0
        }

    for item in results:
        m = item["_id"]["month"]
        t = item["_id"]["type"]
        val = float(item["total"])
        count = int(item["count"])
        if m in months_data:
            months_data[m]["transaction_count"] += count
            if t == "Income":
                months_data[m]["income"] = round(val, 2)
            elif t == "Expense":
                months_data[m]["expenses"] = round(val, 2)

    report_list = []
    for m in sorted(months_data.keys()):
        d = months_data[m]
        d["savings"] = round(d["income"] - d["expenses"], 2)
        d["savings_rate"] = round((d["savings"] / d["income"] * 100.0), 1) if d["income"] > 0 else 0.0
        report_list.append(d)

    total_income = sum(m["income"] for m in report_list)
    total_expense = sum(m["expenses"] for m in report_list)
    total_savings = round(total_income - total_expense, 2)

    return jsonify({
        "success": True,
        "year": year,
        "summary": {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "net_savings": total_savings,
            "overall_savings_rate": round((total_savings / total_income * 100.0), 1) if total_income > 0 else 0.0
        },
        "monthly_breakdown": report_list
    }), 200

@report_bp.route("/category", methods=["GET"])
@jwt_required()
def get_category_report():
    user_id = get_jwt_identity()
    db = get_db()

    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    month = request.args.get("month", "").strip()

    match_filter = {"user_id": str(user_id), "type": "Expense"}
    if month:
        match_filter["date"] = {"$regex": f"^{month}"}
    elif start_date or end_date:
        date_q = {}
        if start_date:
            date_q["$gte"] = start_date
        if end_date:
            date_q["$lte"] = end_date
        match_filter["date"] = date_q

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": "$category",
                "total_amount": {"$sum": "$amount"},
                "count": {"$sum": 1},
                "max_amount": {"$max": "$amount"},
                "min_amount": {"$min": "$amount"},
                "avg_amount": {"$avg": "$amount"}
            }
        },
        {"$sort": {"total_amount": -1}}
    ]

    records = list(db.transactions.aggregate(pipeline))
    overall_expense = sum(float(r["total_amount"]) for r in records)

    category_summary = []
    for r in records:
        spent = float(r["total_amount"])
        pct = round((spent / overall_expense * 100.0), 1) if overall_expense > 0 else 0.0
        category_summary.append({
            "category": r["_id"],
            "total_amount": round(spent, 2),
            "percentage": pct,
            "transaction_count": r["count"],
            "avg_transaction": round(float(r["avg_amount"]), 2),
            "max_transaction": round(float(r["max_amount"]), 2)
        })

    return jsonify({
        "success": True,
        "total_expense": round(overall_expense, 2),
        "category_count": len(category_summary),
        "categories": category_summary
    }), 200

@report_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_summary_report():
    """
    Daily, Weekly, and Comprehensive Summary Report with date range filtering.
    """
    user_id = get_jwt_identity()
    db = get_db()

    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    match_filter = {"user_id": str(user_id)}
    if start_date or end_date:
        date_q = {}
        if start_date:
            date_q["$gte"] = start_date
        if end_date:
            date_q["$lte"] = end_date
        match_filter["date"] = date_q

    # Daily breakdown
    daily_pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": {"date": "$date", "type": "$type"},
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id.date": -1}}
    ]
    daily_raw = list(db.transactions.aggregate(daily_pipeline))
    daily_dict = {}
    for d in daily_raw:
        dt = d["_id"]["date"]
        t = d["_id"]["type"]
        if dt not in daily_dict:
            daily_dict[dt] = {"date": dt, "income": 0.0, "expense": 0.0, "net": 0.0, "count": 0}
        daily_dict[dt]["count"] += d["count"]
        if t == "Income":
            daily_dict[dt]["income"] = round(float(d["total"]), 2)
        else:
            daily_dict[dt]["expense"] = round(float(d["total"]), 2)
        daily_dict[dt]["net"] = round(daily_dict[dt]["income"] - daily_dict[dt]["expense"], 2)

    daily_list = [daily_dict[k] for k in sorted(daily_dict.keys(), reverse=True)]

    total_income = sum(d["income"] for d in daily_list)
    total_expense = sum(d["expense"] for d in daily_list)
    net_savings = round(total_income - total_expense, 2)

    return jsonify({
        "success": True,
        "date_range": {
            "start": start_date or "All time",
            "end": end_date or "Present"
        },
        "summary": {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "net_savings": net_savings,
            "savings_rate": round((net_savings / total_income * 100.0), 1) if total_income > 0 else 0.0,
            "total_days_active": len(daily_list)
        },
        "daily_summary": daily_list[:30]
    }), 200
