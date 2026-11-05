"""Decorators de contrôle d'accès par rôle."""
from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*roles):
    """Exige que l'utilisateur soit authentifié et possède l'un des rôles donnés.

    Exemple::

        @role_required("admin")
        def gestion_utilisateurs():
            ...

        @role_required("admin", "agent")
        def creer_dossier():
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


def admin_required(view_func):
    """Raccourci pour @role_required('admin')."""
    return role_required("admin")(view_func)


def write_required(view_func):
    """Autorise admin et agent. Bloque le rôle consultation."""
    return role_required("admin", "agent")(view_func)
