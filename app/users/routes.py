from flask import Blueprint, request, jsonify, Response
from ..utils.user_managment import user_manager
from app.utils.outfit_managment import outfit_manager
from app.utils.clothing_managment import clothing_manager
from ..utils.exceptions import UsernameTooShortError, UsernameTooLongError, UsernameAlreadyInUseError, UserNotFoundError, UnsupportedFileTypeError
from ..utils.limiter import limiter
from ..utils.authentication_managment import authorize_request

users = Blueprint("users", __name__)

@users.route('/<user_id>/outfits', methods=['GET'])
@limiter.limit('5 per minute')
@authorize_request
def get_outfit_list(user_id: str):
    token = request.headers["Authorization"]
    limit = request.args.get("limit", 1000)
    offset = request.args.get("offset", 0)

    outfit_list = outfit_manager.get_list_of_outfits_by_user_id(token, user_id, limit, offset)

    return jsonify({"limit": limit, "offset": offset, "outfits": [outfit.to_dict() for outfit in outfit_list]}), 200
    
@users.route('/me/outfits', methods=['POST'])
@limiter.limit('5 per minute')
@authorize_request
def create_outfit():
    token = request.headers['Authorization']
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    name = data.get("name", None)
    description = data.get("description", None)
    clothing_ids = data.get("clothing_ids", None)
    seasons = data.get("seasons", None)
    tags = data.get("tags", None)
    outfit = outfit_manager.create_outfit(token, name, clothing_ids, seasons, tags, description)

    return jsonify({"outfit": outfit.to_dict()}), 201

@users.route('/<user_id>/clothing', methods=['GET'])
@limiter.limit('5 per minute')
@authorize_request
def get_clothing_list(user_id: str):
    token = request.headers["Authorization"]
    limit = request.args.get("limit", 1000)
    offset = request.args.get("offset", 0)

    clothing_list = clothing_manager.get_list_of_clothing_by_user_id(token, user_id, limit, offset)

    return jsonify({"limit": limit, "offset": offset, "clothing": [clothing.to_dict() for clothing in clothing_list]}), 200

@users.route('/me/clothing', methods=['POST'])
@limiter.limit('5 per minute')
@authorize_request
def create_clothing_piece():
    token = request.headers["Authorization"]
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    name = data.get("name", None)
    description = data.get("description", None)
    category = data.get("category", None)
    color = data.get("color", None)
    seasons = data.get("seasons", [])
    tags = data.get("tags", [])
    image_url = data.get("image_url", None)

    clothing = clothing_manager.create_clothing(token, name, category, image_url.split("/")[-1] if image_url.endswith(".webp") else image_url.split("/")[-1] + ".webp", color, seasons, tags, description)

    return jsonify(clothing.to_dict()), 201

@users.route('/me/username', methods=['PUT'])
@authorize_request
@limiter.limit('1 per hour')
def setUsername():
    data = request.get_json()
    token = request.headers["Authorization"]
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    if "username" not in data:
        return jsonify({"error": "Missing username"}), 400
    
    try:
        username, oldUsername = user_manager.setUsername(data["username"], token)
    except (UsernameTooShortError, UsernameTooLongError) as e:
        return jsonify({"error": str(e)}), 400
    except UsernameAlreadyInUseError as e:
        return jsonify({"error": str(e), "key": "username"}), 409
    
    return jsonify({"username": username, "old_username": oldUsername}), 200


@users.route('/me', methods=['GET'])
@limiter.limit('10 per minute')
@authorize_request
def getMyUser():
    token = request.headers["Authorization"]
    
    user = user_manager.getMyUser(token)
    
    return jsonify(user.__dict__), 200

@users.route('/<userid>', methods=['GET'])
@limiter.limit('10 per minute')
@authorize_request
def getUserByUserID(userid: str):
    try:
        user = user_manager.getUserByUserID(userid)
    except UserNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    
    return jsonify(user.__dict__), 200

@users.route('/<userid>/profilepicture', methods=['GET'])
@limiter.limit('5 per minute')
@authorize_request
def getUserProfilePicture(userid: str):
    try:
        profilePictureURL = user_manager.getUserProfilePicture(userid)
    except UserNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    
    return jsonify({"path": f"{str(profilePictureURL)}"}), 200


@users.route('/me/profilepicture', methods=['PUT', 'GET', 'DELETE'])
@limiter.limit('5 per minute')
@authorize_request
def userProfilePicture():
    token = request.headers["Authorization"]
    
    if request.method == 'GET':
        return getMyUserProfilePicture(token)
    elif request.method == 'PUT':
        return setMyUserProfilePicture(token)
    else:
        return deleteMyUserProfilePicture()
        
def setMyUserProfilePicture(token: str) -> Response:
    if "file" not in request.files:
        profilePicture = request.args.get("named")
        
        if not profilePicture:
            return jsonify({"error": "No file provided"}), 400
        
        if not profilePicture.endswith(".png"):
            profilePicture += ".png"
        
        #try:
        #    user = user_manager.setDefaultProfilePicture(profilePicture, token)
        #except UserProfilePictureNotFoundError as e:
        #    return jsonify({"error": str(e)}), 404
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
        
    if len(file.read()) > 2*1024*1024:
        return jsonify({"error": "File is too large (max 2MB)"}), 400
    
    file.seek(0)
    
    try:
        user = user_manager.setProfilePicture(file, token)
    except UnsupportedFileTypeError as e:
        return jsonify({"error": str(e)}), 400
    
    return jsonify(user.__dict__), 200

def getMyUserProfilePicture(token: str) -> Response:
    profilePictureURL = user_manager.getMyProfilePicture(token)
    
    return jsonify({"path": f"{str(profilePictureURL)}"}), 200

def deleteMyUserProfilePicture(token: str):
    #try:
    #    user_manager.removeProfilePicture(token)
    #except UserProfilePictureNotFoundError as e:
    #    return jsonify({"error": str(e)}), 404
    
    return jsonify({"message": "Profile picture deleted successfully"}), 200