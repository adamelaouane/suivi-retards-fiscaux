from app.extensions import db
from app.models.type_taxe import TypeTaxe
from app.services.audit import enregistrer_audit


class TypeTaxeInvalide(ValueError):
    """Erreur de validation sur les types de taxes."""


def lister_types_taxes(inclure_inactifs=True):
    query = TypeTaxe.query
    if not inclure_inactifs:
        query = query.filter_by(actif=True)
    return query.order_by(TypeTaxe.code.asc()).all()


def creer_type_taxe(code, libelle, description=None, utilisateur=None):
    code_clean = (code or "").strip().upper()
    if not code_clean:
        raise TypeTaxeInvalide("Le code de la taxe est obligatoire.")

    if TypeTaxe.query.filter_by(code=code_clean).first():
        raise TypeTaxeInvalide(f"Le type de taxe avec le code '{code_clean}' existe déjà.")

    libelle_clean = (libelle or "").strip()
    if not libelle_clean:
        raise TypeTaxeInvalide("Le libellé de la taxe est obligatoire.")

    type_taxe = TypeTaxe(
        code=code_clean,
        libelle=libelle_clean,
        description=(description or "").strip() or None,
        actif=True,
    )

    try:
        db.session.add(type_taxe)
        enregistrer_audit(
            action="CREATION",
            objet="TypeTaxe",
            reference=code_clean,
            description=f"Création type de taxe {code_clean} - {libelle_clean}",
            utilisateur=utilisateur,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return type_taxe


def modifier_type_taxe(type_taxe, libelle, description=None, utilisateur=None):
    if type_taxe is None:
        raise TypeTaxeInvalide("Type de taxe introuvable.")

    libelle_clean = (libelle or "").strip()
    if not libelle_clean:
        raise TypeTaxeInvalide("Le libellé de la taxe est obligatoire.")

    type_taxe.libelle = libelle_clean
    type_taxe.description = (description or "").strip() or None

    try:
        enregistrer_audit(
            action="MODIFICATION",
            objet="TypeTaxe",
            reference=type_taxe.code,
            description=f"Modification type de taxe {type_taxe.code} ({libelle_clean})",
            utilisateur=utilisateur,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return type_taxe


def basculer_statut_type_taxe(type_taxe, utilisateur=None):
    if type_taxe is None:
        raise TypeTaxeInvalide("Type de taxe introuvable.")

    type_taxe.actif = not type_taxe.actif
    action = "ACTIVATION" if type_taxe.actif else "DESACTIVATION"

    try:
        enregistrer_audit(
            action=action,
            objet="TypeTaxe",
            reference=type_taxe.code,
            description=f"{action.capitalize()} du type de taxe {type_taxe.code}",
            utilisateur=utilisateur,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return type_taxe
