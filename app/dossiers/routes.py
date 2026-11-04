from datetime import date
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from app.extensions import db
from app.dossiers.services import DossierInvalide, creer_dossier, modifier_dossier
from app.models.contribuable import Contribuable
from app.models.dossier_fiscal import DossierFiscal
from app.models.type_taxe import TypeTaxe

dossiers_bp = Blueprint(
    "dossiers",
    __name__,
    url_prefix="/dossiers",
)


@dossiers_bp.route("/")
def index():
    return redirect(url_for("recherche.index"))


@dossiers_bp.route("/nouveau", methods=["GET", "POST"])
def nouveau():
    contribuable_id_param = request.args.get("contribuable_id", type=int)

    if request.method == "POST":
        numero_dossier = request.form.get("numero_dossier")
        contribuable_id = request.form.get("contribuable_id")
        type_taxe_id = request.form.get("type_taxe_id")
        annee_fiscale = request.form.get("annee_fiscale")
        date_limite = request.form.get("date_limite")
        montant_exigible = request.form.get("montant_exigible")
        observations = request.form.get("observations")

        try:
            dossier = creer_dossier(
                numero_dossier=numero_dossier,
                contribuable_id=contribuable_id,
                type_taxe_id=type_taxe_id,
                annee_fiscale=annee_fiscale,
                date_limite=date_limite,
                montant_exigible=montant_exigible,
                observations=observations,
            )
            flash(f"Dossier fiscal {dossier.numero_dossier} créé avec succès.", "success")
            return redirect(url_for("dossiers.detail", dossier_id=dossier.id))
        except DossierInvalide as e:
            flash(str(e), "danger")

    contribuables = Contribuable.query.order_by(Contribuable.nom.asc()).all()
    types_taxes = TypeTaxe.query.filter_by(actif=True).order_by(TypeTaxe.libelle.asc()).all()
    annee_courante = date.today().year

    return render_template(
        "dossiers/form.html",
        dossier=None,
        contribuables=contribuables,
        types_taxes=types_taxes,
        contribuable_selectionne=contribuable_id_param,
        annee_courante=annee_courante,
    )


@dossiers_bp.route("/<int:dossier_id>", methods=["GET"])
def detail(dossier_id):
    dossier = db.session.get(DossierFiscal, dossier_id)

    if dossier is None:
        abort(404)
    return render_template("dossiers/detail.html", dossier=dossier)


@dossiers_bp.route("/<int:dossier_id>/modifier", methods=["GET", "POST"])
def modifier(dossier_id):
    dossier = db.session.get(DossierFiscal, dossier_id)

    if dossier is None:
        abort(404)

    if request.method == "POST":
        date_limite = request.form.get("date_limite")
        observations = request.form.get("observations")

        try:
            modifier_dossier(
                dossier=dossier,
                date_limite=date_limite,
                observations=observations,
            )
            flash("Dossier fiscal mis à jour.", "success")
            return redirect(url_for("dossiers.detail", dossier_id=dossier.id))
        except DossierInvalide as e:
            flash(str(e), "danger")

    return render_template("dossiers/form.html", dossier=dossier)
