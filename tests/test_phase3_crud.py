from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

import pytest

from app.extensions import db
from app.models import Contribuable, DossierFiscal, Paiement, Parametre, Relance, TypeTaxe
from app.services.calculs_fiscaux import enregistrer_paiement


@pytest.fixture()
def client(app):
    return app.test_client()


def test_contribuables_crud(client):
    # Création
    r = client.post(
        "/contribuables/nouveau",
        data={
            "identifiant_fiscal": "IF-TEST-100",
            "nom": "Benali",
            "prenom": "Karim",
            "cin": "AB123456",
            "telephone": "0600000000",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    contribuable = Contribuable.query.filter_by(identifiant_fiscal="IF-TEST-100").first()
    assert contribuable is not None
    assert contribuable.nom == "Benali"
    assert "Benali" in r.get_data(as_text=True)

    # Doublon refusé
    r_double = client.post(
        "/contribuables/nouveau",
        data={
            "identifiant_fiscal": "IF-TEST-100",
            "nom": "Autre",
        },
        follow_redirects=True,
    )
    assert "existe déjà" in r_double.get_data(as_text=True)

    # Modification
    r_edit = client.post(
        f"/contribuables/{contribuable.id}/modifier",
        data={
            "nom": "Benali Modifié",
            "prenom": "Karim",
            "cin": "AB123456",
            "telephone": "0611111111",
        },
        follow_redirects=True,
    )
    assert r_edit.status_code == 200
    assert contribuable.nom == "Benali Modifié"
    assert contribuable.telephone == "0611111111"

    # Liste
    r_list = client.get("/contribuables/?q=Benali")
    assert r_list.status_code == 200
    assert "Benali Modifié" in r_list.get_data(as_text=True)


def test_types_taxes_crud(client):
    # Création
    r = client.post(
        "/types-taxes/nouveau",
        data={
            "code": "IS_TEST",
            "libelle": "Impôt sur les Sociétés",
            "description": "Impôt annuel des personnes morales",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    taxe = TypeTaxe.query.filter_by(code="IS_TEST").first()
    assert taxe is not None
    assert taxe.actif is True

    # Basculer statut
    client.post(f"/types-taxes/{taxe.id}/basculer-statut", follow_redirects=True)
    assert taxe.actif is False

    client.post(f"/types-taxes/{taxe.id}/basculer-statut", follow_redirects=True)
    assert taxe.actif is True

    # Modification
    client.post(
        f"/types-taxes/{taxe.id}/modifier",
        data={"libelle": "IS Modifié", "description": "Nouvelle desc"},
        follow_redirects=True,
    )
    assert taxe.libelle == "IS Modifié"


def test_dossiers_et_paiements_et_relances(client):
    c = Contribuable(identifiant_fiscal="IF-DOS-1", nom="Entreprise Atlas")
    t = TypeTaxe(code="TAX-1", libelle="Taxe Urbaine")
    db.session.add_all([c, t])
    db.session.commit()

    # Création dossier
    r = client.post(
        "/dossiers/nouveau",
        data={
            "numero_dossier": "DOS-2025-999",
            "contribuable_id": c.id,
            "type_taxe_id": t.id,
            "annee_fiscale": "2025",
            "date_limite": (date.today() - timedelta(days=20)).strftime("%Y-%m-%d"),
            "montant_exigible": "5000.00",
            "observations": "Dossier test complet",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    dossier = DossierFiscal.query.filter_by(numero_dossier="DOS-2025-999").first()
    assert dossier is not None
    assert dossier.en_retard is True
    assert dossier.jours_retard == 20

    # Consultation détail
    r_detail = client.get(f"/dossiers/{dossier.id}")
    assert r_detail.status_code == 200
    assert "DOS-2025-999" in r_detail.get_data(as_text=True)

    # Modification dossier
    client.post(
        f"/dossiers/{dossier.id}/modifier",
        data={
            "date_limite": (date.today() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "observations": "Échéance reportée",
        },
        follow_redirects=True,
    )
    assert dossier.observations == "Échéance reportée"
    assert dossier.en_retard is False

    # Enregistrement paiement via route
    r_pay = client.post(
        "/paiements/enregistrer",
        data={
            "dossier_id": dossier.id,
            "montant": "2000.00",
            "date_paiement": date.today().strftime("%Y-%m-%d"),
            "reference": "REF-VIR-999",
            "observations": "Virement bancaire",
        },
        follow_redirects=True,
    )
    assert r_pay.status_code == 200
    assert dossier.montant_paye == Decimal("2000.00")
    assert dossier.montant_restant == Decimal("3000.00")
    assert dossier.statut == "PARTIELLEMENT_PAYE"

    paiement = Paiement.query.filter_by(reference="REF-VIR-999").first()
    assert paiement is not None

    # Annulation paiement via route
    r_cancel = client.post(
        f"/paiements/{paiement.id}/annuler",
        data={"motif": "Chèque sans provision"},
        follow_redirects=True,
    )
    assert r_cancel.status_code == 200
    assert paiement.statut == "ANNULE"
    assert dossier.montant_paye == Decimal("0.00")
    assert dossier.montant_restant == Decimal("5000.00")

    # Enregistrement relance via route
    r_rel = client.post(
        "/relances/enregistrer",
        data={
            "dossier_id": dossier.id,
            "canal": "EMAIL",
            "statut": "ENVOYEE",
            "message": "Notification de mise en demeure",
        },
        follow_redirects=True,
    )
    assert r_rel.status_code == 200
    assert Relance.query.filter_by(dossier_id=dossier.id).count() == 1


def test_parametres_route(client):
    r_get = client.get("/parametres/")
    assert r_get.status_code == 200

    r_post = client.post(
        "/parametres/",
        data={
            "seuil_retard_significatif": "45",
            "seuil_retard_critique": "120",
            "lignes_par_page": "25",
            "nom_organisme": "Direction Régionale des Impôts",
        },
        follow_redirects=True,
    )
    assert r_post.status_code == 200
    assert Parametre.get_valeur("seuil_retard_significatif") == 45
    assert Parametre.get_valeur("nom_organisme") == "Direction Régionale des Impôts"


def test_page_404(client):
    r = client.get("/cette-page-n-existe-absolument-pas")
    assert r.status_code == 404
    assert "404" in r.get_data(as_text=True)
