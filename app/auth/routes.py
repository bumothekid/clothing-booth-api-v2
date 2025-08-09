from flask import Blueprint, request, jsonify
#from app.utils.exceptions import EmailInvalidError, PasswordTooShortError, UsernameTooLongError, UsernameTooShortError, EmailAlreadyInUseError, WrongSignInCredentialsError, UsernameAlreadyInUseError, AuthValidationError, UserProfilePictureNotFoundError
from app.utils.authentication_managment import authentication_manager,  authorize_request
from app.utils.user_managment import user_manager
from app.utils.limiter import limiter

auth = Blueprint("auth", __name__)


@auth.route('/guest', methods=['POST'])
@limiter.limit('5 per hour')
def register_guest():
    access_token, expires_in, refresh_token = user_manager.register_guest()

    return jsonify({"access_token": access_token, "expires_in": expires_in, "refresh_token": refresh_token}), 201

@auth.route('/refresh', methods=['POST'])
@limiter.limit('5 per minute')
def refresh_token():
    data = request.get_json()
    refresh_token = data.get("refresh_token")
    access_token = data.get("access_token")

    access_token, expires_in, refresh_token = authentication_manager.refresh_access_token(access_token, refresh_token)

    return jsonify({"access_token": access_token, "expires_in": expires_in, "refresh_token": refresh_token}), 200

@auth.route('/signout', methods=['POST'])
@limiter.limit('2 per minute')
@authorize_request
def delete_refresh_token():
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    authentication_manager.delete_refresh_token(refresh_token)

    return "", 204

@auth.route("/upgrade", methods=["POST"])
@limiter.limit("5 per minute")
@authorize_request
def upgrade_guest():
    token = request.headers["Authorization"]
    data: dict = request.get_json()
    
    email = data.get("email", None)
    username = data.get("username", None)
    password = data.get("password", None)
    profile_picture = data.get("profile_picture", None)
    
    user = user_manager.upgrade_guest_account(token, email, username, password, profile_picture)
    
    return jsonify(user.from_dict), 201

"""
# upgrade account from guest to user
@auth.route('/upgrade', methods=['POST'])
@limiter.limit('5 per')
@authorize_request
def upgrade_guest():
    return
"""

"""
@auth.route('/login', methods=['POST'])
@limiter.limit('5 per minute')
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    missing_data = [field for field in ["email", "username", "password"] if field not in data]
    if "email" not in data and "username" not in data or "password" not in data:
        return jsonify({"error": f"The provided data doesn't contain the following fields: {', '.join(missing_data)}."}), 400
    
    try:
         access_token, expires_in, refresh_token = user_manager.loginWithCredentials(data["password"], data.get("username"), data.get("email"))
    except WrongSignInCredentialsError as e:
        return jsonify({"error": str(e)}), 401
    
    
    return jsonify({"access_token": access_token, "expires_in": expires_in, "refresh_token": refresh_token}), 200
    
"""

"""
@auth.route('/register', methods=['POST'])
@limiter.limit('3 per minute')
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    missing_data = [field for field in ["email", "username", "password", "profile_picture"] if field not in data]
    if missing_data:
        return jsonify({"error": f"The provided data doesn't contain the following fields: {', '.join(missing_data)}."}), 400
    
    profilePicture = str(data["profile_picture"])
    
    if not profilePicture.endswith(".png"):
            profilePicture += ".png"
    
    try:
        access_token, expires_in, refresh_token = user_manager.registerNewUser(data["email"], data["username"], data["password"], profilePicture)
    except (EmailInvalidError, PasswordTooShortError, UsernameTooShortError, UsernameTooLongError, UserProfilePictureNotFoundError) as e:
        return jsonify({"error": str(e)}), 400
    except EmailAlreadyInUseError as e:
        return jsonify({"error": str(e), "key": "email"}), 409
    except UsernameAlreadyInUseError as e:
        return jsonify({"error": str(e), "key": "username"}), 409
    
    return jsonify({"access_token": access_token, "expires_in": expires_in, "refresh_token": refresh_token}), 201
"""


"""
@auth.route('/delete', methods=['DELETE'])
@limiter.limit('2 per minute')
@authorize_request
def delete():
    token = request.headers["Authorization"]
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    if "password" not in data:
        return jsonify({"error": "The provided data doesn't contain the a password."}), 400
    
    try:
        user_manager.deleteAccount(token, data["password"])
    except WrongSignInCredentialsError as e:
        return jsonify({"error": str(e)}), 401

    return jsonify({"message": "User deleted successfully"}), 200
    """