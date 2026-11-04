from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.models import DossierFiscal
from app.models.parametre import Parametre


def _pagination_value(value, default=20, maximum=200):
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


def filtrer_dossiers_impayes(query=None, page=1, par_page=None):
    """Retourne les dossiers avec un reste à payer, avec relations préchargées."""
    if par_page is None:
        par_page = Parametre.get_valeur("lignes_par_page", 20)
    par_page = _pagination_value(par_page)
    page = _page_value(page)

    dossiers_raw = (
        DossierFiscal.query
        .options(
            selectinload(DossierFiscal.paiements),
            selectinload(DossierFiscal.contribuable),
            selectinload(DossierFiscal.type_taxe),
        )
        .join(DossierFiscal.contribuable)
        .join(DossierFiscal.type_taxe)
        .order_by(DossierFiscal.date_limite.asc())
        .all()
    )

    if query:
        q_lower = query.strip().casefold()
        dossiers_raw = [
            d for d in dossiers_raw
            if q_lower in (d.numero_dossier or "").casefold()
            or q_lower in (d.contribuable.nom_complet or "").casefold()
            or q_lower in (d.contribuable.identifiant_fiscal or "").casefold()
        ]

    dossiers = [d for d in dossiers_raw if d.montant_restant > Decimal("0.00")]
    stats = {
        "nombre": len(dossiers),
        "montant_restant": sum((d.montant_restant for d in dossiers), Decimal("0.00")),
        "en_retard": sum(1 for d in dossiers if d.jours_retard > 0),
    }

    total = len(dossiers)
    total_pages = max(1, (total + par_page - 1) // par_page)
    page = min(page, total_pages)
    debut = (page - 1) * par_page

    return {
        "dossiers": dossiers[debut:debut + par_page],
        "total_dossiers": dossiers,
        "stats": stats,
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
