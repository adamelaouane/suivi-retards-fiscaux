from datetime import datetime
from app.extensions import db


class ImportBatch(db.Model):
    __tablename__ = "import_batches"

    id = db.Column(db.Integer, primary_key=True)

    nom_fichier = db.Column(db.String(255), nullable=False)

    type_fichier = db.Column(db.String(20), nullable=False)

    nombre_lignes = db.Column(db.Integer, default=0)

    nombre_importes = db.Column(db.Integer, default=0)

    nombre_erreurs = db.Column(db.Integer, default=0)

    statut = db.Column(db.String(30), default="EN_ATTENTE")

    date_importation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    details_erreurs = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<ImportBatch {self.nom_fichier}>"