
from datetime import datetime

from app.extensions import db


class Contribuable(db.Model):
    __tablename__ = "contribuables"

    id = db.Column(db.Integer, primary_key=True)

    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False, default="")

    cin = db.Column(db.String(20), unique=True, nullable=True)

    identifiant_fiscal = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    telephone = db.Column(db.String(20), nullable=True)

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Un contribuable peut avoir plusieurs dossiers fiscaux.
    dossiers = db.relationship(
        "DossierFiscal",
        back_populates="contribuable",
        lazy=True
    )

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip()

    def __repr__(self):
        return f"<Contribuable {self.identifiant_fiscal}>"
