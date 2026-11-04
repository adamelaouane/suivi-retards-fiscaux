
from app.extensions import db


class TypeTaxe(db.Model):
    __tablename__ = "types_taxes"

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    libelle = db.Column(
        db.String(120),
        nullable=False
    )

    description = db.Column(db.Text, nullable=True)

    actif = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    dossiers = db.relationship(
        "DossierFiscal",
        back_populates="type_taxe",
        lazy=True
    )

    def __repr__(self):
        return f"<TypeTaxe {self.code}>"
