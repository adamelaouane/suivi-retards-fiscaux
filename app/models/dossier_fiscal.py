from datetime import date, datetime
from decimal import Decimal
from app.extensions import db


class DossierFiscal(db.Model):
    __tablename__ = "dossiers_fiscaux"

    id = db.Column(db.Integer, primary_key=True)

    numero_dossier = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )

    contribuable_id = db.Column(
        db.Integer,
        db.ForeignKey("contribuables.id"),
        nullable=False,
        index=True
    )

    type_taxe_id = db.Column(
        db.Integer,
        db.ForeignKey("types_taxes.id"),
        nullable=False,
        index=True
    )

    annee_fiscale = db.Column(
        db.Integer,
        nullable=False,
        index=True
    )

    date_limite = db.Column(db.Date, nullable=False)

    montant_exigible = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    observations = db.Column(db.Text, nullable=True)

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    date_modification = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    contribuable = db.relationship(
        "Contribuable",
        back_populates="dossiers"
    )

    type_taxe = db.relationship(
        "TypeTaxe",
        back_populates="dossiers"
    )

    paiements = db.relationship(
        "Paiement",
        back_populates="dossier",
        cascade="all, delete-orphan",
        order_by="Paiement.date_paiement"
    )

    relances = db.relationship(
        "Relance",
        back_populates="dossier",
        cascade="all, delete-orphan",
        order_by="Relance.date_tentative.desc()"
    )

    @property
    def montant_paye(self):
        return sum(
            (paiement.montant for paiement in self.paiements if getattr(paiement, "statut", "VALIDE") == "VALIDE"),
            Decimal("0.00")
        )

    @property
    def montant_restant(self):
        restant = Decimal(self.montant_exigible) - self.montant_paye
        return max(restant, Decimal("0.00"))

    @property
    def statut(self):
        if self.montant_restant == Decimal("0.00"):
            return "PAYE"

        if self.montant_paye > Decimal("0.00"):
            return "PARTIELLEMENT_PAYE"

        return "IMPAYE"

    @property
    def en_retard(self):
        return self.date_limite < date.today() and self.montant_restant > Decimal("0.00")

    @property
    def jours_retard(self):
        if self.montant_restant <= Decimal("0.00"):
            return 0

        return max((date.today() - self.date_limite).days, 0)

    def __repr__(self):
        return f"<DossierFiscal {self.numero_dossier}>"
