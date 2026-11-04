from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Contribuable, DossierFiscal, TypeTaxe
from app.models.parametre import Parametre


def _pagination_value(value, default=20, maximum=200):
    """Normalise les paramètres de pagination pour éviter division par zéro."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = default
    return max(1, min(value, maximum))


def _page_value(value):
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return 1


def filtrer_recherche(query="", identifiant="", type_taxe_id="", annee="", statut="", retard="", page=1, par_page=None):
    """Recherche multicritère de dossiers, avec chargement groupé des relations."""
    if par_page is None:
        par_page = Parametre.get_valeur("lignes_par_page", 20)
    par_page = _pagination_value(par_page)
    page = _page_value(page)

    dossiers_query = (
        DossierFiscal.query
        .options(
            selectinload(DossierFiscal.paiements),
            selectinload(DossierFiscal.contribuable),
            selectinload(DossierFiscal.type_taxe),
        )
        .join(DossierFiscal.contribuable)
        .join(DossierFiscal.type_taxe)
    )

    if query:
        recherche_str = f"%{query.strip()}%"
        dossiers_query = dossiers_query.filter(
            or_(
                DossierFiscal.numero_dossier.ilike(recherche_str),
                Contribuable.nom.ilike(recherche_str),
                Contribuable.prenom.ilike(recherche_str),
                Contribuable.identifiant_fiscal.ilike(recherche_str),
            )
        )

    if identifiant:
        dossiers_query = dossiers_query.filter(
            Contribuable.identifiant_fiscal.ilike(f"%{identifiant.strip()}%")
        )

    if type_taxe_id:
        try:
            dossiers_query = dossiers_query.filter(DossierFiscal.type_taxe_id == int(type_taxe_id))
        except (TypeError, ValueError):
            pass

    if annee:
        try:
            dossiers_query = dossiers_query.filter(DossierFiscal.annee_fiscale == int(annee))
        except (TypeError, ValueError):
            pass

    dossiers = dossiers_query.order_by(DossierFiscal.date_limite.asc()).all()

    # Ces deux critères dépendent des paiements et de la date du jour.
    if statut in ("IMPAYE", "PARTIELLEMENT_PAYE", "PAYE"):
        dossiers = [d for d in dossiers if d.statut == statut]

    if retard == "en_retard":
        dossiers = [d for d in dossiers if d.montant_restant > 0 and d.jours_retard > 0]
    elif retard == "sans_retard":
        dossiers = [d for d in dossiers if d.montant_restant > 0 and d.jours_retard == 0]

    types_taxes = TypeTaxe.query.order_by(TypeTaxe.libelle.asc()).all()
    annees = [row[0] for row in db.session.query(DossierFiscal.annee_fiscale).distinct().order_by(DossierFiscal.annee_fiscale.desc()).all()]

    total = len(dossiers)
    total_pages = max(1, (total + par_page - 1) // par_page)
    page = min(page, total_pages)
    debut = (page - 1) * par_page

    return {
        "dossiers": dossiers[debut:debut + par_page],
        "total_dossiers": dossiers,
        "types_taxes": types_taxes,
        "annees": annees,
        "pagination": {
            "page": page,
            "par_page": par_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "prev_page": page - 1,
            "next_page": page + 1,
        },
    }
