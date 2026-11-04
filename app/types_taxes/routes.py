
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models.type_taxe import TypeTaxe
from app.types_taxes.services import (
    TypeTaxeInvalide,
    basculer_statut_type_taxe,
    creer_type_taxe,
    lister_types_taxes,
    modifier_type_taxe,
)

types_taxes_bp = Blueprint(
    "types_taxes",
    __name__,
    url_prefix="/types-taxes",
)


@types_taxes_bp.route("/", methods=["GET"])
def index():
    types_taxes = lister_types_taxes(inclure_inactifs=True)
    return render_template("types_taxes/index.html", types_taxes=types_taxes)


@types_taxes_bp.route("/nouveau", methods=["GET", "POST"])
def nouveau():
    if request.method == "POST":
        code = request.form.get("code")
        libelle = request.form.get("libelle")
        description = request.form.get("description")

        try:
            type_taxe = creer_type_taxe(
                code=code,
                libelle=libelle,
                description=description,
            )
            flash(
                f"Type de taxe '{type_taxe.libelle}' créé avec succès.",
                "success",
            )
            return redirect(url_for("types_taxes.index"))

        except TypeTaxeInvalide as e:
            flash(str(e), "danger")

    return render_template("types_taxes/form.html", type_taxe=None)


@types_taxes_bp.route("/<int:taxe_id>/modifier", methods=["GET", "POST"])
def modifier(taxe_id):
    type_taxe = db.session.get(TypeTaxe, taxe_id)

    if type_taxe is None:
        abort(404)

    if request.method == "POST":
        libelle = request.form.get("libelle")
        description = request.form.get("description")

        try:
            modifier_type_taxe(
                type_taxe=type_taxe,
                libelle=libelle,
                description=description,
            )
            flash("Type de taxe modifié avec succès.", "success")
            return redirect(url_for("types_taxes.index"))

        except TypeTaxeInvalide as e:
            flash(str(e), "danger")

    return render_template("types_taxes/form.html", type_taxe=type_taxe)


@types_taxes_bp.route("/<int:taxe_id>/basculer-statut", methods=["POST"])
def basculer_statut(taxe_id):
    type_taxe = db.session.get(TypeTaxe, taxe_id)

    if type_taxe is None:
        abort(404)

    try:
        basculer_statut_type_taxe(type_taxe)
        etat = "activé" if type_taxe.actif else "désactivé"
        flash(f"Type de taxe '{type_taxe.code}' {etat}.", "info")

    except Exception as e:
        flash(f"Erreur : {e}", "danger")

    return redirect(url_for("types_taxes.index"))
