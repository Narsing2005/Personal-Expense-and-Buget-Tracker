import os
from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from database import DatabaseManager, get_db

# Import Route Blueprints
from routes.auth_routes import auth_bp
from routes.transaction_routes import transaction_bp
from routes.budget_routes import budget_bp
from routes.dashboard_routes import dashboard_bp
from routes.report_routes import report_bp
from routes.notification_routes import notification_bp

def create_app(config_class=Config):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize JWT
    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "message": "Token has expired. Please log in again."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"success": False, "message": "Signature verification failed. Invalid token."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"success": False, "message": "Authorization token is missing."}), 401

    # Initialize Database
    with app.app_context():
        DatabaseManager.init_db(app)

    # Register API Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(notification_bp)

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "app": "Finora - Personal Expense and Budget Tracker",
            "database_mode": "mock_memory" if DatabaseManager.is_mock() else "mongodb_live",
            "version": "1.0.0"
        }), 200

    # Demo Seed Route for Instant Evaluation
    @app.route("/api/seed", methods=["POST"])
    def seed_demo_data():
        from seed_data import seed_sample_data
        result = seed_sample_data()
        return jsonify(result), 200

    # Frontend Single Page Application routes
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        if path.startswith("api/"):
            return jsonify({"success": False, "message": "Endpoint not found"}), 404
        return render_template("index.html")

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "message": "Internal server error"}), 500

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")
    print(f"🚀 Starting Finora server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
