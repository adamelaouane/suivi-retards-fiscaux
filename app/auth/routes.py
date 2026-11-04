from datetime import datetime
from urllib.parse import urljoin, urlparse

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _safe_next_url(target):
    if not target:
        return False
    ref = urlparse(urljoin(request.host_url, target))
    return ref.scheme in ("http", "https") and ref.netloc == request.host


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("accueil.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.actif and user.check_password(password):
            login_user(user)
            user.derniere_connexion = datetime.utcnow()
            db.session.commit()
            flash("Connexion réussie.", "success")
            target = request.args.get("next")
            return redirect(target if _safe_next_url(target) else url_for("accueil.index"))

        flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")

    return render_template("auth/login.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/utilisateurs", methods=["GET", "POST"])
@login_required
def utilisateurs():
    if current_user.role != "admin":
        abort(403)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        nom_complet = request.form.get("nom_complet", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "consultation")

        if not username or not nom_complet:
            flash("Le nom d'utilisateur et le nom complet sont obligatoires.", "danger")
        elif len(password) < 12:
            flash("Le mot de passe doit contenir au moins 12 caractères.", "danger")
        elif role not in User.ROLES:
            flash("Rôle invalide.", "danger")
        else:
            user = User(username=username, nom_complet=nom_complet, role=role)
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
                flash("Utilisateur créé avec succès.", "success")
                return redirect(url_for("auth.utilisateurs"))
            except IntegrityError:
                db.session.rollback()
                flash("Ce nom d'utilisateur existe déjà.", "danger")

    users = User.query.order_by(User.username.asc()).all()
    return render_template("auth/utilisateurs.html", users=users)


@auth_bp.post("/utilisateurs/<int:user_id>/basculer-statut")
@login_required
def basculer_statut_utilisateur(user_id):
    if current_user.role != "admin":
        abort(403)

    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Vous ne pouvez pas désactiver votre propre compte.", "warning")
    else:
        user.actif = not user.actif
        db.session.commit()
        flash("Statut du compte mis à jour.", "success")
    return redirect(url_for("auth.utilisateurs"))
