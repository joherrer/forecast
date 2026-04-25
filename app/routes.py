from datetime import datetime, timedelta, timezone

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from .data import spot_order, spot_slugs, spots
from .extensions import db
from .helpers import build_forecast_rows, get_conditions_content, get_forecast_info, login_required
from .models import Favorites, Users


routes_bp = Blueprint("routes", __name__)


@routes_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@routes_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("routes.index"))
        return render_template("login.html")

    username = (request.form.get("username") or "").strip()
    if not username:
        flash("Must provide username", "warning")
        return redirect(url_for("routes.login"))

    password = request.form.get("password")
    if not password:
        flash("Must provide password", "warning")
        return redirect(url_for("routes.login"))

    user = Users.query.filter_by(username=username).first()
    password_matches = user is not None and check_password_hash(user.hash, password)

    if not password_matches:
        flash("Invalid username or password", "warning")
        return redirect(url_for("routes.login"))

    session["user_id"] = user.id
    flash("Logged in successfully", "success")
    return redirect(url_for("routes.index"))


@routes_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("routes.index"))
        return render_template("register.html")

    username = (request.form.get("username") or "").strip()
    if not username:
        flash("Must provide username", "warning")
        return redirect(url_for("routes.register"))

    password = request.form.get("password")
    if not password:
        flash("Must provide password", "warning")
        return redirect(url_for("routes.register"))

    confirmation = request.form.get("confirmation")
    if not confirmation:
        flash("Must confirm password", "warning")
        return redirect(url_for("routes.register"))

    if password != confirmation:
        flash("Passwords do not match", "warning")
        return redirect(url_for("routes.register"))

    user = Users.query.filter_by(username=username).first()
    if user:
        flash("Username already exists", "warning")
        return redirect(url_for("routes.register"))

    password_hashed = generate_password_hash(password)
    new_user = Users(username=username, hash=password_hashed)
    db.session.add(new_user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Username already exists", "warning")
        return redirect(url_for("routes.register"))

    session["user_id"] = new_user.id
    flash("Account created successfully!", "success")
    return redirect(url_for("routes.index"))


@routes_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("routes.index"))


@routes_bp.route("/spots", methods=["GET"])
def spots_route():
    return render_template("spots.html", spots=spots)


@routes_bp.route("/spots/<spot_route>", methods=["GET"])
def spot_forecast(spot_route):
    # Only allow forecast pages for slugs derived from the known spot list.
    spot_name = spot_slugs.get(spot_route.lower())
    spot = spots.get(spot_name) if spot_name else None
    spot_id = spot["id"] if spot else None
    if not spot_id:
        flash("Spot not found", "warning")
        return redirect(url_for("routes.spots_route"))

    wave = get_forecast_info("wave", spot_id)
    wind = get_forecast_info("wind", spot_id)
    weather = get_forecast_info("weather", spot_id)
    conditions = get_forecast_info("conditions", spot_id)
    conditions_content = get_conditions_content(conditions)
    has_forecast_data = bool((wave or {}).get("data", {}).get("wave"))
    if has_forecast_data:
        rows = build_forecast_rows(
            wave,
            wind,
            weather,
            overview_hours=[6, 12, 18],
            forecast_hours=[6, 9, 12, 15, 18],
        )
        current_date = datetime.fromtimestamp(
            wave["data"]["wave"][0]["timestamp"],
            tz=timezone(timedelta(hours=wave["associated"]["utcOffset"])),
        ).strftime("%a, %d %B %Y")
    else:
        rows = {"overview_rows": [], "forecast_rows": []}
        current_date = ""

    return render_template(
        "forecast.html",
        spot_name=spot_name,
        current_date=current_date,
        headline=conditions_content["headline"],
        observation_text=conditions_content["observation_text"],
        has_forecast_data=has_forecast_data,
        overview_rows=rows["overview_rows"],
        forecast_rows=rows["forecast_rows"],
    )


@routes_bp.route("/favorites", methods=["GET", "POST"])
@login_required
def favorites():
    user_id = session["user_id"]
    if request.method == "POST":
        # Handle add/remove actions from the same form endpoint.
        action = request.form.get("action")

        if action == "add":
            spot = (request.form.get("spot") or "").strip()
            if not spot:
                flash("Must select spot to add", "warning")
                return redirect(url_for("routes.favorites"))

            if spot not in spots:
                flash("Selected spot is invalid", "warning")
                return redirect(url_for("routes.favorites"))

            existing_favorite = Favorites.query.filter_by(user_id=user_id, spot=spot).first()
            if existing_favorite:
                flash("Spot already exists", "warning")
                return redirect(url_for("routes.favorites"))

            new_favorite = Favorites(user_id=user_id, spot=spot)
            db.session.add(new_favorite)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Spot already exists", "warning")
                return redirect(url_for("routes.favorites"))
            flash("Spot added to favorites", "success")
            return redirect(url_for("routes.favorites"))

        if action == "remove":
            spot = (request.form.get("spot") or "").strip()
            if not spot:
                flash("Must select spot to remove", "warning")
                return redirect(url_for("routes.favorites"))

            if spot not in spots:
                flash("Selected spot is invalid", "warning")
                return redirect(url_for("routes.favorites"))

            favorite_to_remove = Favorites.query.filter_by(user_id=user_id, spot=spot).first()
            if not favorite_to_remove:
                flash("Spot not found in favorites", "warning")
                return redirect(url_for("routes.favorites"))

            db.session.delete(favorite_to_remove)
            db.session.commit()
            flash("Spot removed from favorites", "success")
            return redirect(url_for("routes.favorites"))

        flash("Invalid action.", "warning")
        return redirect(url_for("routes.favorites"))

    favorites_table = Favorites.query.filter_by(user_id=user_id).all()
    spots_fav = [favorite.spot for favorite in favorites_table if favorite.spot in spots]
    spots_fav.sort(key=lambda favorite_spot: spot_order[favorite_spot])
    return render_template("favorites.html", spots=spots, spots_fav=spots_fav)
