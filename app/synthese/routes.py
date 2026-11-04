
from flask import Blueprint, render_template

from app.synthese.services import obtenir_statistiques


synthese_bp = Blueprint(
    "synthese",
    __name__,
    url_prefix="/synthese",
)


@synthese_bp.route("/")
def index():
    statistiques = obtenir_statistiques()

    return render_template(
        "synthese/index.html",
        statistiques=statistiques,
    )
