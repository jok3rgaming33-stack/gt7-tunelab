"""Feuille GT7 — unités et champs IDENTIQUES au jeu (Praiano / tes feuilles Nürburgring).

GT7 n'a PAS de constante de ressort ni d'amortos 1–10 à 4 voies.
Écran réel :
  hauteur mm · barre 1–10 · compression % · expansion % · fréquence Hz
  carrossage négatif (affichage positif) · pincement IN/OUT
  LSD avant ET arrière · appui (échelle selon la caisse)
"""

from __future__ import annotations

from copy import deepcopy

from .gearing import build_gearing
from .symptoms import SYMPTOMS_BY_ID

PILOTING = [
    {
        "id": "controller",
        "label": "Contrôleur",
        "options": [
            {"id": "pad", "label": "Manette"},
            {"id": "wheel", "label": "Volant"},
        ],
        "default": "pad",
    },
    {
        "id": "level",
        "label": "Niveau",
        "options": [
            {"id": "beginner", "label": "Débutant"},
            {"id": "intermediate", "label": "Confirmé"},
            {"id": "expert", "label": "Expert"},
        ],
        "default": "intermediate",
    },
    {
        "id": "attack",
        "label": "Attaque des appuis",
        "options": [
            {"id": "smooth", "label": "Fluide"},
            {"id": "committed", "label": "Engagé"},
            {"id": "aggressive", "label": "Agressif"},
        ],
        "default": "committed",
    },
    {
        "id": "braking",
        "label": "Freinage",
        "options": [
            {"id": "conservative", "label": "Tôt / sécurisé"},
            {"id": "trail", "label": "Trail-brake"},
            {"id": "late", "label": "Tardif"},
        ],
        "default": "trail",
    },
    {
        "id": "throttle",
        "label": "Remise des gaz",
        "options": [
            {"id": "progressive", "label": "Progressive"},
            {"id": "early", "label": "Tôt / à fond"},
        ],
        "default": "progressive",
    },
    {
        "id": "rotation",
        "label": "Rotation voulue",
        "options": [
            {"id": "stable", "label": "Stable"},
            {"id": "neutral", "label": "Neutre"},
            {"id": "pointy", "label": "Pointue"},
        ],
        "default": "neutral",
    },
]


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _i(v, lo, hi):
    return int(round(_clamp(v, lo, hi)))


def _f(v, lo, hi, nd=2):
    return round(_clamp(v, lo, hi), nd)


def car_band(car: dict) -> str:
    cat = (car.get("category") or "Road")
    name = (car.get("name") or car.get("full_name") or "").lower()
    if cat == "Super Formula" or "super formula" in name or name.startswith("sf19") or name.startswith("sf23"):
        return "sf"
    if cat == "Kart" or "kart" in name:
        return "kart"
    if cat == "Gr.1" or "lmp" in name or "919 hybrid" in name or "ts050" in name or "gr010" in name:
        return "proto"
    if cat in ("Gr.2", "Gr.3") or "gt500" in name or "gt3" in name:
        return "gt"
    if cat in ("Gr.4", "Gr.B"):
        return "gt4"
    if car.get("car_type") in ("Hypercar", "Vision Gran Turismo") and "gr." not in name:
        return "hyper"
    return "road"


def is_bumpy(track: dict, profile: dict) -> bool:
    n = (track.get("name") or "").lower()
    return any(k in n for k in (
        "nordschleife", "nurburgring", "nürburgring", "green hell",
        "panorama", "eiger", "trial mountain", "horse thief", "sardegna - wind",
    )) or profile.get("hills") == "mountain"


def build_sheet(car, track, profile, drivetrain, tire, style, symptoms, pilot, cl, pp_limit, weather, has_gt_auto):
    """Construit une feuille aux unités GT7, calée Praiano + tes tunes Green Hell."""
    band = car_band(car)
    layout = profile.get("layout") or "mixed"
    surface = profile.get("surface") or "tarmac"
    bumpy = is_bumpy(track, profile)
    symptoms = symptoms or []
    pilot = pilot or {}
    name = (track.get("name") or "").lower()

    # ── Bases par classe (valeurs relevées / Praiano / tes 919 & SF23) ─
    # ride mm, arb 1-10, comp 20-40, exp 30-50, nf Hz,
    # camber MAGNITUDE (écran FR « négatif »), toe F=OUT R=IN
    # lsd F/R init-acc-dec, aero, vmax
    if band == "sf":
        n = dict(ride_f=25, ride_r=55, arb_f=7, arb_r=5,
                 comp_f=32, comp_r=35, exp_f=47, exp_r=47,
                 nf_f=5.90, nf_r=5.90, camber_f=3.0, camber_r=1.5,
                 toe_f=0.20, toe_r=0.10,
                 lsd_fi=0, lsd_fa=0, lsd_fd=0,
                 lsd_ri=15, lsd_ra=15, lsd_rd=40,
                 split_f=0, aero_f=1250, aero_r=1600, vmax=360)
    elif band == "proto":
        n = dict(ride_f=50, ride_r=70, arb_f=5, arb_r=6,
                 comp_f=28, comp_r=30, exp_f=38, exp_r=40,
                 nf_f=4.10, nf_r=4.00, camber_f=3.2, camber_r=2.0,
                 toe_f=0.20, toe_r=0.20,
                 lsd_fi=5, lsd_fa=5, lsd_fd=5,
                 lsd_ri=15, lsd_ra=32, lsd_rd=25,
                 split_f=35, aero_f=1000, aero_r=1500, vmax=310)
    elif band == "gt":
        n = dict(ride_f=58, ride_r=72, arb_f=4, arb_r=5,
                 comp_f=26, comp_r=28, exp_f=36, exp_r=38,
                 nf_f=3.45, nf_r=3.35, camber_f=2.8, camber_r=1.8,
                 toe_f=0.15, toe_r=0.18,
                 lsd_fi=5, lsd_fa=8, lsd_fd=8,
                 lsd_ri=10, lsd_ra=22, lsd_rd=24,
                 split_f=32, aero_f=280, aero_r=420, vmax=290)
    elif band == "gt4":
        n = dict(ride_f=72, ride_r=86, arb_f=4, arb_r=4,
                 comp_f=25, comp_r=27, exp_f=35, exp_r=37,
                 nf_f=2.95, nf_r=2.85, camber_f=2.4, camber_r=1.6,
                 toe_f=0.12, toe_r=0.15,
                 lsd_fi=5, lsd_fa=8, lsd_fd=8,
                 lsd_ri=10, lsd_ra=20, lsd_rd=22,
                 split_f=40, aero_f=120, aero_r=180, vmax=270)
    elif band == "hyper":
        n = dict(ride_f=78, ride_r=90, arb_f=4, arb_r=5,
                 comp_f=26, comp_r=28, exp_f=36, exp_r=38,
                 nf_f=2.85, nf_r=2.75, camber_f=2.6, camber_r=1.7,
                 toe_f=0.12, toe_r=0.22,
                 lsd_fi=5, lsd_fa=8, lsd_fd=8,
                 lsd_ri=12, lsd_ra=24, lsd_rd=26,
                 split_f=35, aero_f=90, aero_r=160, vmax=320)
    elif band == "kart":
        n = dict(ride_f=20, ride_r=22, arb_f=3, arb_r=3,
                 comp_f=24, comp_r=24, exp_f=34, exp_r=34,
                 nf_f=4.50, nf_r=4.50, camber_f=1.5, camber_r=1.0,
                 toe_f=0.05, toe_r=0.05,
                 lsd_fi=5, lsd_fa=5, lsd_fd=5,
                 lsd_ri=8, lsd_ra=12, lsd_rd=12,
                 split_f=50, aero_f=0, aero_r=0, vmax=140)
    else:  # road — Praiano: bas + rake, NF moyenne, LSD initial BAS, toe AR IN
        n = dict(ride_f=88, ride_r=98, arb_f=3, arb_r=4,
                 comp_f=24, comp_r=26, exp_f=34, exp_r=36,
                 nf_f=2.45, nf_r=2.55, camber_f=2.2, camber_r=1.4,
                 toe_f=0.10, toe_r=0.18,
                 lsd_fi=5, lsd_fa=8, lsd_fd=8,
                 lsd_ri=8, lsd_ra=18, lsd_rd=20,
                 split_f=38, aero_f=55, aero_r=110, vmax=265)

    n.update(brake_force=5, brake_bal=-2, abs=1, tcs=1, asm=0, countersteer=1,
             ecu=100, ballast_kg=0, ballast_pos=0)

    # Traction — Praiano : LSD bas, Accél. = confort sortie, Décél. = entrée
    if drivetrain == "FF":
        n.update(arb_f=2, arb_r=5, camber_f=2.6, toe_r=0.08, toe_f=0.15,
                 lsd_ri=6, lsd_ra=16, lsd_rd=12, split_f=100, brake_bal=-1)
    elif drivetrain == "MR":
        if band not in ("sf", "proto"):
            n.update(arb_f=max(n["arb_f"], 5), arb_r=min(n["arb_r"], 5),
                     lsd_rd=max(n["lsd_rd"], 24))
        if band == "sf":
            n.update(split_f=0, lsd_fi=0, lsd_fa=0, lsd_fd=0)
    elif drivetrain == "RR":
        n.update(camber_r=max(n["camber_r"], 1.8), lsd_rd=max(n["lsd_rd"], 22), toe_r=0.20)
    elif drivetrain == "4WD":
        if band in ("road", "gt4", "hyper", "gt"):
            n.update(split_f=35, lsd_fi=5, lsd_fa=8, lsd_fd=8,
                     lsd_ri=12, lsd_ra=28, lsd_rd=22)
        if surface in ("dirt", "snow"):
            n["split_f"] = 50
    else:  # FR
        if band in ("road", "gt4", "hyper"):
            n.update(lsd_fi=5, lsd_fa=5, lsd_fd=5)

    # Surface
    if surface in ("dirt", "snow"):
        n.update(ride_f=n["ride_f"] + 28, ride_r=n["ride_r"] + 26,
                 nf_f=max(1.80, n["nf_f"] - 0.70), nf_r=max(1.70, n["nf_r"] - 0.70),
                 comp_f=22, comp_r=24, exp_f=32, exp_r=34,
                 arb_f=2, arb_r=2, camber_f=1.2, camber_r=0.8,
                 lsd_ra=14, lsd_rd=12, aero_f=0, aero_r=0,
                 tcs=3 if surface == "dirt" else 4, abs=2, brake_force=4)

    # Layout — ne PAS couper l'appui des proto/SF (tes 919/SF23 gardent 1000–1600 au Nürburgring)
    if layout == "high_speed" and surface == "tarmac" and band in ("road", "gt4", "hyper"):
        n["aero_f"] = int(n["aero_f"] * 0.88)
        n["aero_r"] = int(n["aero_r"] * 0.92)
        n["vmax"] += 12
        n["toe_r"] += 0.03
    elif layout == "technical" and surface == "tarmac":
        n["aero_f"] = int(n["aero_f"] * 1.06)
        n["nf_f"] -= 0.06
        n["comp_f"] -= 1
        n["vmax"] -= 12

    # Nürburgring / bosses
    if bumpy and surface == "tarmac":
        if band in ("sf", "proto"):
            n["ride_f"] += 2
            n["ride_r"] += 2
            n["comp_f"] -= 1
            n["comp_r"] -= 1
            n["lsd_rd"] += 2
        else:
            n["ride_f"] += 4
            n["ride_r"] += 5
            n["comp_f"] -= 2
            n["comp_r"] -= 2
            n["exp_f"] -= 1
            n["nf_f"] -= 0.10
            n["nf_r"] -= 0.08
            n["aero_r"] = int(n["aero_r"] * 1.05)
            n["lsd_rd"] += 4
            n["toe_r"] += 0.03

    if profile.get("oval") or "route x" in name:
        n["aero_f"] = min(n["aero_f"], 40) if band == "road" else int(n["aero_f"] * 0.4)
        n["aero_r"] = min(n["aero_r"], 80) if band == "road" else int(n["aero_r"] * 0.45)
        n["vmax"] += 40

    if not has_gt_auto and band == "road":
        n["aero_f"] = 0
        n["aero_r"] = 0

    # Style intention
    if style == "drift":
        n.update(camber_f=0.8, camber_r=1.2, toe_f=0.25, toe_r=-0.08,
                 lsd_ri=8, lsd_ra=48, lsd_rd=28, tcs=0, arb_r=1,
                 aero_f=min(n["aero_f"], 40), aero_r=min(n["aero_r"], 60))
    elif style == "chrono":
        n["tcs"] = 0
        n["abs"] = 1
        n["comp_f"] += 1
        n["nf_f"] += 0.06
    elif style == "stable":
        n["tcs"] = 2
        n["lsd_ra"] -= 3
        n["lsd_rd"] += 4
        n["toe_r"] += 0.05
        n["arb_r"] += 1

    if weather in ("wet", "damp"):
        n["tcs"] += 2
        n["abs"] = max(n["abs"], 2)
        n["aero_f"] = int(n["aero_f"] * 1.08)
        n["aero_r"] = int(n["aero_r"] * 1.10)

    # Pilotage
    ctrl = pilot.get("controller") or "pad"
    level = pilot.get("level") or "intermediate"
    attack = pilot.get("attack") or "committed"
    braking = pilot.get("braking") or "trail"
    throttle = pilot.get("throttle") or "progressive"
    rotation = pilot.get("rotation") or "neutral"

    n["countersteer"] = 1 if ctrl == "pad" else 0
    if ctrl == "wheel":
        n["lsd_ri"] += 1
        n["toe_f"] -= 0.02

    if level == "beginner":
        n["tcs"] = max(n["tcs"], 3)
        n["abs"] = max(n["abs"], 2)
        n["lsd_ra"] -= 4
        n["lsd_rd"] += 5
        n["arb_f"] += 1
    elif level == "expert":
        if style != "drift":
            n["tcs"] = 0
        n["abs"] = 1

    if attack == "smooth":
        n["comp_f"] -= 2
        n["arb_f"] -= 1
        n["nf_f"] -= 0.08
    elif attack == "aggressive":
        n["comp_f"] += 2
        n["arb_f"] += 1
        n["lsd_rd"] += 3
        n["nf_f"] += 0.08

    if braking == "conservative":
        n["brake_force"] = 4
        n["brake_bal"] = -3
        n["abs"] = max(n["abs"], 2)
    elif braking == "late":
        n["brake_force"] = 6
        n["brake_bal"] = -1
        n["comp_f"] += 1
    else:
        n["lsd_rd"] += 2
        n["brake_bal"] = -2

    if throttle == "early":
        n["lsd_ra"] -= 3
        n["tcs"] += 1
        n["split_f"] = min(50, n["split_f"] + 4)
    else:
        n["lsd_ra"] += 1

    if rotation == "stable":
        n["toe_r"] += 0.06
        n["arb_r"] += 1
        n["lsd_rd"] += 3
        n["aero_r"] = int(n["aero_r"] * 1.06)
    elif rotation == "pointy":
        n["toe_f"] += 0.05
        n["toe_r"] -= 0.04
        n["arb_f"] -= 1
        n["ride_r"] += 3
        n["lsd_rd"] -= 3

    # Symptômes — deltas dans l'échelle RÉELLE
    SYMPTOM_DELTAS = {
        "us_entry": {"lsd_rd": -6, "brake_bal": -1, "toe_f": 0.04, "aero_f": 8},
        "us_mid": {"arb_f": -2, "arb_r": 1, "camber_f": 0.3, "ride_f": -2},
        "us_exit": {"lsd_ra": -5, "split_f": -5, "aero_r": -10},
        "os_entry": {"lsd_rd": 6, "lsd_ri": 3, "brake_bal": -1, "toe_r": 0.06, "aero_r": 12},
        "os_mid": {"arb_r": -2, "arb_f": 1, "camber_r": 0.3, "nf_r": 0.08, "aero_r": 12},
        "os_exit": {"lsd_ra": -6, "tcs": 1, "aero_r": 10},
        "os_lift": {"exp_r": 2, "lsd_ri": 3, "arb_r": -1},
        "brake_unstable": {"brake_bal": -1, "brake_force": -1, "abs": 1, "lsd_rd": 4},
        "brake_weak": {"brake_force": 1, "abs": 0},
        "brake_lock_f": {"brake_force": -1, "brake_bal": 1, "abs": 1},
        "brake_dive": {"nf_f": 0.12, "comp_f": 2, "ride_f": 3},
        "spin_exit": {"lsd_ra": 5, "lsd_ri": 2, "tcs": 1},
        "spin_inside": {"lsd_ra": 6, "lsd_ri": 4, "arb_r": 1},
        "launch_slow": {},
        "bottom": {"ride_f": 5, "ride_r": 4, "comp_f": -2},
        "kerb": {"comp_f": -3, "comp_r": -3, "arb_f": -1, "arb_r": -1},
        "bounce": {"exp_f": 2, "exp_r": 3, "comp_f": 1},
        "stiff": {"nf_f": -0.15, "nf_r": -0.12, "arb_f": -1, "comp_f": -2},
        "nervous": {"toe_r": 0.08, "lsd_ri": 3, "aero_r": 10},
        "no_rotate": {"toe_f": 0.06, "toe_r": -0.05, "ride_r": 4, "lsd_rd": -4, "arb_f": -1},
        "squat": {"nf_r": 0.12, "comp_r": 2, "ride_r": 2, "aero_r": 8},
        "hs_us": {"aero_f": 15, "arb_f": -1, "camber_f": 0.2},
        "hs_os": {"aero_r": 18, "aero_f": -8, "toe_r": 0.05, "lsd_ra": -3},
        "hs_wander": {"toe_r": 0.08, "toe_f": -0.03, "aero_f": 6, "aero_r": 10, "arb_f": 1},
        "drag": {"aero_f": -20, "aero_r": -30},
        "heat_inner": {"camber_f": -0.4, "camber_r": -0.3},
        "heat_outer": {"camber_f": 0.4, "camber_r": 0.3},
        "wear_front": {"brake_bal": 1, "brake_force": -1, "aero_f": -10, "aero_r": 8},
        "wear_rear": {"lsd_ra": -4, "tcs": 1, "aero_r": 10},
        "limiter_early": {},
        "limiter_never": {},
        "gear_gap": {},
    }

    for sid in symptoms:
        for key, delta in SYMPTOM_DELTAS.get(sid, {}).items():
            if key in n:
                n[key] = n[key] + delta

    # Clamps GT7
    n["ride_f"] = _i(n["ride_f"], 15, 160)
    n["ride_r"] = _i(n["ride_r"], 15, 165)
    if n["ride_r"] < n["ride_f"]:
        n["ride_r"] = n["ride_f"] + 4  # rake : AR plus haut = rotation (Praiano)
    n["arb_f"] = _i(n["arb_f"], 1, 10)
    n["arb_r"] = _i(n["arb_r"], 1, 10)
    n["comp_f"] = _i(n["comp_f"], 20, 40)
    n["comp_r"] = _i(n["comp_r"], 20, 40)
    n["exp_f"] = _i(n["exp_f"], 30, 50)
    n["exp_r"] = _i(n["exp_r"], 30, 50)
    # expansion toujours ≥ compression (tes feuilles + guides)
    if n["exp_f"] < n["comp_f"] + 6:
        n["exp_f"] = min(50, n["comp_f"] + 10)
    if n["exp_r"] < n["comp_r"] + 6:
        n["exp_r"] = min(50, n["comp_r"] + 10)
    n["nf_f"] = _f(n["nf_f"], 1.20, 7.50, 2)
    n["nf_r"] = _f(n["nf_r"], 1.20, 7.50, 2)
    n["camber_f"] = _f(n["camber_f"], 0.0, 6.0, 1)
    n["camber_r"] = _f(n["camber_r"], 0.0, 6.0, 1)
    n["toe_f"] = _f(n["toe_f"], -0.40, 0.60, 2)
    n["toe_r"] = _f(n["toe_r"], -0.50, 0.80, 2)
    for k in ("lsd_fi", "lsd_fa", "lsd_fd", "lsd_ri", "lsd_ra", "lsd_rd"):
        n[k] = _i(n[k], 0, 60)
    n["split_f"] = _i(n["split_f"], 0, 100)
    n["aero_f"] = _i(n["aero_f"], 0, 2000)
    n["aero_r"] = _i(n["aero_r"], 0, 2000)
    n["brake_force"] = _i(n["brake_force"], 1, 10)
    n["brake_bal"] = _i(n["brake_bal"], -5, 5)
    n["abs"] = _i(n["abs"], 0, 5)
    n["tcs"] = _i(n["tcs"], 0, 5)
    n["countersteer"] = 1 if n["countersteer"] else 0
    n["ecu"] = 100 if not pp_limit else 92
    n["vmax"] = _i(n.get("vmax", 270), 120, 450)

    # Gearing : Vmax feuille prioritaire
    g = build_gearing(track, profile, style, symptoms)
    g = deepcopy(g)
    g["max_speed"] = n["vmax"]
    if bumpy:
        g["max_speed"] = max(g["max_speed"], n["vmax"])

    def toe_f(v):
        side = "OUT" if v >= 0 else "IN"
        return f"{abs(v):.2f}° {side}"

    def toe_r(v):
        # Praiano : IN arrière (valeur positive). Négatif = OUT (rare, FF/4WD)
        side = "IN" if v >= 0 else "OUT"
        return f"{abs(v):.2f}° {side}"

    def bal(v):
        if v == 0:
            return "0"
        if v < 0:
            return f"{v}  (vers l'avant)"
        return f"+{v}  (vers l'arrière)"

    show_front_lsd = drivetrain in ("4WD",) or band in ("proto", "sf", "gt")
    lsd_rows = [
        {"label": "Couple initial", "front": str(n["lsd_fi"]), "rear": str(n["lsd_ri"])},
        {"label": "Sensibilité accélération", "front": str(n["lsd_fa"]), "rear": str(n["lsd_ra"])},
        {"label": "Sensibilité freinage", "front": str(n["lsd_fd"]), "rear": str(n["lsd_rd"])},
    ]
    if drivetrain == "4WD" or band == "sf":
        lsd_rows.append({
            "label": "Répartition centrale",
            "front": f"{n['split_f']}",
            "rear": f"{100 - n['split_f']}",
        })

    blocks = [
        {
            "title": "PNEUS",
            "kind": "single",
            "rows": [{"label": "Compound", "value": tire["name_fr"]}],
        },
        {
            "title": "SUSPENSION",
            "kind": "fr",
            "rows": [
                {"label": "Hauteur de caisse", "front": f"{n['ride_f']} mm", "rear": f"{n['ride_r']} mm"},
                {"label": "Barre anti-roulis", "front": str(n["arb_f"]), "rear": str(n["arb_r"])},
                {"label": "Amort. compression", "front": f"{n['comp_f']} %", "rear": f"{n['comp_r']} %"},
                {"label": "Amort. expansion", "front": f"{n['exp_f']} %", "rear": f"{n['exp_r']} %"},
                {"label": "Fréquence naturelle", "front": f"{n['nf_f']:.2f} Hz", "rear": f"{n['nf_r']:.2f} Hz"},
                {"label": "Carrossage (négatif)", "front": f"{n['camber_f']:.1f}°", "rear": f"{n['camber_r']:.1f}°"},
                {"label": "Pincement", "front": toe_f(n["toe_f"]), "rear": toe_r(n["toe_r"])},
            ],
        },
        {
            "title": "AÉRODYNAMIQUE",
            "kind": "fr",
            "rows": [
                {"label": "Appui", "front": str(n["aero_f"]), "rear": str(n["aero_r"])},
            ],
        },
        {
            "title": "DIFFÉRENTIEL",
            "kind": "fr" if show_front_lsd else "single",
            "rows": lsd_rows if show_front_lsd else [
                {"label": "Couple initial", "value": str(n["lsd_ri"])},
                {"label": "Sensibilité accélération", "value": str(n["lsd_ra"])},
                {"label": "Sensibilité freinage", "value": str(n["lsd_rd"])},
            ],
        },
        {
            "title": "TRANSMISSION",
            "kind": "single",
            "rows": [
                {"label": "Étalonnage auto · Vmax", "value": f"{g['max_speed']} km/h"},
                {"label": "Pont", "value": f"{g['final_drive']:.3f}"},
            ] + [{"label": f"{r['gear']}e", "value": f"{r['ratio']:.3f}"} for r in g["ratios"]],
        },
        {
            "title": "FREINS",
            "kind": "single",
            "rows": [
                {"label": "Équilibre avant/arrière", "value": bal(n["brake_bal"])},
            ],
        },
        {
            "title": "AIDES",
            "kind": "single",
            "rows": [
                {"label": "TCS", "value": str(n["tcs"])},
                {"label": "ABS", "value": str(n["abs"])},
                {"label": "ASM", "value": "OFF"},
                {"label": "Contre-braquage auto", "value": "ON" if n["countersteer"] else "OFF"},
            ],
        },
        {
            "title": "ECU / LEST",
            "kind": "single",
            "rows": [
                {"label": "Puissance ECU", "value": f"{n['ecu']} %"},
                {"label": "Lest", "value": f"{n['ballast_kg']} kg"},
                {"label": "Position du lest", "value": str(n["ballast_pos"])},
            ],
        },
    ]

    diag = []
    for sid in symptoms:
        spec = SYMPTOMS_BY_ID.get(sid)
        if spec:
            diag.append({"symptom": spec["label"], "detail": spec.get("detail") or spec.get("hint") or ""})

    method = (
        "Logique Praiano : d'abord les forts (hauteur, fréquence, carrossage, appui), "
        "puis LSD / pincement / freins, enfin amortos et barres. "
        "Rake (AR plus haut). Compression < expansion. LSD initial BAS. "
        "Pincement AV OUT, AR IN. Unités = écran GT7 (amortos en %, Hz, appui selon la caisse)."
    )
    if bumpy:
        method += " Nürburgring / bosses : +4–5 mm, compression −2, décél. LSD +, un peu plus d'appui AR."

    return {
        "numbers": n,
        "blocks": blocks,
        "gearing": g,
        "band": band,
        "disclaimer": method,
        "diagnostics": {
            "ids": symptoms,
            "labels": [SYMPTOMS_BY_ID[s]["label"] for s in symptoms if s in SYMPTOMS_BY_ID],
            "items": diag,
        },
        "pilot": {
            "controller": ctrl, "level": level, "attack": attack,
            "braking": braking, "throttle": throttle, "rotation": rotation,
        },
    }
