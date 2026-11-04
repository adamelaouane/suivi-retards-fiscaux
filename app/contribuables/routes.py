from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from app.extensions import db
from app.contribuables.services import (
    ContribuableInvalide,
    creer_contribuable,
    get_situation_financiere,
    lister_contribuables,
    modifier_contribuable,
)
from app.models.contribuable import Contribuable

contribuables_bp = Blueprint(
    "contribuables",
    __name__,
    url_prefix="/contribuables",
)


@contribuables_bp.route("/", methods=["GET"])
def index():
    recherche = request.args.get("q", "").strip()
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

    pagination = lister_contribuables(recherche=recherche, page=page)
    return render_template(
        "contribuables/index.html",
        pagination=pagination,
        recherche=recherche,
    )


@contribuables_bp.route("/nouveau", methods=["GET", "POST"])
def nouveau():
    if request.method == "POST":
        identifiant = request.form.get("identifiant_fiscal")
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        cin = request.form.get("cin")
        telephone = request.form.get("telephone")

        try:
            contribuable = creer_contribuable(
                identifiant_fiscal=identifiant,
                nom=nom,
                prenom=prenom,
                cin=cin,
                telephone=telephone,
            )
            flash(f"Contribuable {contribuable.nom_complet} créé avec succès.", "success")
            return redirect(url_for("contribuables.detail", contribuable_id=contribuable.id))
        except ContribuableInvalide as e:
            flash(str(e), "danger")

    return render_template("contribuables/form.html", contribuable=None)


@contribuables_bp.route("/<int:contribuable_id>", methods=["GET"])
def detail(contribuable_id):
    contribuable = db.session.get(Contribuable, contribuable_id)
    if contribuable is None:
       abort(404) 
    situation = get_situation_financiere(contribuable)
    return render_template(
        "contribuables/detail.html",
        contribuable=contribuable,
        situation=situation,
    )


@contribuables_bp.route("/<int:contribuable_id>/modifier", methods=["GET", "POST"])
def modifier(contribuable_id):
    contribuable = db.session.get(Contribuable, contribuable_id)
    if contribuable is None:
        abort(404)
    if request.method == "POST":
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        cin = request.form.get("cin")
        telephone = request.form.get("telephone")

        try:
            modifier_contribuable(
                contribuable=contribuable,
                nom=nom,
                prenom=prenom,
                cin=cin,
                telephone=telephone,
            )
            flash("Informations du contribuable mises à jour.", "success")
            return redirect(url_for("contribuables.detail", contribuable_id=contribuable.id))
        except ContribuableInvalide as e:
            flash(str(e), "danger")

    return render_template("contribuables/form.html", contribuable=contribuable)
