from datetime import datetime

from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)

    date_action = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    action = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )

    objet = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )

    reference_objet = db.Column(
        db.String(100),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    utilisateur = db.Column(
        db.String(100),
        default="Système",
        nullable=True
    )

    ip_adresse = db.Column(
        db.String(50),
        nullable=True
    )

    def __repr__(self):
        return f"<AuditLog {self.action} {self.objet} ({self.date_action})>"
