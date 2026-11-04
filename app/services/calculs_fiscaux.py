"""Logique métier des paiements (règles du cahier des charges)."""

from datetime import date
from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models.paiement import Paiement
from app.services.audit import enregistrer_audit


class PaiementInvalide(ValueError):
    """Erreur de validation d'un paiement (message lisible par l'utilisateur)."""


def convertir_montant_paiement(valeur):
    try:
        montant = Decimal(str(valeur).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        raise PaiementInvalide("Montant invalide.")

    if not montant.is_finite() or montant <= 0:
        raise PaiementInvalide("Le montant du paiement doit être strictement positif.")

    return montant.quantize(Decimal("0.01"))


def enregistrer_paiement(dossier, montant, date_paiement=None, reference=None, observations=None, utilisateur=None):
    """Valide puis enregistre un paiement dans une seule transaction.

    Refuse un montant <= 0 ou supérieur au montant restant.
    En cas d'erreur, rien n'est enregistré.
    """
    if dossier is None:
        raise PaiementInvalide("Le paiement doit être associé à un dossier existant.")

    montant = convertir_montant_paiement(montant)

    if montant > dossier.montant_restant:
        raise PaiementInvalide(
            f"Le paiement ({montant}) dépasse le montant restant ({dossier.montant_restant})."
        )

    reference = (reference or "").strip() or None
    if reference and Paiement.query.filter_by(reference=reference).first():
        raise PaiementInvalide(f"La référence de paiement existe déjà : {reference}")

    paiement = Paiement(
        dossier_id=dossier.id,
        montant=montant,
        date_paiement=date_paiement or date.today(),
        reference=reference,
        observations=observations,
        statut="VALIDE",
    )

    try:
        db.session.add(paiement)
        enregistrer_audit(
            action="PAIEMENT",
            objet="Paiement",
            reference=reference or f"Dossier {dossier.numero_dossier}",
            description=f"Enregistrement paiement de {montant} pour le dossier {dossier.numero_dossier}",
            utilisateur=utilisateur,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return paiement


def annuler_paiement(paiement, motif, utilisateur=None):
    """Annule un paiement validé avec motif obligatoire et trace d'audit."""
    if paiement is None:
        raise PaiementInvalide("Paiement introuvable.")

    if paiement.statut == "ANNULE":
        raise PaiementInvalide("Ce paiement est déjà annulé.")

    motif = (motif or "").strip()
    if not motif:
        raise PaiementInvalide("Le motif d'annulation est obligatoire.")

    try:
        paiement.statut = "ANNULE"
        paiement.motif_annulation = motif
        enregistrer_audit(
            action="ANNULATION",
            objet="Paiement",
            reference=paiement.reference or str(paiement.id),
            description=f"Annulation paiement #{paiement.id} ({paiement.montant}) : {motif}",
            utilisateur=utilisateur,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return paiement
