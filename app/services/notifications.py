"""Service de notification et gestion des relances."""

from app.relances.services import enregistrer_relance, RelanceInvalide


def envoyer_notification_rappel(dossier, canal="EMAIL", utilisateur=None):
    """Génère un message de rappel et consigne la relance."""
    message = (
        f"Rappel d'échéance fiscale pour le dossier {dossier.numero_dossier} "
        f"({dossier.type_taxe.libelle} - {dossier.annee_fiscale}). "
        f"Montant restant dû : {dossier.montant_restant} DH."
    )
    return enregistrer_relance(
        dossier=dossier,
        canal=canal,
        message=message,
        statut="ENVOYEE",
        utilisateur=utilisateur,
    )
