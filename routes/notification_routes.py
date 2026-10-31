from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import get_db
from utils.auth_helpers import serialize_doc
from utils.budget_calculator import calculate_budget_utilization

notification_bp = Blueprint("notification_bp", __name__, url_prefix="/api/notifications")

@notification_bp.route("", methods=["GET"])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    db = get_db()

    # Re-sync current month's budget utilization alerts
    current_month = datetime.utcnow().strftime("%Y-%m")
    try:
        calculate_budget_utilization(user_id, current_month)
    except Exception:
        pass

    cursor = db.notifications.find({"user_id": str(user_id)}).sort("created_at", -1).limit(50)
    notifications = [serialize_doc(doc) for doc in cursor]
    unread_count = sum(1 for n in notifications if not n.get("read", False))

    return jsonify({
        "success": True,
        "total": len(notifications),
        "unread_count": unread_count,
        "notifications": notifications
    }), 200

@notification_bp.route("/<notification_id>/read", methods=["POST"])
@jwt_required()
def mark_as_read(notification_id):
    user_id = get_jwt_identity()
    db = get_db()

    try:
        obj_id = ObjectId(notification_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid ID format."}), 400

    result = db.notifications.update_one(
        {"_id": obj_id, "user_id": str(user_id)},
        {"$set": {"read": True}}
    )

    if result.matched_count == 0:
        return jsonify({"success": False, "message": "Notification not found."}), 404

    return jsonify({"success": True, "message": "Notification marked as read."}), 200

@notification_bp.route("/clear", methods=["POST"])
@jwt_required()
def clear_all():
    user_id = get_jwt_identity()
    db = get_db()

    db.notifications.update_many(
        {"user_id": str(user_id)},
        {"$set": {"read": True}}
    )

    return jsonify({"success": True, "message": "All notifications marked as read."}), 200
