from flask import Blueprint, request, jsonify
from app.models.resource import Resource

resources_bp = Blueprint("resources", __name__)


@resources_bp.route("", methods=["GET"])
def list_resources():
    category = request.args.get("category")
    query = Resource.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)
    resources = query.all()
    return jsonify({"resources": [r.to_dict() for r in resources]})
