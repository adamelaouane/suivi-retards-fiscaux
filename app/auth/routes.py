from datetime import datetime
from urllib.parse import urljoin, urlparse

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User
from app.auth.decorators import admin_required


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

        if user is None:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
            return render_template("auth/login.html")

        if not user.actif:
            flash("Ce compte est désactivé. Contactez un administrateur.", "danger")
            return render_template("auth/login.html")

        if user.est_verrouille():
            flash(
                "Compte temporairement verrouillé après trop de tentatives. "
                "Réessayez dans quelques minutes.",
                "danger",
            )
            return render_template("auth/login.html")

        if user.check_password(password):
            user.reinitialiser_echecs()
            user.derniere_connexion = datetime.utcnow()
            db.session.commit()
            login_user(user)
            flash("Connexion réussie.", "success")
            target = request.args.get("next")
            return redirect(target if _safe_next_url(target) else url_for("accueil.index"))

        user.enregistrer_echec_connexion()
        db.session.commit()
        flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")

    return render_template("auth/login.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/utilisateurs", methods=["GET", "POST"])
@admin_required
def utilisateurs():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        nom_complet = request.form.get("nom_complet", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "consultation")

        if not username or not nom_complet:
            flash("Le nom d'utilisateur et le nom complet sont obligatoires.", "danger")
        elif role not in User.ROLES:
            flash("Rôle invalide.", "danger")
        else:
            ok, msg = User.valider_mot_de_passe(password)
            if not ok:
                flash(msg, "danger")
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
@admin_required
def basculer_statut_utilisateur(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Vous ne pouvez pas désactiver votre propre compte.", "warning")
    else:
        user.actif = not user.actif
        db.session.commit()
        flash("Statut du compte mis à jour.", "success")
    return redirect(url_for("auth.utilisateurs"))
