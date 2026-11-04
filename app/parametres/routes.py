from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.parametre import Parametre
from app.services.audit import enregistrer_audit

parametres_bp = Blueprint("parametres", __name__, url_prefix="/parametres")


def _entier_formulaire(nom, minimum, maximum, libelle):
    valeur = request.form.get(nom, "").strip()
    try:
        nombre = int(valeur)
    except (TypeError, ValueError):
        raise ValueError(f"{libelle} doit être un nombre entier.")
    if not minimum <= nombre <= maximum:
        raise ValueError(f"{libelle} doit être compris entre {minimum} et {maximum}.")
    return nombre


@parametres_bp.route("/", methods=["GET", "POST"])
def index():
    # Initialisation idempotente; la transaction est validée explicitement ici.
    try:
        Parametre.initialiser_defauts()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    if request.method == "POST":
        try:
            seuil_significatif = _entier_formulaire(
                "seuil_retard_significatif", 1, 365, "Le seuil significatif"
            )
            seuil_critique = _entier_formulaire(
                "seuil_retard_critique", 1, 1000, "Le seuil critique"
            )
            lignes_par_page = _entier_formulaire(
                "lignes_par_page", 5, 100, "Le nombre de lignes par page"
            )
            nom_organisme = request.form.get("nom_organisme", "").strip()

            if seuil_critique <= seuil_significatif:
                raise ValueError(
                    "Le seuil critique doit être supérieur au seuil significatif."
                )
            if not nom_organisme:
                raise ValueError("Le nom de l'organisme est obligatoire.")
            if len(nom_organisme) > 120:
                raise ValueError("Le nom de l'organisme ne doit pas dépasser 120 caractères.")

            Parametre.set_valeur(
                "seuil_retard_significatif", seuil_significatif, type_valeur="int"
            )
            Parametre.set_valeur(
                "seuil_retard_critique", seuil_critique, type_valeur="int"
            )
            Parametre.set_valeur(
                "lignes_par_page", lignes_par_page, type_valeur="int"
            )
            Parametre.set_valeur(
                "nom_organisme", nom_organisme, type_valeur="str"
            )
            enregistrer_audit(
                action="MODIFICATION",
                objet="Parametre",
                reference="Configuration",
                description="Mise à jour des paramètres système (seuils et pagination)",
            )
            db.session.commit()
            flash("Paramètres enregistrés avec succès.", "success")
        except ValueError as erreur:
            db.session.rollback()
            flash(str(erreur), "danger")
        except Exception:
            db.session.rollback()
            flash("Une erreur interne est survenue lors de la sauvegarde.", "danger")

        return redirect(url_for("parametres.index"))

    parametres = Parametre.query.order_by(Parametre.cle.asc()).all()
    recent_audits = AuditLog.query.order_by(AuditLog.date_action.desc()).limit(30).all()
    return render_template(
        "parametres/index.html",
        parametres=parametres,
        recent_audits=recent_audits,
    )
