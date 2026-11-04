"""Service d'exportation PDF via ReportLab."""

from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from app.models.parametre import Parametre


def exporter_dossiers_pdf(dossiers, titre="Rapport des Dossiers Fiscaux"):
    """Génère un document PDF au format paysage pour une liste de dossiers."""
    sortie = BytesIO()
    doc = SimpleDocTemplate(
        sortie,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    nom_orga = Parametre.get_valeur("nom_organisme", "Direction Générale des Impôts")
    date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")

    styles = getSampleStyleSheet()

    titre_style = ParagraphStyle(
        "TitreRapport",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1e3a8a"),
        fontSize=15,
        leading=18,
        spaceAfter=4,
    )

    sous_titre_style = ParagraphStyle(
        "SousTitreRapport",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#64748b"),
        fontSize=9,
        spaceAfter=12,
    )

    cell_style = ParagraphStyle(
        "CellNormal",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )

    cell_header = ParagraphStyle(
        "CellHeader",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )

    elements = [
        Paragraph(f"{nom_orga} — {titre}", titre_style),
        Paragraph(f"Document de démonstration généré le {date_str} — {len(dossiers)} dossier(s) listé(s)", sous_titre_style),
    ]

    entetes = [
        Paragraph("N° Dossier", cell_header),
        Paragraph("Contribuable", cell_header),
        Paragraph("Taxe", cell_header),
        Paragraph("Année", cell_header),
        Paragraph("Montant Dû", cell_header),
        Paragraph("Payé", cell_header),
        Paragraph("Restant", cell_header),
        Paragraph("Échéance", cell_header),
        Paragraph("Retard", cell_header),
        Paragraph("Statut", cell_header),
    ]

    lignes = [entetes]

    statut_labels = {
        "PAYE": "Payé",
        "PARTIELLEMENT_PAYE": "Partiel",
        "IMPAYE": "Impayé",
    }

    for d in dossiers:
        lignes.append([
            Paragraph(d.numero_dossier, cell_style),
            Paragraph(f"{d.contribuable.nom_complet}<br/><font color='#64748b'>{d.contribuable.identifiant_fiscal or ''}</font>", cell_style),
            Paragraph(d.type_taxe.libelle, cell_style),
            Paragraph(str(d.annee_fiscale), cell_style),
            Paragraph(f"{d.montant_exigible} DH", cell_style),
            Paragraph(f"{d.montant_paye} DH", cell_style),
            Paragraph(f"<b>{d.montant_restant} DH</b>", cell_style),
            Paragraph(d.date_limite.strftime("%d/%m/%Y"), cell_style),
            Paragraph(f"{d.jours_retard} j" if d.en_retard else "À jour", cell_style),
            Paragraph(statut_labels.get(d.statut, d.statut), cell_style),
        ])

    tableau = Table(
        lignes,
        colWidths=[28 * mm, 50 * mm, 38 * mm, 16 * mm, 28 * mm, 26 * mm, 28 * mm, 24 * mm, 18 * mm, 21 * mm],
        repeatRows=1,
    )

    tableau.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))

    elements.append(tableau)
    doc.build(elements)
    sortie.seek(0)
    return sortie
