from flask import Blueprint, render_template, request
from app.recherche.services import filtrer_recherche

recherche_bp = Blueprint(
    "recherche",
    __name__,
    url_prefix="/recherche",
)


@recherche_bp.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "").strip()
    identifiant = request.args.get("identifiant", "").strip()
    type_taxe_id = request.args.get("type_taxe_id", "").strip()
    annee = request.args.get("annee", "").strip()
    statut = request.args.get("statut", "").strip()
    retard = request.args.get("retard", "").strip()
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

    resultat = filtrer_recherche(
        query=query,
        identifiant=identifiant,
        type_taxe_id=type_taxe_id,
        annee=annee,
        statut=statut,
        retard=retard,
        page=page,
    )

    return render_template(
        "recherche/index.html",
        dossiers=resultat["dossiers"],
        types_taxes=resultat["types_taxes"],
        annees=resultat["annees"],
        query=query,
        identifiant=identifiant,
        type_taxe_id=type_taxe_id,
        annee=annee,
        statut=statut,
        retard=retard,
        pagination=resultat["pagination"],
    )
