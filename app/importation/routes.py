
import os

from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
)

from app.importation.services import importer_dossiers


importation_bp = Blueprint(
    "importation",
    __name__,
    url_prefix="/importation",
)


@importation_bp.route("/", methods=["GET", "POST"])
def index():

    resultat = None

    if request.method == "POST":

        fichier = request.files.get("fichier")

        if not fichier or fichier.filename == "":
            flash("Veuillez sélectionner un fichier.", "error")
            return redirect(url_for("importation.index"))

        extension = os.path.splitext(fichier.filename)[1].lower()

        if extension not in [".csv", ".xlsx"]:
            flash("Format non accepté. Utilisez CSV ou Excel.", "error")
            return redirect(url_for("importation.index"))

        try:
            resultat = importer_dossiers(
                fichier,
                fichier.filename,
            )

            nb_ok = resultat["nombre_importes"]
            nb_err = resultat["nombre_erreurs"]

            if nb_ok > 0 and nb_err == 0:
                flash(
                    f"Importation réussie : {nb_ok} dossier(s) importé(s).",
                    "success",
                )
            elif nb_ok > 0 and nb_err > 0:
                flash(
                    f"Importation partielle : {nb_ok} dossier(s) importé(s), "
                    f"{nb_err} ligne(s) ignorée(s) — voir le détail ci-dessous.",
                    "warning",
                )
            else:
                flash(
                    f"Aucun dossier importé. {nb_err} erreur(s) — voir le détail ci-dessous.",
                    "error",
                )

        except Exception as erreur:
            flash(f"Erreur critique : {str(erreur)}", "error")

    return render_template(
        "importation/index.html",
        resultat=resultat,
    )
