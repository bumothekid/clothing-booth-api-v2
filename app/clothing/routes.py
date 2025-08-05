from flask import Blueprint, request, jsonify
from app.utils.clothing_managment import ClothingManager
from app.utils.limiter import limiter
from app.utils.authentication_managment import authorize_request

clothing = Blueprint("clothing", __name__)

@clothing.route('/', methods=['POST'])
@limiter.limit('5 per minute')
@authorize_request
def create_clothing_piece():
    token = request.headers["Authorization"]
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    missing_data = [field for field in ["name", "description", "category", "color", "seasons", "tags"] if field not in data]
    if missing_data:
        return jsonify({"error": f"The provided data doesn't contain the following fields: {', '.join(missing_data)}."}), 400
    
    name = data.get("name", None)
    description = data.get("description", None)
    category = data.get("category", None)
    color = data.get("color", None)
    seasons = data.get("seasons", [])
    tags = data.get("tags", [])
    image_url = data.get("image_url", None)

    clothing = ClothingManager.getInstance().create_clothing(token, name, category, image_url.split("/")[-1] if image_url.endswith(".webp") else image_url.split("/")[-1] + ".webp", color, seasons, tags, description)

    return jsonify(clothing.to_dict()), 201

@clothing.route('/<clothing_id>', methods=['GET'])
@limiter.limit('5 per minute')
@authorize_request
def get_clothing_piece(clothing_id: str):
    token = request.headers["Authorization"]
    clothing = ClothingManager.getInstance().get_clothing_by_id(clothing_id, token)
    return jsonify(clothing.to_dict()), 200

@clothing.route('/list/<user_id>', methods=['GET'])
@limiter.limit('5 per minute')
@authorize_request
def get_clothing_list(user_id: str):
    token = request.headers["Authorization"]
    limit = request.args.get("limit", None)
    offset = request.args.get("offset", None)

    if not limit and not offset:
        clothing_list = ClothingManager.getInstance().get_list_of_clothing_by_user_id(user_id, token)
    else:
        if limit:
            limit = int(limit)
        else:
            limit = 10000

        if offset:
            offset = int(offset)
        else:
            offset = 0
        
        clothing_list = ClothingManager.getInstance().get_list_of_clothing_by_user_id(user_id, token, limit, offset)

    return jsonify({"limit": limit, "offset": offset, "clothing": [clothing.to_dict() for clothing in clothing_list]}), 200

@clothing.route('<clothing_id>', methods=['DELETE'])
@limiter.limit('5 per minute')
@authorize_request
def delete_clothing_piece(clothing_id: str):
    token = request.headers["Authorization"]
    
    ClothingManager.getInstance().delete_clothing_by_id(clothing_id, token)

    return "", 204

"""
@clothing.route('/<clothingID>', methods=['PUT'])
@limiter.limit('5 per minute')
@authorize_request
def updateClothing(clothingID: str):
    token = request.headers["Authorization"]
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        name = data.get("name")
        description = data.get("description")
        category = data.get("category")
        color = data.get("color")
        seasons = data.get("seasons")
        tags = data.get("tags")
        image_url = data.get("image")
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    if not any([name, description, category, color, seasons, tags, image_url]):
        return jsonify({"error": "No data provided"}), 400
    
    if name:
        name = str(name).strip()
        
    if description:
        description = str(description).strip()
        
    if color:
        color = str(color).strip()
        colorRegex = r"^#([A-Fa-f0-9]{6})$"
        if not re.match(colorRegex, color):
            return jsonify({"error": "The provided color is not valid"}), 400
        
    if category:
        category = str(category).upper()
        if category not in ClothingCategory.__members__:
            return jsonify({"error": "The provided category is not valid."}), 400
        
        category = ClothingCategory[category].name
    
    seasonsList = None
    if seasons is not None:
        seasons: list[str] = seasons
        for season in seasons:
            if str(season).capitalize() not in ["Spring", "Summer", "Autumn", "Winter"]:
                return jsonify({"error": f"The provided season ({season}) is not valid."}), 400
            
        seasonsList = [season.capitalize() for season in seasons]
    
    tagsList = None
    if tags is not None:
        tags: list[str] = tags
        for tag in tags:
            if tag.capitalize() not in ["Casual", "Formal", "Sports", "Vintage"]:
                return jsonify({"error": f"The provided tag ({tag}) is not valid."}), 400
            
        tagsList = [tag.capitalize() for tag in tags]
    
    try:
        clothing = ClothingManager.getInstance().updateClothing(token, clothingID, name, category, description, color, seasonsList, tagsList, image_url)
    except ClothingNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except (ClothingNameTooShortError, ClothingNameTooLongError, ClothingDescriptionTooLongError) as e:
        return jsonify({"error": str(e)}), 400
    
    return jsonify(clothing.to_dict()), 200
    """