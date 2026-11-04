
from flask import Blueprint, abort, flash, redirect, request, url_for

from app.extensions import db
from app.models.dossier_fiscal import DossierFiscal
from app.relances.services import RelanceInvalide, enregistrer_relance

relances_bp = Blueprint(
    "relances",
    __name__,
    url_prefix="/relances",
)


@relances_bp.route("/enregistrer", methods=["POST"])
def enregistrer():
    dossier_id = request.form.get("dossier_id", type=int)

    dossier = db.session.get(DossierFiscal, dossier_id)

    if dossier is None:
        abort(404)

    canal = request.form.get("canal")
    message = request.form.get("message")
    statut = request.form.get("statut")

    try:
        relance = enregistrer_relance(
            dossier=dossier,
            canal=canal,
            message=message,
            statut=statut,
        )
        flash(
            f"Action de relance consignée avec succès (Canal: {relance.canal}).",
            "success",
        )

    except RelanceInvalide as e:
        flash(str(e), "danger")

    except Exception as e:
        flash(f"Erreur lors de l'enregistrement de la relance : {e}", "danger")

    return redirect(
        url_for("dossiers.detail", dossier_id=dossier.id)
    )
