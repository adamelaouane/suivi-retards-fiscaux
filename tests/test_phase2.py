from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import AuditLog, Contribuable, DossierFiscal, Parametre, TypeTaxe
from app.services.audit import enregistrer_audit
from app.services.calculs_fiscaux import (
    PaiementInvalide,
    annuler_paiement,
    enregistrer_paiement,
)


def creer_dossier():
    c = Contribuable(identifiant_fiscal="IF-P2", nom="Test Phase 2")
    t = TypeTaxe(code="P2", libelle="Taxe Phase 2")
    db.session.add_all([c, t])
    db.session.flush()
    d = DossierFiscal(
        numero_dossier="D-P2-1",
        contribuable_id=c.id,
        type_taxe_id=t.id,
        annee_fiscale=2025,
        date_limite=date.today() - timedelta(days=15),
        montant_exigible=Decimal("1000.00"),
    )
    db.session.add(d)
    db.session.commit()
    return d


def test_paiement_statut_et_annulation(app):
    d = creer_dossier()
    p = enregistrer_paiement(d, "400.00", reference="P-REF-1")
    assert p.statut == "VALIDE"
    assert d.montant_paye == Decimal("400.00")
    assert d.montant_restant == Decimal("600.00")

    # Annulation
    annuler_paiement(p, motif="Erreur de saisie")
    assert p.statut == "ANNULE"
    assert p.motif_annulation == "Erreur de saisie"
    assert d.montant_paye == Decimal("0.00")
    assert d.montant_restant == Decimal("1000.00")

    # Impossible de ré-annuler
    with pytest.raises(PaiementInvalide):
        annuler_paiement(p, motif="Autre motif")


def test_annulation_sans_motif_refusee(app):
    d = creer_dossier()
    p = enregistrer_paiement(d, "200.00")
    with pytest.raises(PaiementInvalide):
        annuler_paiement(p, motif="")


def test_parametre_get_set_et_types(app):
    Parametre.set_valeur("seuil_test", 45, description="Seuil de test")
    db.session.commit()
    assert Parametre.get_valeur("seuil_test") == 45

    Parametre.set_valeur("activer_feature", True)
    db.session.commit()
    assert Parametre.get_valeur("activer_feature") is True

    Parametre.set_valeur("nom_application", "Suivi Fiscal")
    db.session.commit()
    assert Parametre.get_valeur("nom_application") == "Suivi Fiscal"


def test_parametre_valeurs_par_defaut(app):
    Parametre.initialiser_defauts()
    assert Parametre.get_valeur("seuil_retard_significatif") == 30
    assert Parametre.get_valeur("seuil_retard_critique") == 90
    assert Parametre.get_valeur("lignes_par_page") == 20


def test_audit_log(app):
    nb_initial = AuditLog.query.count()
    enregistrer_audit(
        action="TEST_ACTION",
        objet="TestObject",
        reference="REF-001",
        description="Description test audit",
        utilisateur="Agent Test",
    )
    db.session.commit()
    assert AuditLog.query.count() == nb_initial + 1
    log = AuditLog.query.order_by(AuditLog.id.desc()).first()
    assert log.action == "TEST_ACTION"
    assert log.objet == "TestObject"
    assert log.utilisateur == "Agent Test"
