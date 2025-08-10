from flask import Blueprint, request, jsonify
from app.utils.outfit_managment import outfit_manager
from app.utils.limiter import limiter
from app.utils.authentication_managment import authorize_request

outfits = Blueprint("outfits", __name__)

@outfits.route('/', methods=['POST'])
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
    
@outfits.route('/<outfit_id>', methods=['GET'])
@limiter.limit('5 per minute')
@authorize_request
def get_outfit(outfit_id: str):
    token = request.headers["Authorization"]
    outfit = outfit_manager.get_outfit_by_id(outfit_id, token)

    return jsonify(outfit.to_dict()), 200

@outfits.route('/<outfit_id>', methods=['DELETE'])
@limiter.limit('5 per minute')
@authorize_request
def delete_outfit(outfit_id: str):
    token = request.headers["Authorization"]
    outfit_manager.delete_outfit_by_id(token, outfit_id)

    return "", 204