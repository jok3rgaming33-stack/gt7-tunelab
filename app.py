#!/usr/bin/env python3
"""GT7 TuneLab — serveur local."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

from engine.catalog import CAR_TYPES, CATEGORIES, DRIVETRAINS, PARTS, TIERS, TIRE_COMPOUNDS, WEATHER
from engine.database import Database
from engine.recommend import recommend, suggest_cars

ROOT = Path(__file__).resolve().parent
app = Flask(
    __name__,
    static_folder=str(ROOT / "public" / "static"),
    static_url_path="/static",
    template_folder=str(ROOT / "templates"),
)
db = Database(ROOT / "data")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/meta")
def meta():
    return jsonify({
        "categories": CATEGORIES,
        "car_types": CAR_TYPES,
        "drivetrains": DRIVETRAINS,
        "tires": TIRE_COMPOUNDS,
        "weather": WEATHER,
        "tiers": TIERS,
        "counts": {"cars": len(db.cars), "tracks": len(db.tracks), "parts": len(PARTS)},
    })


@app.get("/api/cars")
def cars():
    q = request.args.get("q", "")
    category = request.args.get("category") or None
    drivetrain = request.args.get("drivetrain") or None
    car_type = request.args.get("car_type") or None
    has_swap = request.args.get("has_swap")
    has_swap = True if has_swap in ("1", "true", "yes") else None
    limit = min(int(request.args.get("limit") or 60), 200)
    hits = db.search_cars(q=q, category=category, drivetrain=drivetrain, car_type=car_type, has_swap=has_swap, limit=limit)
    return jsonify(hits)


@app.get("/api/cars/<int:cid>")
def car_one(cid):
    c = db.cars_by_id.get(cid)
    if not c:
        return jsonify({"error": "voiture inconnue"}), 404
    return jsonify(c)


@app.get("/api/tracks")
def tracks():
    q = request.args.get("q", "")
    limit = min(int(request.args.get("limit") or 80), 200)
    return jsonify(db.search_tracks(q=q, limit=limit))


@app.get("/api/tracks/<int:tid>")
def track_one(tid):
    t = db.tracks_by_id.get(tid)
    if not t:
        return jsonify({"error": "circuit inconnu"}), 404
    return jsonify(t)


@app.get("/api/catalog")
def catalog():
    return jsonify({"tiers": TIERS, "parts": PARTS})


@app.post("/api/tune")
def tune():
    body = request.get_json(force=True) or {}
    car_id = body.get("car_id")
    track_id = body.get("track_id")
    if not car_id or not track_id:
        return jsonify({"error": "Choisis une voiture et un circuit."}), 400
    car = db.cars_by_id.get(int(car_id))
    track = db.tracks_by_id.get(int(track_id))
    if not car:
        return jsonify({"error": "Voiture introuvable."}), 404
    if not track:
        return jsonify({"error": "Circuit introuvable."}), 404
    result = recommend(car, track, body)
    return jsonify(result)


@app.post("/api/suggest")
def suggest():
    body = request.get_json(force=True) or {}
    track_id = body.get("track_id")
    if not track_id:
        return jsonify({"error": "Choisis d'abord un circuit."}), 400
    track = db.tracks_by_id.get(int(track_id))
    if not track:
        return jsonify({"error": "Circuit introuvable."}), 404
    cars = suggest_cars(db, track, body, limit=int(body.get("limit") or 12))
    return jsonify({"track": track, "cars": cars})


@app.get("/favicon.ico")
def favicon():
    return send_from_directory(ROOT / "public" / "static", "favicon.svg", mimetype="image/svg+xml")


def main():
    print("GT7 TuneLab  →  http://127.0.0.1:8765")
    app.run(host="127.0.0.1", port=8765, debug=False)


if __name__ == "__main__":
    main()
