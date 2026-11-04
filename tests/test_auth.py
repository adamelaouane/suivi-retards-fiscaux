from app import create_app
from app.extensions import db
from app.models import User


def make_auth_app():
    app = create_app({
        "TESTING": True,
        "AUTH_DISABLED": False,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        admin = User(username="admin-test", nom_complet="Admin Test", role="admin")
        admin.set_password("MotDePasseTest123!")
        db.session.add(admin)
        db.session.commit()
    return app


def test_pages_redirigent_vers_login_si_non_connecte():
    app = make_auth_app()
    response = app.test_client().get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_login_et_logout():
    app = make_auth_app()
    client = app.test_client()
    response = client.post("/auth/login", data={
        "username": "admin-test",
        "password": "MotDePasseTest123!",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Tableau de bord" in response.data
    response = client.post("/auth/logout", follow_redirects=False)
    assert response.status_code == 302


def test_consultation_ne_peut_pas_modifier():
    app = make_auth_app()
    with app.app_context():
        user = User(username="lecteur", nom_complet="Lecteur", role="consultation")
        user.set_password("MotDePasseTest123!")
        db.session.add(user)
        db.session.commit()
    client = app.test_client()
    client.post("/auth/login", data={"username": "lecteur", "password": "MotDePasseTest123!"})
    response = client.post("/importation/", data={})
    assert response.status_code == 403
