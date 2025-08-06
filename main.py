import os
from flask import Flask, jsonify
from app.utils.limiter import limiter
from app.utils.logging import get_logger
from app.utils.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    PermissionError
)
from app.utils.authentication_managment import authentication_manager
from app.utils.user_managment import user_manager
from app.utils.clothing_managment import clothing_manager
from app.utils.outfit_managment import outfit_manager
from app.main.routes import api as main
from app.auth.routes import auth
#from app.users.routes import users
#from app.uploads.routes import uploads
from app.clothing.routes import clothing
from app.images.routes import images
from app.outfit.routes import outfit

api = Flask("Clothing Booth API")

logger = get_logger()

limiter.init_app(api)
api.register_blueprint(main)
api.register_blueprint(auth, url_prefix="/auth")
#api.register_blueprint(users, url_prefix="/users")
api.register_blueprint(clothing, url_prefix="/clothing")
#api.register_blueprint(uploads, url_prefix="/uploads")
api.register_blueprint(images, url_prefix="/images")
api.register_blueprint(outfit, url_prefix="/outfit")
logger.info("API registered blueprints")

# ? Go through the code and add comments
# ? Go through all the routes and check their response codes

@api.errorhandler(ValidationError)
def validation_error_handler(error):
    return jsonify({"error": str(error)}), 400

@api.errorhandler(NotFoundError)
def not_found_error_handler(error):
    return jsonify({"error": str(error)}), 404

@api.errorhandler(ConflictError)
def conflict_error_handler(error):
    return jsonify({"error": str(error)}), 409

@api.errorhandler(PermissionError)
def outfit_permission_error_handler(error):
    return jsonify({"error": str(error)}), 403

@api.errorhandler(Exception)
def internal_error_handler(error):
    return jsonify({"error": "An unexpected error occurred."}), 500

@api.errorhandler(404)
def not_found_error_handler(error):
    return jsonify({"error": "Resource not found."}), 404

if not os.path.exists("logs"):
    try:
        os.makedirs("logs", exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating logs directory: {e}")
        
    logger.info("Logs directory created or already exists.")

if not os.path.exists("app/static/temp"):
    try:
        os.makedirs("app/static/temp", exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating temp directory: {e}")
        
    logger.info("Temporary images directory created or already exists.")

def initialize_database():
    user_manager.ensure_table_exists()
    authentication_manager.ensure_table_exists()
    clothing_manager.ensure_table_exists()
    outfit_manager.ensure_table_exists()
    
    logger.info("Database initialized successfully.")

if __name__ == '__main__':
    initialize_database()
    logger.info("Starting API in debug mode")
    api.run(host="0.0.0.0", debug=True, port=8000)
else:
    initialize_database()
    logger.info("Starting API in production mode")