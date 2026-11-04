from datetime import datetime
from flask import has_request_context, request

from app.extensions import db
from app.models.audit_log import AuditLog


def enregistrer_audit(action, objet, reference=None, description="", utilisateur=None, ip_adresse=None):
    """Enregistre un événement dans le journal d'audit."""
    if utilisateur is None:
        utilisateur = "Système"
        if has_request_context():
            utilisateur = getattr(request, "remote_user", None) or "Système"

    if ip_adresse is None and has_request_context():
        ip_adresse = request.remote_addr

    log = AuditLog(
        action=str(action).upper(),
        objet=str(objet),
        reference_objet=str(reference) if reference else None,
        description=str(description),
        utilisateur=utilisateur,
        ip_adresse=ip_adresse,
        date_action=datetime.utcnow(),
    )
    db.session.add(log)
    return log
