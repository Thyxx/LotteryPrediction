from __future__ import annotations

from math import ceil
from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from .data_fetcher import FetchError, update_all_draws
from .database import get_session
from .models import EuroMillionsDraw, LotoDraw
from .predictions import generate_euromillions_predictions, generate_loto_predictions

bp = Blueprint("main", __name__)


def _paginate_query(query, page: int, per_page: int):
    total = query.count()
    pages = max(ceil(total / per_page), 1) if total else 1
    page = max(1, min(page, pages))
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total, pages, page


@bp.route("/")
def index():
    session = get_session()
    try:
        loto_latest = (
            session.query(LotoDraw)
            .order_by(LotoDraw.draw_date.desc(), LotoDraw.draw_number.desc())
            .limit(10)
            .all()
        )
        euromillions_latest = (
            session.query(EuroMillionsDraw)
            .order_by(EuroMillionsDraw.draw_date.desc(), EuroMillionsDraw.draw_number.desc())
            .limit(10)
            .all()
        )

        loto_predictions = generate_loto_predictions(session)
        euromillions_predictions = generate_euromillions_predictions(session)

        counts = {
            "loto": session.query(func.count(LotoDraw.id)).scalar() or 0,
            "euromillions": session.query(func.count(EuroMillionsDraw.id)).scalar() or 0,
        }
        last_update = max(filter(None, [
            session.query(func.max(LotoDraw.updated_at)).scalar(),
            session.query(func.max(EuroMillionsDraw.updated_at)).scalar(),
        ]), default=None)
    finally:
        session.close()

    return render_template(
        "index.html",
        loto_latest=loto_latest,
        euromillions_latest=euromillions_latest,
        loto_predictions=loto_predictions,
        euromillions_predictions=euromillions_predictions,
        counts=counts,
        last_update=last_update,
    )


@bp.route("/update", methods=["POST"])
def update_data():
    session = get_session()
    try:
        results = update_all_draws(session)
        flash(
            f"Mise à jour terminée : {results['loto']} nouveaux tirages Loto, "
            f"{results['euromillions']} nouveaux tirages EuroMillions.",
            "success",
        )
    except FetchError as exc:
        session.rollback()
        flash(f"Impossible de récupérer les données : {exc}", "danger")
    except Exception as exc:  # pragma: no cover - defensive programming
        session.rollback()
        flash(f"Erreur inattendue : {exc}", "danger")
    finally:
        session.close()
    return redirect(url_for("main.index"))


@bp.route("/historique/<string:game>")
def history(game: str):
    per_page = 30
    page = request.args.get("page", default=1, type=int)
    session = get_session()
    try:
        if game == "loto":
            query = session.query(LotoDraw).order_by(
                LotoDraw.draw_date.desc(), LotoDraw.draw_number.desc()
            )
            label = "Loto"
            last_update = session.query(func.max(LotoDraw.updated_at)).scalar()
        elif game == "euromillions":
            query = session.query(EuroMillionsDraw).order_by(
                EuroMillionsDraw.draw_date.desc(), EuroMillionsDraw.draw_number.desc()
            )
            label = "EuroMillions"
            last_update = session.query(func.max(EuroMillionsDraw.updated_at)).scalar()
        else:
            flash("Jeu inconnu demandé.", "warning")
            return redirect(url_for("main.index"))

        items, total, pages, current_page = _paginate_query(query, page, per_page)
    finally:
        session.close()

    return render_template(
        "history.html",
        game=game,
        label=label,
        items=items,
        total=total,
        pages=pages,
        current_page=current_page,
        per_page=per_page,
        last_update=last_update,
    )
