from flask import Blueprint, request, jsonify
from app.utils.limiter import limiter
from app.utils.exceptions import FileTooLargeError, ImageUnclearError
from app.utils.authentication_managment import authorize_request
from app.utils.image_managment import ImageManager

images = Blueprint("images", __name__)

@images.route("/preview", methods=['POST'])
@limiter.limit("1 per minute")
@authorize_request
def generate_image():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    size = file.read()
    if len(size) > 4*1024*1024:
        return jsonify({"error": "File is too large (max 4MB)"}), 413
    try:
        removed_background_url, _ = ImageManager.getInstance().remove_background(file)
    except FileTooLargeError as e:
        return jsonify({"error": str(e)}), 413
    except ImageUnclearError as e:
        return jsonify({"error": str(e)}), 422

    return jsonify({"image_url": removed_background_url}), 201