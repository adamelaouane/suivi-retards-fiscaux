from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Contribuable, DossierFiscal, TypeTaxe
from app.services.calculs_fiscaux import PaiementInvalide, enregistrer_paiement


def creer_dossier(delta_jours=-10, montant="1000.00"):
    c = Contribuable(identifiant_fiscal="IF-T1", nom="Test")
    t = TypeTaxe(code="T", libelle="Taxe test")
    db.session.add_all([c, t])
    db.session.flush()
    d = DossierFiscal(
        numero_dossier="D-1",
        contribuable_id=c.id,
        type_taxe_id=t.id,
        annee_fiscale=2025,
        date_limite=date.today() + timedelta(days=delta_jours),
        montant_exigible=Decimal(montant),
    )
    db.session.add(d)
    db.session.commit()
    return d


def test_impaye_en_retard(app):
    d = creer_dossier(-10)
    assert d.statut == "IMPAYE"
    assert d.montant_restant == Decimal("1000.00")
    assert d.jours_retard == 10


def test_echeance_aujourdhui_pas_en_retard(app):
    assert creer_dossier(0).jours_retard == 0


def test_paiement_partiel_puis_total(app):
    d = creer_dossier()
    enregistrer_paiement(d, "400")
    assert d.statut == "PARTIELLEMENT_PAYE"
    assert d.montant_restant == Decimal("600.00")
    enregistrer_paiement(d, "600,00")
    assert d.statut == "PAYE"
    assert d.jours_retard == 0


@pytest.mark.parametrize("valeur", ["0", "-5", "abc", ""])
def test_paiement_invalide_refuse(app, valeur):
    d = creer_dossier()
    with pytest.raises(PaiementInvalide):
        enregistrer_paiement(d, valeur)
    assert d.montant_paye == Decimal("0.00")


def test_paiement_superieur_au_restant_refuse(app):
    d = creer_dossier()
    with pytest.raises(PaiementInvalide):
        enregistrer_paiement(d, "1000.01")
    assert len(d.paiements) == 0


def test_reference_paiement_unique(app):
    d = creer_dossier()
    enregistrer_paiement(d, "100", reference="R1")
    with pytest.raises(PaiementInvalide):
        enregistrer_paiement(d, "100", reference="R1")
