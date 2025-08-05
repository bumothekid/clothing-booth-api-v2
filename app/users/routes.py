from flask import Blueprint, request, jsonify, Response
from ..utils.user_managment import UserManagment
from ..utils.exceptions import UsernameTooShortError, UsernameTooLongError, UsernameAlreadyInUseError, UserNotFoundError, UnsupportedFileTypeError, UserProfilePictureNotFoundError
from ..utils.limiter import limiter
from ..utils.authentication_managment import authorize_request

users = Blueprint("users", __name__)

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
        username, oldUsername = UserManagment.getInstance().setUsername(data["username"], token)
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
    
    user = UserManagment.getInstance().getMyUser(token)
    
    return jsonify(user.__dict__), 200

@users.route('/<userid>', methods=['GET'])
@limiter.limit('10 per minute')
@authorize_request
def getUserByUserID(userid: str):
    try:
        user = UserManagment.getInstance().getUserByUserID(userid)
    except UserNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    
    return jsonify(user.__dict__), 200

@users.route('/<userid>/profilepicture', methods=['GET'])
@limiter.limit('5 per minute')
@authorize_request
def getUserProfilePicture(userid: str):
    try:
        profilePictureURL = UserManagment.getInstance().getUserProfilePicture(userid)
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
        
        try:
            user = UserManagment.getInstance().setDefaultProfilePicture(profilePicture, token)
        except UserProfilePictureNotFoundError as e:
            return jsonify({"error": str(e)}), 404
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
        
    if len(file.read()) > 2*1024*1024:
        return jsonify({"error": "File is too large (max 2MB)"}), 400
    
    file.seek(0)
    
    try:
        user = UserManagment.getInstance().setProfilePicture(file, token)
    except UnsupportedFileTypeError as e:
        return jsonify({"error": str(e)}), 400
    
    return jsonify(user.__dict__), 200

def getMyUserProfilePicture(token: str) -> Response:
    profilePictureURL = UserManagment.getInstance().getMyProfilePicture(token)
    
    return jsonify({"path": f"{str(profilePictureURL)}"}), 200

def deleteMyUserProfilePicture(token: str):
    try:
        UserManagment.getInstance().removeProfilePicture(token)
    except UserProfilePictureNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    
    return jsonify({"message": "Profile picture deleted successfully"}), 200