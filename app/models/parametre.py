from datetime import datetime

from app.extensions import db


class Parametre(db.Model):
    __tablename__ = "parametres"

    id = db.Column(db.Integer, primary_key=True)
    cle = db.Column(db.String(50), unique=True, nullable=False, index=True)
    valeur = db.Column(db.Text, nullable=False)
    type_valeur = db.Column(db.String(20), default="str", nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date_modification = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    @property
    def valeur_typee(self):
        val = (self.valeur or "").strip()
        if self.type_valeur == "int":
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0
        if self.type_valeur == "float":
            try:
                return float(val)
            except (ValueError, TypeError):
                return 0.0
        if self.type_valeur == "bool":
            return val.lower() in ("true", "1", "yes", "oui", "t", "y")
        return self.valeur

    @classmethod
    def get_valeur(cls, cle, default=None):
        """Retourne la valeur typée; les erreurs DB ne sont pas masquées."""
        param = cls.query.filter_by(cle=cle).first()
        return param.valeur_typee if param is not None else default

    @classmethod
    def set_valeur(cls, cle, valeur, description=None, type_valeur=None):
        param = cls.query.filter_by(cle=cle).first()
        if type_valeur is None:
            if isinstance(valeur, bool):
                type_valeur = "bool"
            elif isinstance(valeur, int):
                type_valeur = "int"
            elif isinstance(valeur, float):
                type_valeur = "float"
            else:
                type_valeur = "str"

        if param is None:
            param = cls(
                cle=cle,
                valeur=str(valeur),
                type_valeur=type_valeur,
                description=description,
            )
            db.session.add(param)
        else:
            param.valeur = str(valeur)
            param.type_valeur = type_valeur
            if description is not None:
                param.description = description
        return param

    @classmethod
    def initialiser_defauts(cls):
        """Ajoute les paramètres absents sans valider la transaction.

        L'appelant reste responsable du commit/rollback.
        """
        defaults = [
            ("seuil_retard_significatif", "30", "int", "Seuil de retard significatif (jours)"),
            ("seuil_retard_critique", "90", "int", "Seuil de retard critique (jours)"),
            ("lignes_par_page", "20", "int", "Nombre de lignes par page pour les listes"),
            ("nom_organisme", "Direction Générale des Impôts", "str", "Nom de l'organisme fiscal"),
        ]
        crees = 0
        for cle, valeur, type_valeur, description in defaults:
            if cls.query.filter_by(cle=cle).first() is None:
                db.session.add(cls(
                    cle=cle,
                    valeur=valeur,
                    type_valeur=type_valeur,
                    description=description,
                ))
                crees += 1
        return crees

    def __repr__(self):
        return f"<Parametre {self.cle}={self.valeur}>"
