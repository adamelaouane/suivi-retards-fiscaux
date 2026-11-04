import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pandas as pd
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Contribuable, DossierFiscal, ImportBatch, TypeTaxe
from app.services.audit import enregistrer_audit


def lire_fichier(fichier, nom_fichier):
    """Lire un fichier CSV ou Excel."""
    extension = nom_fichier.rsplit(".", 1)[-1].lower()
    contenu = fichier.read()

    if extension == "csv":
        try:
            return pd.read_csv(
                BytesIO(contenu), sep=None, engine="python", dtype=str
            )
        except UnicodeDecodeError:
            return pd.read_csv(
                BytesIO(contenu), sep=None, engine="python",
                encoding="latin-1", dtype=str
            )
    if extension == "xlsx":
        return pd.read_excel(BytesIO(contenu), dtype=str)

    raise ValueError("Format non supporté. Utilisez CSV ou XLSX.")


def nettoyer_texte(valeur):
    """Convertir une valeur pandas en texte propre."""
    if valeur is None or pd.isna(valeur):
        return ""
    return str(valeur).strip()


def convertir_montant(valeur):
    """Convertir un montant en Decimal sans passer par float."""
    if valeur is None or pd.isna(valeur):
        raise ValueError("Montant manquant.")

    texte = str(valeur).strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        montant = Decimal(texte)
    except (InvalidOperation, ValueError):
        raise ValueError("Format de montant invalide.")

    if not montant.is_finite() or montant <= 0:
        raise ValueError("Le montant doit être supérieur à zéro.")
    return montant.quantize(Decimal("0.01"))


def convertir_date(valeur):
    """Convertir une date depuis les formats courants du fichier."""
    if valeur is None or pd.isna(valeur):
        raise ValueError("Date manquante.")
    if isinstance(valeur, (datetime, pd.Timestamp)):
        return valeur.date()
    if isinstance(valeur, date):
        return valeur

    texte = str(valeur).strip()
    for format_date in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(texte, format_date).date()
        except ValueError:
            continue
    raise ValueError(
        f"Format de date non reconnu : {texte}. "
        "Formats acceptés : JJ/MM/AAAA ou AAAA-MM-JJ."
    )


def importer_dossiers(fichier, nom_fichier):
    """Importer des dossiers. Chaque ligne est isolée par un savepoint."""
    extension = nom_fichier.rsplit(".", 1)[-1].lower()
    batch = ImportBatch(
        nom_fichier=nom_fichier,
        type_fichier=extension.upper(),
        statut="EN_COURS",
    )
    db.session.add(batch)
    db.session.flush()

    erreurs = []
    nombre_importes = 0

    try:
        df = lire_fichier(fichier, nom_fichier)
        colonnes = [str(col).strip().lower() for col in df.columns]
        if len(colonnes) != len(set(colonnes)):
            raise ValueError("Le fichier contient des noms de colonnes en double.")

        colonnes_requises = {
            "numero_dossier", "identifiant_fiscal", "nom", "type_taxe",
            "annee_fiscale", "date_limite", "montant_exigible",
        }
        manquantes = colonnes_requises.difference(colonnes)
        if manquantes:
            raise ValueError(
                "Colonne(s) obligatoire(s) manquante(s) : "
                + ", ".join(sorted(manquantes))
            )
        df.columns = colonnes
        batch.nombre_lignes = len(df)

        contribuables = {
            c.identifiant_fiscal: c for c in Contribuable.query.all()
        }
        cin_vers_identifiant = {
            c.cin: c.identifiant_fiscal
            for c in Contribuable.query.filter(Contribuable.cin.isnot(None)).all()
        }
        types_taxes = {t.code.upper(): t for t in TypeTaxe.query.all()}
        dossiers_existants = {
            d.numero_dossier for d in DossierFiscal.query.all()
        }
        dossiers_du_fichier = set()

        for index, ligne in df.iterrows():
            numero_ligne = index + 2
            try:
                # Valider toutes les données avant toute création en base.
                numero_dossier = nettoyer_texte(ligne["numero_dossier"])
                identifiant = nettoyer_texte(ligne["identifiant_fiscal"])
                nom = nettoyer_texte(ligne["nom"])
                prenom = nettoyer_texte(ligne.get("prenom", ""))
                cin = nettoyer_texte(ligne.get("cin", "")) or None
                telephone = nettoyer_texte(ligne.get("telephone", "")) or None
                code_taxe = nettoyer_texte(ligne["type_taxe"]).upper()
                annee_texte = nettoyer_texte(ligne["annee_fiscale"])
                observations = nettoyer_texte(ligne.get("observations", "")) or None

                if not numero_dossier:
                    raise ValueError("Numéro de dossier vide.")
                if numero_dossier in dossiers_du_fichier or numero_dossier in dossiers_existants:
                    raise ValueError(f"Dossier déjà existant ou répété : {numero_dossier}")
                if not identifiant:
                    raise ValueError("Identifiant fiscal vide.")
                if not nom:
                    raise ValueError("Nom du contribuable vide.")
                if not code_taxe:
                    raise ValueError("Type de taxe vide.")

                try:
                    annee_decimal = Decimal(annee_texte)
                    if not annee_decimal.is_finite() or annee_decimal != annee_decimal.to_integral_value():
                        raise ValueError
                    annee = int(annee_decimal)
                except (InvalidOperation, ValueError):
                    raise ValueError("Année fiscale invalide.")
                if not 1900 <= annee <= 2100:
                    raise ValueError("Année fiscale invalide.")

                date_limite = convertir_date(ligne["date_limite"])
                montant = convertir_montant(ligne["montant_exigible"])

                contribuable = contribuables.get(identifiant)
                if contribuable is None and cin:
                    autre_identifiant = cin_vers_identifiant.get(cin)
                    if autre_identifiant and autre_identifiant != identifiant:
                        raise ValueError(
                            f"CIN déjà associé à un autre contribuable : {cin}"
                        )

                # Toutes les opérations SQL de la ligne sont dans un savepoint.
                with db.session.begin_nested():
                    if contribuable is None:
                        contribuable = Contribuable(
                            identifiant_fiscal=identifiant,
                            nom=nom,
                            prenom=prenom,
                            cin=cin,
                            telephone=telephone,
                        )
                        db.session.add(contribuable)
                        db.session.flush()

                    type_taxe = types_taxes.get(code_taxe)
                    if type_taxe is None:
                        libelle = nettoyer_texte(ligne.get("libelle_taxe", "")) or code_taxe
                        type_taxe = TypeTaxe(
                            code=code_taxe,
                            libelle=libelle,
                            actif=True,
                        )
                        db.session.add(type_taxe)
                        db.session.flush()

                    dossier = DossierFiscal(
                        numero_dossier=numero_dossier,
                        contribuable_id=contribuable.id,
                        type_taxe_id=type_taxe.id,
                        annee_fiscale=annee,
                        date_limite=date_limite,
                        montant_exigible=montant,
                        observations=observations,
                    )
                    db.session.add(dossier)
                    db.session.flush()

                contribuables[identifiant] = contribuable
                if cin:
                    cin_vers_identifiant[cin] = identifiant
                types_taxes[code_taxe] = type_taxe
                dossiers_du_fichier.add(numero_dossier)
                dossiers_existants.add(numero_dossier)
                nombre_importes += 1

            except IntegrityError:
                # Le savepoint de la ligne a été annulé par la sortie du contexte.
                erreurs.append({
                    "ligne": numero_ligne,
                    "erreur": "Conflit de données : identifiant fiscal, CIN, type de taxe ou numéro de dossier déjà utilisé.",
                })
            except Exception as erreur:
                erreurs.append({"ligne": numero_ligne, "erreur": str(erreur)})

        batch.nombre_importes = nombre_importes
        batch.nombre_erreurs = len(erreurs)
        batch.details_erreurs = json.dumps(erreurs, ensure_ascii=False)
        batch.statut = "TERMINE" if not erreurs else "TERMINE_AVEC_ERREURS"

        enregistrer_audit(
            action="IMPORT",
            objet="ImportBatch",
            reference=str(batch.id),
            description=(
                f"Importation {nom_fichier} : {nombre_importes} importés, "
                f"{len(erreurs)} erreurs"
            ),
        )
        db.session.commit()

        return {
            "batch": batch,
            "nombre_importes": nombre_importes,
            "nombre_erreurs": len(erreurs),
            "erreurs": erreurs,
        }

    except Exception:
        db.session.rollback()
        raise
