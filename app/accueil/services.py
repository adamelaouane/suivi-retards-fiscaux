from decimal import Decimal

from sqlalchemy.orm import selectinload, joinedload

from app.models import DossierFiscal, Paiement


def get_dashboard_stats():
    """Indicateurs du tableau de bord, calculés depuis la base."""
    dossiers = (
        DossierFiscal.query
        .options(selectinload(DossierFiscal.paiements))
        .all()
    )

    stats = {
        "total_dossiers": len(dossiers),
        "dossiers_impayes": 0,
        "dossiers_partiels": 0,
        "dossiers_payes": 0,
        "en_retard": 0,
        "montant_restant": Decimal("0.00"),
    }

    for dossier in dossiers:
        stats["montant_restant"] += dossier.montant_restant
        if dossier.statut == "PAYE":
            stats["dossiers_payes"] += 1
        elif dossier.statut == "PARTIELLEMENT_PAYE":
            stats["dossiers_partiels"] += 1
        else:
            stats["dossiers_impayes"] += 1
        if dossier.jours_retard > 0:
            stats["en_retard"] += 1

    return stats


def get_recent_activities(limit=10):
    """Derniers paiements enregistrés (en attendant le journal d'audit)."""
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 100))

    paiements = (
        Paiement.query
        .options(joinedload(Paiement.dossier))
        .order_by(Paiement.date_enregistrement.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "date": p.date_enregistrement.strftime("%d/%m/%Y %H:%M"),
            "operation": "Paiement enregistré",
            "reference": p.dossier.numero_dossier,
            "statut": "Enregistré",
        }
        for p in paiements
    ]
