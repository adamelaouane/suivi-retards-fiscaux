
from datetime import datetime

from app.extensions import db


class Relance(db.Model):
    __tablename__ = "relances"

    id = db.Column(db.Integer, primary_key=True)

    dossier_id = db.Column(
        db.Integer,
        db.ForeignKey("dossiers_fiscaux.id"),
        nullable=False,
        index=True
    )

    canal = db.Column(
        db.String(30),
        nullable=False,
        default="MANUEL"
    )

    message = db.Column(db.Text, nullable=False)

    date_tentative = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    statut = db.Column(
        db.String(30),
        nullable=False,
        default="ENREGISTREE"
    )

    reference_externe = db.Column(
        db.String(100),
        nullable=True
    )

    erreur = db.Column(db.Text, nullable=True)

    dossier = db.relationship(
        "DossierFiscal",
        back_populates="relances"
    )

    def __repr__(self):
        return f"<Relance {self.id}: {self.statut}>"
