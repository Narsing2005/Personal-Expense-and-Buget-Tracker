from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import get_db
from utils.auth_helpers import serialize_doc
from utils.validators import validate_budget
from utils.budget_calculator import calculate_budget_utilization

budget_bp = Blueprint("budget_bp", __name__, url_prefix="/api/budgets")

@budget_bp.route("", methods=["GET"])
@jwt_required()
def get_budgets():
    user_id = get_jwt_identity()
    month = request.args.get("month", "").strip()
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")

    budgets_with_metrics = calculate_budget_utilization(user_id, month)

    total_budgeted = sum(b["limit_amount"] for b in budgets_with_metrics)
    total_spent = sum(b["spent"] for b in budgets_with_metrics)
    total_remaining = total_budgeted - total_spent
    overall_utilization = round((total_spent / total_budgeted * 100.0), 1) if total_budgeted > 0 else 0.0

    return jsonify({
        "success": True,
        "month": month,
        "summary": {
            "total_budgeted": round(total_budgeted, 2),
            "total_spent": round(total_spent, 2),
            "total_remaining": round(total_remaining, 2),
            "overall_utilization": overall_utilization
        },
        "budgets": budgets_with_metrics
    }), 200

@budget_bp.route("", methods=["POST"])
@jwt_required()
def create_budget():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    is_valid, errors = validate_budget(data)
    if not is_valid:
        return jsonify({"success": False, "message": "Validation failed", "errors": errors}), 400

    month = data["month"].strip()
    category = data["category"].strip()
    limit_amount = round(float(data["limit_amount"]), 2)

    db = get_db()
    # Check if budget for this month and category already exists
    existing = db.budgets.find_one({
        "user_id": str(user_id),
        "month": month,
        "category": category
    })
    if existing:
        return jsonify({
            "success": False,
            "message": f"A budget for '{category}' already exists for {month}. You can edit it instead."
        }), 409

    new_budget = {
        "user_id": str(user_id),
        "month": month,
        "category": category,
        "limit_amount": limit_amount,
        "notes": data.get("notes", "").strip(),
        "created_at": datetime.utcnow()
    }

    result = db.budgets.insert_one(new_budget)
    created_id = str(result.inserted_id)

    # Recalculate utilization and alert notifications
    metrics = calculate_budget_utilization(user_id, month)
    matched_metric = next((b for b in metrics if b["id"] == created_id), None)

    return jsonify({
        "success": True,
        "message": "Budget created successfully.",
        "budget": matched_metric or {
            "id": created_id,
            "user_id": str(user_id),
            "month": month,
            "category": category,
            "limit_amount": limit_amount,
            "spent": 0.0,
            "remaining": limit_amount,
            "utilization_percentage": 0.0,
            "status": "normal"
        }
    }), 201

@budget_bp.route("/<budget_id>", methods=["PUT"])
@jwt_required()
def update_budget(budget_id):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    is_valid, errors = validate_budget(data)
    if not is_valid:
        return jsonify({"success": False, "message": "Validation failed", "errors": errors}), 400

    db = get_db()
    try:
        obj_id = ObjectId(budget_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid budget ID format."}), 400

    existing = db.budgets.find_one({"_id": obj_id, "user_id": str(user_id)})
    if not existing:
        return jsonify({"success": False, "message": "Budget not found or access denied."}), 404

    month = data["month"].strip()
    category = data["category"].strip()
    limit_amount = round(float(data["limit_amount"]), 2)

    # Check collision if category/month changed
    duplicate = db.budgets.find_one({
        "_id": {"$ne": obj_id},
        "user_id": str(user_id),
        "month": month,
        "category": category
    })
    if duplicate:
        return jsonify({
            "success": False,
            "message": f"Another budget for '{category}' already exists for {month}."
        }), 409

    update_fields = {
        "month": month,
        "category": category,
        "limit_amount": limit_amount,
        "notes": data.get("notes", "").strip(),
        "updated_at": datetime.utcnow()
    }

    db.budgets.update_one({"_id": obj_id}, {"$set": update_fields})

    # Recalculate metrics
    metrics = calculate_budget_utilization(user_id, month)
    matched_metric = next((b for b in metrics if b["id"] == str(obj_id)), None)

    return jsonify({
        "success": True,
        "message": "Budget updated successfully.",
        "budget": matched_metric
    }), 200

@budget_bp.route("/<budget_id>", methods=["DELETE"])
@jwt_required()
def delete_budget(budget_id):
    user_id = get_jwt_identity()
    db = get_db()

    try:
        obj_id = ObjectId(budget_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid budget ID format."}), 400

    existing = db.budgets.find_one({"_id": obj_id, "user_id": str(user_id)})
    if not existing:
        return jsonify({"success": False, "message": "Budget not found or access denied."}), 404

    # Remove associated notifications for this budget
    db.notifications.delete_many({"budget_id": str(obj_id)})
    db.budgets.delete_one({"_id": obj_id})

    return jsonify({
        "success": True,
        "message": "Budget deleted successfully."
    }), 200
