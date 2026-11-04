from io import BytesIO

from app.extensions import db
from app.models import Contribuable, DossierFiscal, ImportBatch, TypeTaxe


def _importer(app, contenu, nom="test.csv"):
    return app.test_client().post(
        "/importation/",
        data={"fichier": (BytesIO(contenu.encode("utf-8")), nom)},
        content_type="multipart/form-data",
    )


def test_import_csv_zero_initial_et_erreurs(app):
    db.session.add_all([
        Contribuable(identifiant_fiscal="00123", nom="A"),
        TypeTaxe(code="TVA", libelle="TVA"),
    ])
    db.session.commit()

    csv = (
        "numero_dossier,identifiant_fiscal,nom,type_taxe,annee_fiscale,date_limite,montant_exigible\n"
        "D1,00123,A,TVA,2025,31/12/2025,1500.50\n"
        "D2,99999,B,TVA,2025,31/12/2025,100\n"
        "D1,00123,A,TVA,2025,31/12/2025,100\n"
    )
    response = _importer(app, csv)

    assert response.status_code == 200
    assert DossierFiscal.query.count() == 2
    assert Contribuable.query.filter_by(identifiant_fiscal="99999").count() == 1
    batch = ImportBatch.query.order_by(ImportBatch.id.desc()).first()
    assert batch.nombre_importes == 2
    assert batch.nombre_erreurs == 1
    assert str(DossierFiscal.query.filter_by(numero_dossier="D1").one().montant_exigible) == "1500.50"


def test_import_continue_apres_cin_deja_utilise(app):
    db.session.add_all([
        Contribuable(identifiant_fiscal="IF-EXISTANT", nom="A", cin="AB123456"),
        TypeTaxe(code="TVA", libelle="TVA"),
    ])
    db.session.commit()

    csv = (
        "numero_dossier,identifiant_fiscal,nom,cin,type_taxe,annee_fiscale,date_limite,montant_exigible\n"
        "D1,IF-NOUVEAU-1,B,AB123456,TVA,2025,31/12/2025,100\n"
        "D2,IF-NOUVEAU-2,C,CD654321,TVA,2025,31/12/2025,200\n"
    )
    response = _importer(app, csv)

    assert response.status_code == 200
    assert DossierFiscal.query.count() == 1
    assert DossierFiscal.query.first().numero_dossier == "D2"
    assert Contribuable.query.filter_by(identifiant_fiscal="IF-NOUVEAU-1").count() == 0
    assert Contribuable.query.filter_by(identifiant_fiscal="IF-NOUVEAU-2").count() == 1
    batch = ImportBatch.query.order_by(ImportBatch.id.desc()).first()
    assert batch.nombre_importes == 1
    assert batch.nombre_erreurs == 1


def test_import_rejette_montant_invalide_sans_creer_contribuable(app):
    db.session.add(TypeTaxe(code="TVA", libelle="TVA"))
    db.session.commit()

    csv = (
        "numero_dossier,identifiant_fiscal,nom,type_taxe,annee_fiscale,date_limite,montant_exigible\n"
        "D1,IF-INVALID,Nom,TVA,2025,31/12/2025,abc\n"
    )
    response = _importer(app, csv)

    assert response.status_code == 200
    assert DossierFiscal.query.count() == 0
    assert Contribuable.query.filter_by(identifiant_fiscal="IF-INVALID").count() == 0
