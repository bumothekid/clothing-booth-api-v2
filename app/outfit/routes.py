import re
from flask import Blueprint, request, jsonify
from app.models.outfit import OutfitSeason, OutfitTags
from app.utils.outfit_managment import outfit_manager
from app.utils.exceptions import OutfitNameTooLongError, OutfitDescriptionTooLongError, OutfitNameTooLongError, OutfitNameTooShortError, OutfitNotFoundError
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
    
    missing_data = [field for field in ["name", "description", "clothing_ids", "seasons", "tags"] if field not in data]
    if missing_data:
        return jsonify({"error": f"The provided data doesn't contain the following fields: {', '.join(missing_data)}."}), 400
    
    try:
        name = str(data["name"]).strip()
        description = str(data["description"]).strip()
        
        seasons: list[str] = data["seasons"]
        for season in seasons:
            if str(season).strip().upper() not in OutfitSeason.__members__:
                return jsonify({"error": f"The provided season ({season}) is not valid."}), 400

        seasons_list = [season.strip().upper() for season in seasons]
        tags: list[str] = data["tags"]
        for tag in tags:
            if tag.strip().upper() not in OutfitTags.__members__:
                return jsonify({"error": f"The provided tag ({tag}) is not valid."}), 400

        tags_list = [tag.strip().upper() for tag in tags]
        
        clothing_ids = data["clothing_ids"]
        
        if not clothing_ids:
            return jsonify({"error": "The clothing_ids field cannot be empty."}), 400
        
        outfit = outfit_manager.create_outfit(token, name, seasons_list, tags_list, clothing_ids, description)
    except (OutfitNameTooShortError, OutfitNameTooLongError, OutfitDescriptionTooLongError) as e:
        return jsonify({"error": str(e)}), 400
    
    return jsonify({"outfit": outfit.to_dict()}), 201
    
@outfit.route('/<outfit_id>', methods=['GET'])
@limiter.limit('5 per minute')
@authorize_request
def get_outfit(outfit_id: str):
    token = request.headers["Authorization"]
    try:
        outfit = outfit_manager.get_outfit_by_id(outfit_id, token)
    except OutfitNotFoundError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify(outfit.to_dict()), 200

@outfit.route('/list/<user_id>', methods=['GET'])
@limiter.limit('5 per minute')
@authorize_request
def get_outfit_list(user_id: str):
    token = request.headers["Authorization"]
    limit = request.args.get("limit", None)
    offset = request.args.get("offset", None)

    if not limit and not offset:
        outfit_list = outfit_manager.get_list_of_outfits_by_user_id(user_id, token)
    else:
        if limit:
            limit = int(limit)
        else:
            limit = 10000

        if offset:
            offset = int(offset)
        else:
            offset = 0

        outfit_list = outfit_manager.get_list_of_outfits_by_user_id(user_id, token, limit, offset)

    return jsonify({"limit": limit, "offset": offset, "outfits": [outfit.to_dict() for outfit in outfit_list]}), 200

@outfit.route('/<outfit_id>', methods=['DELETE'])
@limiter.limit('5 per minute')
@authorize_request
def delete_outfit(outfit_id: str):
    token = request.headers["Authorization"]
    try:
        outfit_manager.delete_outfit(outfit_id, token)
    except OutfitNotFoundError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify({"message": "Outfit deleted successfully"}), 200