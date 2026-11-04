from datetime import datetime
from app.extensions import db
from app.models.relance import Relance
from app.services.audit import enregistrer_audit


class RelanceInvalide(ValueError):
    """Erreur lors de l'enregistrement d'une relance."""


def enregistrer_relance(dossier, canal, message, statut="ENREGISTREE", reference_externe=None, utilisateur=None):
    if dossier is None:
        raise RelanceInvalide("Dossier introuvable.")

    message_clean = (message or "").strip()
    if not message_clean:
        raise RelanceInvalide("Le message ou contenu de la relance est obligatoire.")

    canal_clean = (canal or "MANUEL").strip().upper()
    statut_clean = (statut or "ENREGISTREE").strip().upper()

    relance = Relance(
        dossier_id=dossier.id,
        canal=canal_clean,
        message=message_clean,
        statut=statut_clean,
        reference_externe=(reference_externe or "").strip() or None,
        date_tentative=datetime.utcnow(),
    )

    try:
        db.session.add(relance)
        enregistrer_audit(
            action="RELANCE",
            objet="Relance",
            reference=f"Dossier {dossier.numero_dossier}",
            description=f"Relance [{canal_clean}] pour {dossier.contribuable.nom_complet} : {message_clean}",
            utilisateur=utilisateur,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return relance
