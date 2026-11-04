"""Services du module Rapports, exploitant export_excel et export_pdf."""

from io import BytesIO
from app.models.dossier_fiscal import DossierFiscal
from app.services.export_excel import exporter_dossiers_excel
from app.services.export_pdf import exporter_dossiers_pdf


def obtenir_dossiers(filtre=None):
    """Récupère les dossiers fiscaux avec leurs contribuables et taxes."""
    query = (
        DossierFiscal.query
        .join(DossierFiscal.contribuable)
        .join(DossierFiscal.type_taxe)
        .order_by(DossierFiscal.date_limite.asc())
    )
    dossiers = query.all()
    if filtre == "impayes":
        return [d for d in dossiers if d.montant_restant > 0]
    elif filtre == "retard":
        return [d for d in dossiers if d.en_retard]
    return dossiers


def generer_excel(filtre=None):
    """Génère un fichier Excel contenant les dossiers fiscaux."""
    dossiers = obtenir_dossiers(filtre)
    titre = "RAPPORT DES DOSSIERS FISCAUX"
    if filtre == "impayes":
        titre = "RAPPORT DES DOSSIERS IMPAYÉS"
    elif filtre == "retard":
        titre = "RAPPORT DES DOSSIERS EN RETARD"
    return exporter_dossiers_excel(dossiers, titre=titre)


def generer_pdf(filtre=None):
    """Génère un rapport PDF des dossiers fiscaux."""
    dossiers = obtenir_dossiers(filtre)
    titre = "Rapport des dossiers fiscaux"
    if filtre == "impayes":
        titre = "Rapport des dossiers impayés"
    elif filtre == "retard":
        titre = "Rapport des dossiers en retard"
    return exporter_dossiers_pdf(dossiers, titre=titre)
