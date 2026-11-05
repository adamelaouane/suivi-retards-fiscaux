import os
import secrets
import warnings

from flask import Flask, render_template, request, abort
from flask_login import current_user

from app.extensions import csrf, db, migrate, login_manager

_DEFAULT_SECRET = "dev-key-change-me-suivi-retards-fiscaux"


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)

    secret = os.getenv("SECRET_KEY", "").strip()
    if not secret:
        if (config or {}).get("TESTING"):
            secret = "test-secret-key-not-for-production"
        else:
            # En développement uniquement : générer une clé volatile et avertir.
            secret = _DEFAULT_SECRET
            warnings.warn(
                "SECRET_KEY non définie. Utilisez un fichier .env avec une clé forte "
                "(python -c \"import secrets; print(secrets.token_hex(32))\").",
                UserWarning,
                stacklevel=2,
            )
    app.config["SECRET_KEY"] = secret

    os.makedirs(app.instance_path, exist_ok=True)

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "sqlite:///" + os.path.join(app.instance_path, "fiscal.db")
        )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 Mo max par import
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    if config:
        app.config.update(config)

    if app.config.get("TESTING"):
        app.config["WTF_CSRF_ENABLED"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    # Charger les modèles
    from app import models  # noqa: F401
    from app.models import User

    # Importer les Blueprints
    from app.auth.routes import auth_bp
    from app.accueil.routes import accueil_bp
    from app.contribuables.routes import contribuables_bp
    from app.dossiers.routes import dossiers_bp
    from app.importation.routes import importation_bp
    from app.paiements.routes import paiements_bp
    from app.parametres.routes import parametres_bp
    from app.rapports.routes import rapports_bp
    from app.recherche.routes import recherche_bp
    from app.relances.routes import relances_bp
    from app.suivi_impayes.routes import suivi_impayes_bp
    from app.synthese.routes import synthese_bp
    from app.types_taxes.routes import types_taxes_bp

    # Enregistrer les Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(accueil_bp)
    app.register_blueprint(suivi_impayes_bp)
    app.register_blueprint(recherche_bp)
    app.register_blueprint(synthese_bp)
    app.register_blueprint(rapports_bp)
    app.register_blueprint(importation_bp)
    app.register_blueprint(contribuables_bp)
    app.register_blueprint(types_taxes_bp)
    app.register_blueprint(dossiers_bp)
    app.register_blueprint(paiements_bp)
    app.register_blueprint(relances_bp)
    app.register_blueprint(parametres_bp)

    # Toutes les pages métier nécessitent une session authentifiée.
    @app.before_request
    def proteger_application():
        if app.config.get("AUTH_DISABLED", False):
            return None
        if request.endpoint is None or request.endpoint == "static":
            return None
        if request.endpoint in {"auth.login"}:
            return None
        if not current_user.is_authenticated:
            from flask import redirect, url_for
            return redirect(url_for("auth.login", next=request.url))

        # Consultation peut uniquement lire les pages (GET/HEAD/OPTIONS).
        if current_user.role == "consultation" and request.method not in {"GET", "HEAD", "OPTIONS"}:
            abort(403)

        # Les paramètres et la gestion des comptes sont réservés à l'Admin.
        endpoint = request.endpoint or ""
        if (
            endpoint.startswith("parametres.")
            or endpoint.startswith("auth.utilisateurs")
            or endpoint.startswith("auth.basculer_statut_utilisateur")
        ):
            if current_user.role != "admin":
                abort(403)

    @app.cli.command("init-auth-db")
    def init_auth_db_command():
        """Créer les tables manquantes, notamment la table users, sans supprimer les données."""
        import click
        db.create_all()
        click.echo("Tables manquantes créées. Les tables et données existantes sont conservées.")

    @app.cli.command("create-admin")
    def create_admin_command():
        """Créer le premier compte administrateur de l'application."""
        import click
        from getpass import getpass

        if User.query.filter_by(role="admin", actif=True).first():
            click.echo("Un compte administrateur actif existe déjà.")
            return

        username = click.prompt("Nom d'utilisateur")
        nom_complet = click.prompt("Nom complet")
        password = getpass(
            f"Mot de passe ({User.MIN_PASSWORD_LENGTH} caractères min, "
            "majuscule, minuscule, chiffre): "
        )
        confirmation = getpass("Confirmer le mot de passe: ")
        if password != confirmation:
            click.echo("Confirmation différente.")
            return
        ok, msg = User.valider_mot_de_passe(password)
        if not ok:
            click.echo(msg)
            return
        user = User(username=username.strip(), nom_complet=nom_complet.strip(), role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Compte administrateur créé avec succès.")

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app
