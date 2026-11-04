
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    request,
    url_for,
)

from app.extensions import db
from app.models.dossier_fiscal import DossierFiscal
from app.models.paiement import Paiement
from app.services.calculs_fiscaux import (
    PaiementInvalide,
    annuler_paiement,
    enregistrer_paiement,
)

paiements_bp = Blueprint(
    "paiements",
    __name__,
    url_prefix="/paiements",
)


@paiements_bp.route("/enregistrer", methods=["POST"])
def enregistrer():
    dossier_id = request.form.get("dossier_id", type=int)

    dossier = db.session.get(DossierFiscal, dossier_id)

    if dossier is None:
        abort(404)

    montant = request.form.get("montant")
    date_str = request.form.get("date_paiement")
    reference = request.form.get("reference")
    observations = request.form.get("observations")

    date_paiement = None

    if date_str:
        try:
            date_paiement = datetime.strptime(
                date_str.strip(),
                "%Y-%m-%d",
            ).date()
        except ValueError:
            flash("Format de date de paiement invalide.", "danger")
            return redirect(
                url_for("dossiers.detail", dossier_id=dossier.id)
            )

    try:
        paiement = enregistrer_paiement(
            dossier=dossier,
            montant=montant,
            date_paiement=date_paiement,
            reference=reference,
            observations=observations,
        )

        flash(
            f"Paiement de {paiement.montant} DH enregistré avec succès.",
            "success",
        )

    except PaiementInvalide as e:
        flash(str(e), "danger")

    except Exception as e:
        flash(f"Erreur lors de l'enregistrement : {e}", "danger")

    return redirect(
        url_for("dossiers.detail", dossier_id=dossier.id)
    )


@paiements_bp.route("/<int:paiement_id>/annuler", methods=["POST"])
def annuler(paiement_id):
    paiement = db.session.get(Paiement, paiement_id)

    if paiement is None:
        abort(404)

    motif = request.form.get("motif")

    try:
        annuler_paiement(
            paiement=paiement,
            motif=motif,
        )

        flash(
            f"Paiement #{paiement.id} annulé avec succès.",
            "info",
        )

    except PaiementInvalide as e:
        flash(str(e), "danger")

    except Exception as e:
        flash(f"Erreur lors de l'annulation : {e}", "danger")

    return redirect(
        url_for("dossiers.detail", dossier_id=paiement.dossier_id)
    )
