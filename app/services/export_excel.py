"""Service d'exportation Excel via OpenPyXL."""

from datetime import datetime
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.models.parametre import Parametre


def securiser_texte_excel(valeur):
    """Empêche l'interprétation d'un texte utilisateur comme formule Excel."""
    if not isinstance(valeur, str):
        return valeur
    texte = valeur
    debut = texte.lstrip(" \t\r\n\x00")
    if debut.startswith(("=", "+", "-", "@")):
        return "'" + texte
    return texte


def exporter_dossiers_excel(dossiers, titre="RAPPORT DES DOSSIERS FISCAUX"):
    """Génère un classeur Excel pour une liste de dossiers fiscaux."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Dossiers"

    nom_orga = Parametre.get_valeur(
        "nom_organisme", "Direction Générale des Impôts"
    )
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    ws.append([securiser_texte_excel(
        f"{str(nom_orga).upper()} - {titre} (Données synthétiques de démonstration)"
    )])
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=11)
    ws["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor="1E3A8A")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

    ws.append([f"Généré le : {date_str} - Total dossiers : {len(dossiers)}"])
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=11)
    ws["A2"].font = Font(italic=True, size=10, color="475569")
    ws["A2"].alignment = Alignment(horizontal="left", vertical="center")

    entetes = [
        "Référence", "Contribuable", "Identifiant Fiscal", "Taxe", "Année",
        "Montant Exigible (DH)", "Montant Payé (DH)", "Montant Restant (DH)",
        "Échéance", "Jours Retard", "Statut",
    ]
    ws.append(entetes)
    for cell in ws[3]:
        cell.font = Font(bold=True, color="FFFFFF", size=10)
        cell.fill = PatternFill("solid", fgColor="3B82F6")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    statut_labels = {
        "PAYE": "Payé",
        "PARTIELLEMENT_PAYE": "Partiellement payé",
        "IMPAYE": "Impayé",
    }

    for dossier in dossiers:
        valeurs = [
            dossier.numero_dossier,
            dossier.contribuable.nom_complet,
            dossier.contribuable.identifiant_fiscal or "",
            dossier.type_taxe.libelle,
            dossier.annee_fiscale,
            float(dossier.montant_exigible),
            float(dossier.montant_paye),
            float(dossier.montant_restant),
            dossier.date_limite.strftime("%d/%m/%Y"),
            dossier.jours_retard,
            statut_labels.get(dossier.statut, dossier.statut),
        ]
        ws.append([securiser_texte_excel(v) for v in valeurs])

    for row in ws.iter_rows(min_row=4, min_col=6, max_col=8):
        for cell in row:
            cell.number_format = '#,##0.00 "DH"'

    largeurs = [20, 26, 20, 20, 12, 22, 20, 22, 16, 16, 22]
    for index, largeur in enumerate(largeurs, start=1):
        ws.column_dimensions[get_column_letter(index)].width = largeur

    ws.freeze_panes = "A4"
    if ws.max_row >= 3:
        ws.auto_filter.ref = f"A3:K{ws.max_row}"

    sortie = BytesIO()
    wb.save(sortie)
    sortie.seek(0)
    return sortie
