import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "AUTH_DISABLED": True,  # Les tests historiques restent centrés sur les fonctions métier.
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
