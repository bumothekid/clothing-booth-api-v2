from flask import Blueprint, request, jsonify
from app.utils.outfit_managment import outfit_manager
from app.utils.limiter import limiter
from app.utils.authentication_managment import authorize_request

outfit = Blueprint("outfit", __name__)

@outfit.route('/', methods=['POST'])
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
    
@outfit.route('/<outfit_id>', methods=['GET'])
@limiter.limit('5 per minute')
@authorize_request
def get_outfit(outfit_id: str):
    token = request.headers["Authorization"]
    outfit = outfit_manager.get_outfit_by_id(outfit_id, token)

    return jsonify(outfit.to_dict()), 200

@outfit.route('/list/<user_id>', methods=['GET'])
@limiter.limit('5 per minute')
@authorize_request
def get_outfit_list(user_id: str):
    token = request.headers["Authorization"]
    limit = request.args.get("limit", None)
    offset = request.args.get("offset", None)
    
    if limit is not None:
        limit = 1000
    if offset is not None:
        offset = 0

    outfit_list = outfit_manager.get_list_of_outfits_by_user_id(user_id, token, limit, offset)

    return jsonify({"limit": limit, "offset": offset, "outfits": [outfit.to_dict() for outfit in outfit_list]}), 200

@outfit.route('/<outfit_id>', methods=['DELETE'])
@limiter.limit('5 per minute')
@authorize_request
def delete_outfit(outfit_id: str):
    token = request.headers["Authorization"]
    outfit_manager.delete_outfit_by_id(token, outfit_id)

    return "", 204