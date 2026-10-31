from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import get_db
from utils.auth_helpers import serialize_doc
from utils.validators import validate_transaction
from utils.budget_calculator import calculate_budget_utilization

transaction_bp = Blueprint("transaction_bp", __name__, url_prefix="/api/transactions")

@transaction_bp.route("", methods=["GET"])
@jwt_required()
def get_transactions():
    user_id = get_jwt_identity()
    db = get_db()

    query = {"user_id": str(user_id)}

    # Filtering
    search = request.args.get("search", "").strip()
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]

    category = request.args.get("category", "").strip()
    if category and category.lower() != "all":
        query["category"] = category

    t_type = request.args.get("type", "").strip()
    if t_type and t_type.lower() != "all":
        query["type"] = t_type.capitalize()

    month = request.args.get("month", "").strip()
    if month:
        query["date"] = {"$regex": f"^{month}"}

    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        query["date"] = date_filter

    # Sorting
    sort_field = request.args.get("sort_by", "date")
    sort_order = -1 if request.args.get("order", "desc").lower() == "desc" else 1

    sort_criteria = [(sort_field, sort_order)]
    if sort_field != "_id":
        sort_criteria.append(("_id", -1))

    # Pagination
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(500, max(1, int(request.args.get("limit", 100))))
    except ValueError:
        page, limit = 1, 100

    skip = (page - 1) * limit

    total_count = db.transactions.count_documents(query)
    cursor = db.transactions.find(query).sort(sort_criteria).skip(skip).limit(limit)
    transactions = [serialize_doc(doc) for doc in cursor]

    return jsonify({
        "success": True,
        "count": len(transactions),
        "total": total_count,
        "page": page,
        "limit": limit,
        "transactions": transactions
    }), 200

@transaction_bp.route("", methods=["POST"])
@jwt_required()
def create_transaction():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    is_valid, errors = validate_transaction(data)
    if not is_valid:
        return jsonify({"success": False, "message": "Validation failed", "errors": errors}), 400

    db = get_db()
    amount = round(float(data["amount"]), 2)
    t_type = data["type"].strip().capitalize()
    t_date = data["date"].strip()

    new_transaction = {
        "user_id": str(user_id),
        "title": data["title"].strip(),
        "amount": amount,
        "type": t_type,
        "category": data["category"].strip(),
        "date": t_date,
        "description": data.get("description", "").strip(),
        "created_at": datetime.utcnow()
    }

    result = db.transactions.insert_one(new_transaction)
    created_id = str(result.inserted_id)

    # If expense, recalculate budget alerts for that transaction's month
    if t_type == "Expense":
        t_month = t_date[:7]
        try:
            calculate_budget_utilization(user_id, t_month)
        except Exception:
            pass

    new_transaction["id"] = created_id
    new_transaction.pop("_id", None)

    return jsonify({
        "success": True,
        "message": f"{t_type} transaction created successfully.",
        "transaction": serialize_doc(new_transaction)
    }), 201

@transaction_bp.route("/<transaction_id>", methods=["PUT"])
@jwt_required()
def update_transaction(transaction_id):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    is_valid, errors = validate_transaction(data)
    if not is_valid:
        return jsonify({"success": False, "message": "Validation failed", "errors": errors}), 400

    db = get_db()
    try:
        obj_id = ObjectId(transaction_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid transaction ID format."}), 400

    existing = db.transactions.find_one({"_id": obj_id, "user_id": str(user_id)})
    if not existing:
        return jsonify({"success": False, "message": "Transaction not found or access denied."}), 404

    amount = round(float(data["amount"]), 2)
    t_type = data["type"].strip().capitalize()
    t_date = data["date"].strip()

    update_fields = {
        "title": data["title"].strip(),
        "amount": amount,
        "type": t_type,
        "category": data["category"].strip(),
        "date": t_date,
        "description": data.get("description", "").strip(),
        "updated_at": datetime.utcnow()
    }

    db.transactions.update_one({"_id": obj_id}, {"$set": update_fields})

    # Recalculate alerts
    t_month = t_date[:7]
    try:
        calculate_budget_utilization(user_id, t_month)
    except Exception:
        pass

    updated_doc = db.transactions.find_one({"_id": obj_id})

    return jsonify({
        "success": True,
        "message": "Transaction updated successfully.",
        "transaction": serialize_doc(updated_doc)
    }), 200

@transaction_bp.route("/<transaction_id>", methods=["DELETE"])
@jwt_required()
def delete_transaction(transaction_id):
    user_id = get_jwt_identity()
    db = get_db()

    try:
        obj_id = ObjectId(transaction_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid transaction ID format."}), 400

    existing = db.transactions.find_one({"_id": obj_id, "user_id": str(user_id)})
    if not existing:
        return jsonify({"success": False, "message": "Transaction not found or access denied."}), 404

    t_month = existing.get("date", "")[:7]
    db.transactions.delete_one({"_id": obj_id})

    # Recalculate alerts after deletion
    if t_month:
        try:
            calculate_budget_utilization(user_id, t_month)
        except Exception:
            pass

    return jsonify({
        "success": True,
        "message": "Transaction deleted successfully."
    }), 200
