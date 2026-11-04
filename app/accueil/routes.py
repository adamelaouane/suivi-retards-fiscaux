from flask import Blueprint, render_template

from app.accueil.services import get_dashboard_stats, get_recent_activities
from app.models import DossierFiscal


accueil_bp = Blueprint("accueil", __name__)


@accueil_bp.route("/")
def index():
    dossiers = DossierFiscal.query.order_by(
        DossierFiscal.date_creation.desc()
    ).all()

    return render_template(
        "accueil/index.html",
        stats=get_dashboard_stats(),
        activites=get_recent_activities(),
        dossiers=dossiers,
    )
