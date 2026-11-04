from flask import Blueprint, render_template, request, send_file
from app.rapports.services import generer_excel, generer_pdf

rapports_bp = Blueprint(
    "rapports",
    __name__,
    url_prefix="/rapports",
)


@rapports_bp.route("/")
def index():
    return render_template("rapports/index.html")


@rapports_bp.route("/export/excel")
def exporter_excel():
    filtre = request.args.get("filtre")
    fichier = generer_excel(filtre=filtre)
    nom_fichier = f"rapport_dossiers_{filtre or 'complet'}.xlsx"

    return send_file(
        fichier,
        as_attachment=True,
        download_name=nom_fichier,
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )


@rapports_bp.route("/export/pdf")
def exporter_pdf():
    filtre = request.args.get("filtre")
    fichier = generer_pdf(filtre=filtre)
    nom_fichier = f"rapport_dossiers_{filtre or 'complet'}.pdf"

    return send_file(
        fichier,
        as_attachment=True,
        download_name=nom_fichier,
        mimetype="application/pdf",
    )
