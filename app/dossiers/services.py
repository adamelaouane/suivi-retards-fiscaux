from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models.contribuable import Contribuable
from app.models.dossier_fiscal import DossierFiscal
from app.models.type_taxe import TypeTaxe
from app.services.audit import enregistrer_audit


class DossierInvalide(ValueError):
    """Erreur de validation lors de la création ou modification d'un dossier."""


def creer_dossier(numero_dossier, contribuable_id, type_taxe_id, annee_fiscale, date_limite, montant_exigible, observations=None, utilisateur=None):
    numero = (numero_dossier or "").strip()
    if not numero:
        raise DossierInvalide("Le numéro de dossier est obligatoire.")

    if DossierFiscal.query.filter_by(numero_dossier=numero).first():
        raise DossierInvalide(f"Le numéro de dossier '{numero}' existe déjà.")

    contribuable = db.session.get(Contribuable, contribuable_id)
    if not contribuable:
        raise DossierInvalide("Le contribuable sélectionné est introuvable.")

    type_taxe = db.session.get(TypeTaxe, type_taxe_id)
    if not type_taxe:
        raise DossierInvalide("Le type de taxe sélectionné est introuvable.")

    if not type_taxe.actif:
        raise DossierInvalide(f"Le type de taxe '{type_taxe.libelle}' est inactif.")

    try:
        annee = int(annee_fiscale)
    except (ValueError, TypeError):
        raise DossierInvalide("Année fiscale invalide.")

    if annee < 1900 or annee > 2100:
        raise DossierInvalide("L'année fiscale doit être comprise entre 1900 et 2100.")

    if isinstance(date_limite, str):
        try:
            date_limite = datetime.strptime(date_limite.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise DossierInvalide("Format de date limite invalide (AAAA-MM-JJ attendu).")
    elif not isinstance(date_limite, date):
        raise DossierInvalide("Date limite obligatoire.")

    try:
        montant = Decimal(str(montant_exigible).strip().replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        raise DossierInvalide("Montant exigible invalide.")

    if not montant.is_finite() or montant <= 0:
        raise DossierInvalide("Le montant exigible doit être strictement supérieur à 0.")

    montant = montant.quantize(Decimal("0.01"))

    dossier = DossierFiscal(
        numero_dossier=numero,
        contribuable_id=contribuable.id,
        type_taxe_id=type_taxe.id,
        annee_fiscale=annee,
        date_limite=date_limite,
        montant_exigible=montant,
        observations=(observations or "").strip() or None,
    )

    try:
        db.session.add(dossier)
        enregistrer_audit(
            action="CREATION",
            objet="DossierFiscal",
            reference=numero,
            description=f"Création dossier {numero} pour {contribuable.nom_complet} (Montant: {montant} DH)",
            utilisateur=utilisateur,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return dossier


def modifier_dossier(dossier, date_limite=None, observations=None, utilisateur=None):
    if dossier is None:
        raise DossierInvalide("Dossier introuvable.")

    if date_limite is not None:
        if isinstance(date_limite, str):
            try:
                date_limite = datetime.strptime(date_limite.strip(), "%Y-%m-%d").date()
            except ValueError:
                raise DossierInvalide("Format de date limite invalide.")
        dossier.date_limite = date_limite

    dossier.observations = (observations or "").strip() or None

    try:
        enregistrer_audit(
            action="MODIFICATION",
            objet="DossierFiscal",
            reference=dossier.numero_dossier,
            description=f"Modification dossier {dossier.numero_dossier} (Nouvelle échéance: {dossier.date_limite})",
            utilisateur=utilisateur,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return dossier
