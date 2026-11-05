from datetime import datetime
import re

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
    # Compteur d'échecs de connexion (anti brute-force simple)
    echecs_connexion = db.Column(db.Integer, nullable=False, default=0)
    verrouille_jusqu_a = db.Column(db.DateTime, nullable=True)

    ROLES = ("admin", "agent", "consultation")
    MIN_PASSWORD_LENGTH = 12

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.actif

    def est_verrouille(self):
        """True si le compte est temporairement verrouillé après trop d'échecs."""
        if self.verrouille_jusqu_a is None:
            return False
        return datetime.utcnow() < self.verrouille_jusqu_a

    def enregistrer_echec_connexion(self, max_echecs=5, duree_minutes=15):
        """Incrémente les échecs et verrouille si le seuil est atteint."""
        from datetime import timedelta
        self.echecs_connexion = (self.echecs_connexion or 0) + 1
        if self.echecs_connexion >= max_echecs:
            self.verrouille_jusqu_a = datetime.utcnow() + timedelta(minutes=duree_minutes)
            self.echecs_connexion = 0

    def reinitialiser_echecs(self):
        self.echecs_connexion = 0
        self.verrouille_jusqu_a = None

    @staticmethod
    def valider_mot_de_passe(password):
        """
        Valide la politique de mot de passe.
        Retourne (ok: bool, message: str).
        """
        if not password or len(password) < User.MIN_PASSWORD_LENGTH:
            return False, f"Le mot de passe doit contenir au moins {User.MIN_PASSWORD_LENGTH} caractères."
        if not re.search(r"[A-Z]", password):
            return False, "Le mot de passe doit contenir au moins une majuscule."
        if not re.search(r"[a-z]", password):
            return False, "Le mot de passe doit contenir au moins une minuscule."
        if not re.search(r"\d", password):
            return False, "Le mot de passe doit contenir au moins un chiffre."
        return True, ""

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
