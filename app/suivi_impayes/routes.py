from flask import Blueprint, render_template, request
from app.suivi_impayes.services import filtrer_dossiers_impayes

suivi_impayes_bp = Blueprint(
    "suivi_impayes",
    __name__,
    url_prefix="/suivi-impayes",
)


@suivi_impayes_bp.route("/")
def index():
    query = request.args.get("q", "").strip()
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

    resultat = filtrer_dossiers_impayes(query=query, page=page)

    return render_template(
        "suivi_impayes/index.html",
        dossiers=resultat["dossiers"],
        query=query,
        stats=resultat["stats"],
        pagination=resultat["pagination"],
    )
