from collections import defaultdict
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.models.dossier_fiscal import DossierFiscal
from app.models.paiement import Paiement
from app.models.type_taxe import TypeTaxe
from app.models.parametre import Parametre


def _seuils_retard():
    """Garantit des seuils cohérents même si les paramètres sont mal saisis."""
    try:
        significatif = max(1, int(Parametre.get_valeur("seuil_retard_significatif", 30)))
    except (TypeError, ValueError):
        significatif = 30
    try:
        critique = max(significatif + 1, int(Parametre.get_valeur("seuil_retard_critique", 90)))
    except (TypeError, ValueError):
        critique = max(significatif + 1, 90)
    return significatif, critique


def obtenir_statistiques():
    """Calcule les indicateurs financiers sans requête par dossier pour les paiements."""
    dossiers = (
        DossierFiscal.query
        .options(selectinload(DossierFiscal.paiements))
        .all()
    )

    nombre_dossiers = len(dossiers)
    nombre_payes = sum(1 for d in dossiers if d.statut == "PAYE")
    nombre_impayes = sum(1 for d in dossiers if d.statut == "IMPAYE")
    nombre_partiels = sum(1 for d in dossiers if d.statut == "PARTIELLEMENT_PAYE")

    montant_exigible = sum((Decimal(str(d.montant_exigible)) for d in dossiers), Decimal("0.00"))
    montant_paye = sum((d.montant_paye for d in dossiers), Decimal("0.00"))
    montant_restant = sum((d.montant_restant for d in dossiers), Decimal("0.00"))
    nombre_en_retard = sum(1 for d in dossiers if d.montant_restant > 0 and d.jours_retard > 0)

    taux_recouvrement = float(montant_paye / montant_exigible * 100) if montant_exigible > 0 else 0.0

    seuil_significatif, seuil_critique = _seuils_retard()
    tranches_retard = {
        "a_jour": {"label": "Non échu / À jour", "count": 0, "montant": Decimal("0.00")},
        "modere": {"label": f"1 à {seuil_significatif} jours", "count": 0, "montant": Decimal("0.00")},
        "significatif": {"label": f"{seuil_significatif + 1} à {seuil_critique} jours", "count": 0, "montant": Decimal("0.00")},
        "critique": {"label": f"+ de {seuil_critique} jours (critique)", "count": 0, "montant": Decimal("0.00")},
    }

    dossiers_par_taxe = defaultdict(list)
    for dossier in dossiers:
        dossiers_par_taxe[dossier.type_taxe_id].append(dossier)
        if dossier.montant_restant <= 0:
            continue
        jours = dossier.jours_retard
        if jours == 0:
            tranche = "a_jour"
        elif jours <= seuil_significatif:
            tranche = "modere"
        elif jours <= seuil_critique:
            tranche = "significatif"
        else:
            tranche = "critique"
        tranches_retard[tranche]["count"] += 1
        tranches_retard[tranche]["montant"] += dossier.montant_restant

    stats_par_taxe = []
    for taxe in TypeTaxe.query.order_by(TypeTaxe.libelle.asc()).all():
        taxe_dossiers = dossiers_par_taxe.get(taxe.id, [])
        if not taxe_dossiers:
            continue
        exigible = sum((Decimal(str(d.montant_exigible)) for d in taxe_dossiers), Decimal("0.00"))
        paye = sum((d.montant_paye for d in taxe_dossiers), Decimal("0.00"))
        restant = sum((d.montant_restant for d in taxe_dossiers), Decimal("0.00"))
        en_retard = sum(1 for d in taxe_dossiers if d.en_retard)
        taux = float(paye / exigible * 100) if exigible > 0 else 0.0
        stats_par_taxe.append({
            "taxe": taxe,
            "total_dossiers": len(taxe_dossiers),
            "montant_exigible": exigible,
            "montant_paye": paye,
            "montant_restant": restant,
            "nb_retard": en_retard,
            "taux_recouvrement": taux,
        })

    paiements_valides = (
        Paiement.query
        .filter_by(statut="VALIDE")
        .order_by(Paiement.date_paiement.desc())
        .limit(10)
        .all()
    )

    return {
        "nombre_dossiers": nombre_dossiers,
        "nombre_payes": nombre_payes,
        "nombre_impayes": nombre_impayes,
        "nombre_partiels": nombre_partiels,
        "nombre_en_retard": nombre_en_retard,
        "montant_exigible": montant_exigible,
        "montant_paye": montant_paye,
        "montant_restant": montant_restant,
        "taux_recouvrement": taux_recouvrement,
        "tranches_retard": tranches_retard,
        "stats_par_taxe": stats_par_taxe,
        "paiements_recents": paiements_valides,
    }
