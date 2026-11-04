import pytest


@pytest.mark.parametrize("url", [
    "/",
    "/suivi-impayes/",
    "/recherche/",
    "/synthese/",
    "/rapports/",
    "/importation/",
    "/rapports/export/excel",
    "/rapports/export/pdf",
    "/rapports/export/excel?filtre=impayes",
    "/rapports/export/pdf?filtre=retard",
    "/contribuables/",
    "/contribuables/nouveau",
    "/types-taxes/",
    "/types-taxes/nouveau",
    "/dossiers/nouveau",
    "/parametres/",
])
def test_pages_vides_ne_plantent_pas(app, url):
    assert app.test_client().get(url).status_code == 200
