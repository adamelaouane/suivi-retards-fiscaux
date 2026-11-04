from decimal import Decimal
from sqlalchemy import or_

from app.extensions import db
from app.models.contribuable import Contribuable
from app.models.parametre import Parametre
from app.services.audit import enregistrer_audit


class ContribuableInvalide(ValueError):
    """Erreur de validation sur les données du contribuable."""


def lister_contribuables(recherche=None, page=1, par_page=None):
    if par_page is None:
        par_page = Parametre.get_valeur("lignes_par_page", 20)

    query = Contribuable.query

    if recherche:
        recherche_str = f"%{recherche.strip()}%"
        query = query.filter(
            or_(
                Contribuable.nom.ilike(recherche_str),
                Contribuable.prenom.ilike(recherche_str),
                Contribuable.identifiant_fiscal.ilike(recherche_str),
                Contribuable.cin.ilike(recherche_str),
                Contribuable.telephone.ilike(recherche_str),
            )
        )

    pagination = query.order_by(Contribuable.nom.asc(), Contribuable.prenom.asc()).paginate(
        page=page,
        per_page=par_page,
        error_out=False,
    )
    return pagination


def creer_contribuable(identifiant_fiscal, nom, prenom=None, cin=None, telephone=None, utilisateur=None):
    identifiant = (identifiant_fiscal or "").strip()
    if not identifiant:
        raise ContribuableInvalide("L'identifiant fiscal est obligatoire.")

    if Contribuable.query.filter_by(identifiant_fiscal=identifiant).first():
        raise ContribuableInvalide(f"L'identifiant fiscal '{identifiant}' existe déjà.")

    nom_clean = (nom or "").strip()
    if not nom_clean:
        raise ContribuableInvalide("Le nom du contribuable est obligatoire.")

    cin_clean = (cin or "").strip() or None
    if cin_clean and Contribuable.query.filter_by(cin=cin_clean).first():
        raise ContribuableInvalide(f"Le CIN '{cin_clean}' est déjà attribué à un autre contribuable.")

    contribuable = Contribuable(
        identifiant_fiscal=identifiant,
        nom=nom_clean,
        prenom=(prenom or "").strip() or "",
        cin=cin_clean,
        telephone=(telephone or "").strip() or None,
    )

    try:
        db.session.add(contribuable)
        enregistrer_audit(
            action="CREATION",
            objet="Contribuable",
            reference=identifiant,
            description=f"Création contribuable {contribuable.nom_complet} ({identifiant})",
            utilisateur=utilisateur,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return contribuable


def modifier_contribuable(contribuable, nom, prenom=None, cin=None, telephone=None, utilisateur=None):
    if contribuable is None:
        raise ContribuableInvalide("Contribuable introuvable.")

    nom_clean = (nom or "").strip()
    if not nom_clean:
        raise ContribuableInvalide("Le nom du contribuable est obligatoire.")

    cin_clean = (cin or "").strip() or None
    if cin_clean:
        existant = Contribuable.query.filter_by(cin=cin_clean).first()
        if existant and existant.id != contribuable.id:
            raise ContribuableInvalide(f"Le CIN '{cin_clean}' est déjà utilisé.")

    contribuable.nom = nom_clean
    contribuable.prenom = (prenom or "").strip() or ""
    contribuable.cin = cin_clean
    contribuable.telephone = (telephone or "").strip() or None

    try:
        enregistrer_audit(
            action="MODIFICATION",
            objet="Contribuable",
            reference=contribuable.identifiant_fiscal,
            description=f"Modification coordonnées contribuable {contribuable.nom_complet}",
            utilisateur=utilisateur,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return contribuable


def get_situation_financiere(contribuable):
    dossiers = contribuable.dossiers
    total_du = sum((Decimal(d.montant_exigible) for d in dossiers), Decimal("0.00"))
    total_paye = sum((d.montant_paye for d in dossiers), Decimal("0.00"))
    total_restant = sum((d.montant_restant for d in dossiers), Decimal("0.00"))
    en_retard = [d for d in dossiers if d.jours_retard > 0 and d.montant_restant > 0]

    return {
        "total_dossiers": len(dossiers),
        "total_du": total_du,
        "total_paye": total_paye,
        "total_restant": total_restant,
        "nb_en_retard": len(en_retard),
        "dossiers": sorted(dossiers, key=lambda d: d.date_limite),
    }
