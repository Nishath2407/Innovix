from app.extensions import db
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.models.user import User


def login_required(fn):
    """Verifies a valid JWT is present. Every protected endpoint should use
    this (directly or via role_required)."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """Verifies the authenticated user's role is one of allowed_roles.
    Usage: @role_required("therapist", "admin")"""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role")
            if role not in allowed_roles:
                return jsonify({"error": "forbidden", "message": "You don't have access to this resource."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user():
    """Fetches the full User row for the current JWT identity. Returns None
    if not authenticated or user no longer exists/active."""
    user_id = get_jwt_identity()
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        return None
    return user


def owns_resource_or_403(resource_user_id):
    """Call inside a route after loading a resource to confirm the current
    user owns it (or is admin). Raises via abort-like return — caller must
    `return` the result if it is not None."""
    from flask import jsonify
    current_id = get_jwt_identity()
    claims = get_jwt()
    if claims.get("role") == "admin":
        return None
    if current_id != resource_user_id:
        return jsonify({"error": "forbidden", "message": "You don't have access to this resource."}), 403
    return None
