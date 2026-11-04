from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    nom_complet = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="consultation")
    actif = db.Column(db.Boolean, nullable=False, default=True)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    derniere_connexion = db.Column(db.DateTime, nullable=True)

    ROLES = ("admin", "agent", "consultation")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.actif

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
