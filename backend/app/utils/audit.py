from flask import request
from app.extensions import db
from app.models.audit_log import AuditLog


def log_action(actor_user_id, action, target_type=None, target_id=None, **meta):
    """Records a security-relevant action. Never pass therapy content in meta."""
    db.session.add(AuditLog(
        actor_user_id=actor_user_id, action=action, target_type=target_type,
        target_id=target_id, metadata_json=meta or {},
        ip_address=(request.remote_addr if request else None),
    ))
