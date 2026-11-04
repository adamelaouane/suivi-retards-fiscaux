from datetime import datetime

from app.extensions import db


class Paiement(db.Model):
    __tablename__ = "paiements"

    id = db.Column(db.Integer, primary_key=True)

    dossier_id = db.Column(
        db.Integer,
        db.ForeignKey("dossiers_fiscaux.id"),
        nullable=False,
        index=True
    )

    montant = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    date_paiement = db.Column(
        db.Date,
        nullable=False
    )

    reference = db.Column(
        db.String(100),
        unique=True,
        nullable=True
    )

    observations = db.Column(db.Text, nullable=True)

    statut = db.Column(
        db.String(20),
        default="VALIDE",
        nullable=False
    )

    motif_annulation = db.Column(
        db.Text,
        nullable=True
    )

    date_enregistrement = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    dossier = db.relationship(
        "DossierFiscal",
        back_populates="paiements"
    )

    def __repr__(self):
        return f"<Paiement {self.id}: {self.montant} ({self.statut})>"
