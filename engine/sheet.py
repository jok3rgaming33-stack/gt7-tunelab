"""Feuille de réglages GT7 — valeurs numériques exactes (un cran = un chiffre)."""

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

# Deltas numériques appliqués après la base (valeurs GT7).
SYMPTOM_DELTAS = {
    "us_entry": {"lsd_dec": -7, "brake_bal": -1, "toe_f": 0.04, "aero_f": 8},
    "us_mid": {"arb_f": -2, "arb_r": 1, "camber_f": -0.3, "ride_f": -2},
    "us_exit": {"lsd_acc": -6, "split_r": 5, "aero_r": -8},
    "os_entry": {"lsd_dec": 6, "lsd_init": 3, "brake_bal": -1, "toe_r": 0.06, "aero_r": 15},
    "os_mid": {"arb_r": -2, "arb_f": 1, "camber_r": -0.3, "spring_r": 0.35, "aero_r": 12},
    "os_exit": {"lsd_acc": -8, "tcs": 1, "aero_r": 10},
    "os_lift": {"damp_es_r": 1, "lsd_init": 3, "arb_r": -1},
    "brake_unstable": {"brake_bal": -1, "brake_force": -1, "abs": 1, "lsd_dec": 4},
    "brake_weak": {"brake_force": 2, "abs": 0},
    "brake_lock_f": {"brake_force": -2, "brake_bal": 1, "abs": 1},
    "brake_dive": {"spring_f": 0.40, "damp_cs_f": 1, "ride_f": 2},
    "spin_exit": {"lsd_acc": 6, "lsd_init": 2, "tcs": 1},
    "spin_inside": {"lsd_acc": 6, "lsd_init": 4, "arb_r": 1},
    "launch_slow": {},
    "bottom": {"ride_f": 4, "ride_r": 3, "damp_cf_f": -1},
    "kerb": {"damp_cf_f": -2, "damp_cf_r": -2, "arb_f": -1, "arb_r": -1},
    "bounce": {"damp_es_f": 1, "damp_es_r": 2, "damp_cs_f": 1},
    "stiff": {"spring_f": -0.55, "spring_r": -0.45, "arb_f": -1, "damp_cf_f": -1},
    "nervous": {"toe_r": 0.08, "lsd_init": 3, "aero_r": 10},
    "no_rotate": {"toe_f": 0.06, "toe_r": -0.05, "ride_r": 3, "lsd_dec": -4, "arb_f": -1, "arb_r": 1},
    "squat": {"spring_r": 0.45, "damp_cs_r": 1, "ride_r": 1, "aero_r": 5},
    "hs_us": {"aero_f": 18, "arb_f": -1, "camber_f": -0.2},
    "hs_os": {"aero_r": 22, "aero_f": -5, "toe_r": 0.05, "lsd_acc": -3},
    "hs_wander": {"toe_r": 0.10, "toe_f": -0.04, "aero_f": 8, "aero_r": 12, "arb_f": 1},
    "drag": {"aero_f": -20, "aero_r": -25},
    "heat_inner": {"camber_f": 0.5, "camber_r": 0.4},
    "heat_outer": {"camber_f": -0.4, "camber_r": -0.3},
    "wear_front": {"brake_bal": 1, "brake_force": -1, "aero_f": -8, "aero_r": 8},
    "wear_rear": {"lsd_acc": -4, "tcs": 1, "aero_r": 10},
    "limiter_early": {},
    "limiter_never": {},
    "gear_gap": {},
}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _round(v, nd=0):
    if nd == 0:
        return int(round(v))
    return round(v, nd)


def build_sheet(car, track, profile, drivetrain, tire, style, symptoms, pilot, cl, pp_limit, weather, has_gt_auto):
    layout = profile["layout"]
    surface = profile["surface"]
    hills = profile["hills"]
    race = car.get("is_race")
    name = (track.get("name") or "").lower()
    symptoms = symptoms or []
    pilot = pilot or {}

    # ── Base numérique (unités GT7) ────────────────────────────────────
    n = {
        "ride_f": 92, "ride_r": 97,
        "spring_f": 7.85, "spring_r": 7.25,
        "nfr_f": 2.32, "nfr_r": 2.18,
        "damp_cs_f": 5, "damp_cs_r": 4,
        "damp_cf_f": 3, "damp_cf_r": 3,
        "damp_es_f": 6, "damp_es_r": 6,
        "damp_ef_f": 5, "damp_ef_r": 5,
        "arb_f": 4, "arb_r": 3,
        "camber_f": -2.4, "camber_r": -1.8,
        "toe_f": 0.08, "toe_r": 0.14,  # + = ouvert AV / pincé AR (affichage)
        "lsd_init": 12, "lsd_acc": 24, "lsd_dec": 16,
        "split_f": 40, "split_r": 60,  # 4WD only
        "aero_f": 70, "aero_r": 120,
        "brake_force": 6, "brake_bal": 2,  # + vers l'arrière
        "abs": 1, "tcs": 1, "asm": 0,
        "countersteer": 1,
        "ecu": 100, "ballast_kg": 0, "ballast_pos": 0,
    }

    if race:
        n["ride_f"], n["ride_r"] = 82, 86
        n["spring_f"], n["spring_r"] = 10.40, 9.65
        n["nfr_f"], n["nfr_r"] = 2.48, 2.32
        n["aero_f"], n["aero_r"] = 200, 320

    if surface in ("dirt", "snow"):
        n.update({
            "ride_f": 118, "ride_r": 122,
            "spring_f": 5.60, "spring_r": 5.25,
            "nfr_f": 1.95, "nfr_r": 1.85,
            "damp_cs_f": 3, "damp_cs_r": 3,
            "damp_cf_f": 2, "damp_cf_r": 2,
            "damp_es_f": 5, "damp_es_r": 5,
            "damp_ef_f": 4, "damp_ef_r": 4,
            "arb_f": 2, "arb_r": 2,
            "camber_f": -1.2, "camber_r": -0.8,
            "toe_f": 0.12, "toe_r": 0.08,
            "lsd_init": 8, "lsd_acc": 16, "lsd_dec": 10,
            "split_f": 50, "split_r": 50,
            "aero_f": 0, "aero_r": 0,
            "brake_force": 4, "brake_bal": 1,
            "tcs": 3 if surface == "dirt" else 4, "abs": 2,
        })
    elif layout == "high_speed":
        n["ride_f"], n["ride_r"] = 86, 90
        n["spring_f"] += 1.10
        n["spring_r"] += 0.95
        n["nfr_f"], n["nfr_r"] = 2.50, 2.34
        n["arb_f"], n["arb_r"] = 5, 4
        n["damp_cs_f"], n["damp_cs_r"] = 6, 5
        n["aero_f"], n["aero_r"] = (35, 90) if not race else (180, 260)
        if profile.get("oval") or "route x" in name:
            n["aero_f"], n["aero_r"] = 10, 40
            n["camber_f"], n["camber_r"] = -2.8, -2.2
    elif layout == "technical":
        n["ride_f"], n["ride_r"] = 90, 96
        n["spring_f"] -= 0.35
        n["spring_r"] -= 0.40
        n["nfr_f"], n["nfr_r"] = 2.22, 2.08
        n["arb_f"], n["arb_r"] = 3, 2
        n["damp_cf_f"], n["damp_cf_r"] = 2, 2
        n["aero_f"], n["aero_r"] = (90, 155) if not race else (280, 420)
    else:
        n["aero_f"], n["aero_r"] = (72, 125) if not race else (220, 340)

    if hills in ("hilly", "mountain") or "nordschleife" in name or "panorama" in name:
        n["ride_f"] += 3
        n["ride_r"] += 3
        n["damp_cf_f"] = max(2, n["damp_cf_f"] - 1)

    if drivetrain == "FF":
        n["arb_f"], n["arb_r"] = 2, 5
        n["camber_f"] = -2.8
        n["lsd_init"], n["lsd_acc"], n["lsd_dec"] = 10, 20, 10
        n["brake_bal"] = 0
    elif drivetrain == "MR":
        n["arb_r"] = 2
        n["lsd_init"], n["lsd_acc"], n["lsd_dec"] = 10, 18, 12
        n["toe_r"] = 0.10
        n["brake_bal"] = 2
    elif drivetrain == "4WD":
        n["lsd_init"], n["lsd_acc"], n["lsd_dec"] = 14, 22, 16
        n["split_f"], n["split_r"] = 38, 62
        n["brake_bal"] = 1
    elif drivetrain == "RR":
        n["lsd_init"], n["lsd_acc"], n["lsd_dec"] = 11, 22, 14
        n["camber_r"] = -2.0
        n["brake_bal"] = 2
    else:  # FR
        n["lsd_init"], n["lsd_acc"], n["lsd_dec"] = 12, 26, 15
        n["brake_bal"] = 2

    if style == "drift":
        n.update({
            "camber_f": -0.8, "camber_r": -1.2,
            "toe_f": 0.22, "toe_r": -0.10,
            "lsd_init": 10, "lsd_acc": 48, "lsd_dec": 28,
            "arb_f": 3, "arb_r": 1,
            "tcs": 0, "abs": 1, "countersteer": 1,
            "aero_f": 20, "aero_r": 40,
        })
    elif style == "chrono":
        n["tcs"] = 0
        n["abs"] = 1
        n["damp_cs_f"] += 1
        n["spring_f"] += 0.25
    elif style == "stable":
        n["tcs"] = 2
        n["lsd_acc"] -= 4
        n["lsd_dec"] += 3
        n["toe_r"] += 0.04
        n["arb_f"] += 1

    if tire["grip"] >= 7:
        n["brake_force"] = 7
    if weather in ("wet", "damp"):
        n["tcs"] += 2
        n["abs"] = max(n["abs"], 2)
        n["aero_f"] += 10
        n["aero_r"] += 15

    if not has_gt_auto or surface != "tarmac":
        n["aero_f"] = 0
        n["aero_r"] = 0

    # ── Style de pilotage ──────────────────────────────────────────────
    ctrl = pilot.get("controller") or "pad"
    level = pilot.get("level") or "intermediate"
    attack = pilot.get("attack") or "committed"
    braking = pilot.get("braking") or "trail"
    throttle = pilot.get("throttle") or "progressive"
    rotation = pilot.get("rotation") or "neutral"

    n["countersteer"] = 1 if ctrl == "pad" else 0
    if ctrl == "wheel":
        n["lsd_init"] += 1
        n["toe_f"] -= 0.02

    if level == "beginner":
        n["tcs"] = max(n["tcs"], 3)
        n["abs"] = max(n["abs"], 2)
        n["lsd_acc"] -= 4
        n["lsd_dec"] += 4
        n["arb_f"] += 1
        n["asm"] = 0
    elif level == "expert":
        n["tcs"] = 0 if style != "drift" else n["tcs"]
        n["abs"] = 1
        n["lsd_acc"] += 2

    if attack == "smooth":
        n["damp_cs_f"] -= 1
        n["arb_f"] -= 1
        n["spring_f"] -= 0.30
    elif attack == "aggressive":
        n["damp_cs_f"] += 1
        n["arb_f"] += 1
        n["lsd_dec"] += 3
        n["spring_f"] += 0.35

    if braking == "conservative":
        n["brake_force"] = max(4, n["brake_force"] - 1)
        n["brake_bal"] -= 1
        n["abs"] = max(n["abs"], 2)
    elif braking == "late":
        n["brake_force"] = min(8, n["brake_force"] + 1)
        n["brake_bal"] += 1
        n["damp_cs_f"] += 1
    else:  # trail
        n["lsd_dec"] += 2
        n["brake_bal"] += 0

    if throttle == "early":
        n["lsd_acc"] -= 3
        n["tcs"] += 1
        n["split_r"] += 4
    else:
        n["lsd_acc"] += 1

    if rotation == "stable":
        n["toe_r"] += 0.06
        n["arb_r"] += 1
        n["lsd_dec"] += 3
        n["aero_r"] += 8
    elif rotation == "pointy":
        n["toe_f"] += 0.05
        n["toe_r"] -= 0.04
        n["arb_f"] -= 1
        n["arb_r"] += 1
        n["lsd_dec"] -= 3
        n["ride_r"] += 2

    # ── Symptômes : deltas concrets ────────────────────────────────────
    corrections = []
    before = deepcopy(n)
    for sid in symptoms:
        if sid not in SYMPTOM_DELTAS:
            continue
        spec = SYMPTOMS_BY_ID.get(sid, {"label": sid})
        for key, delta in SYMPTOM_DELTAS[sid].items():
            if key in n:
                n[key] = n[key] + delta
        corrections.append(sid)

    # Clamps GT7
    n["ride_f"] = _clamp(_round(n["ride_f"]), 55, 145)
    n["ride_r"] = _clamp(_round(n["ride_r"]), 55, 150)
    n["spring_f"] = _clamp(_round(n["spring_f"], 2), 2.50, 18.00)
    n["spring_r"] = _clamp(_round(n["spring_r"], 2), 2.50, 18.00)
    n["nfr_f"] = _clamp(_round(n["nfr_f"], 2), 1.60, 3.20)
    n["nfr_r"] = _clamp(_round(n["nfr_r"], 2), 1.50, 3.00)
    for k in ("damp_cs_f", "damp_cs_r", "damp_cf_f", "damp_cf_r", "damp_es_f", "damp_es_r", "damp_ef_f", "damp_ef_r"):
        n[k] = _clamp(_round(n[k]), 1, 10)
    n["arb_f"] = _clamp(_round(n["arb_f"]), 1, 10)
    n["arb_r"] = _clamp(_round(n["arb_r"]), 1, 10)
    n["camber_f"] = _clamp(_round(n["camber_f"], 1), -6.0, 0.0)
    n["camber_r"] = _clamp(_round(n["camber_r"], 1), -6.0, 0.0)
    n["toe_f"] = _clamp(_round(n["toe_f"], 2), -0.40, 0.40)
    n["toe_r"] = _clamp(_round(n["toe_r"], 2), -0.40, 0.40)
    for k in ("lsd_init", "lsd_acc", "lsd_dec"):
        n[k] = _clamp(_round(n[k]), 5, 60)
    n["split_f"] = _clamp(_round(n["split_f"]), 0, 100)
    n["split_r"] = 100 - n["split_f"]
    n["aero_f"] = _clamp(_round(n["aero_f"]), 0, 500)
    n["aero_r"] = _clamp(_round(n["aero_r"]), 0, 500)
    n["brake_force"] = _clamp(_round(n["brake_force"]), 1, 10)
    n["brake_bal"] = _clamp(_round(n["brake_bal"]), -5, 5)
    n["abs"] = _clamp(_round(n["abs"]), 0, 5)
    n["tcs"] = _clamp(_round(n["tcs"]), 0, 5)
    n["asm"] = 0
    n["countersteer"] = 1 if n["countersteer"] else 0
    n["ecu"] = 100 if not pp_limit else 92
    n["ballast_kg"] = 0 if not pp_limit else 0
    n["ballast_pos"] = 25 if drivetrain == "FF" else (20 if drivetrain == "MR" else 0)
    if not pp_limit:
        n["ballast_pos"] = 0

    gearing = build_gearing(track, profile, style, symptoms)

    def toe_txt(v, axle):
        # GT7: pincement positif = IN à l'arrière souvent ; on affiche IN/OUT clair
        if axle == "f":
            side = "OUT" if v >= 0 else "IN"
            return f"{abs(v):.2f}° {side}"
        side = "IN" if v >= 0 else "OUT"
        return f"{abs(v):.2f}° {side}"

    def bal_txt(v):
        if v == 0:
            return "0"
        if v > 0:
            return f"{v} vers l'AR"
        return f"{abs(v)} vers l'AV"

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
                {"label": "Constante de ressort", "front": f"{n['spring_f']:.2f}", "rear": f"{n['spring_r']:.2f}"},
                {"label": "Fréquence naturelle", "front": f"{n['nfr_f']:.2f} Hz", "rear": f"{n['nfr_r']:.2f} Hz"},
                {"label": "Comp. lente", "front": str(n["damp_cs_f"]), "rear": str(n["damp_cs_r"])},
                {"label": "Comp. rapide", "front": str(n["damp_cf_f"]), "rear": str(n["damp_cf_r"])},
                {"label": "Détente lente", "front": str(n["damp_es_f"]), "rear": str(n["damp_es_r"])},
                {"label": "Détente rapide", "front": str(n["damp_ef_f"]), "rear": str(n["damp_ef_r"])},
                {"label": "Barre anti-roulis", "front": str(n["arb_f"]), "rear": str(n["arb_r"])},
                {"label": "Carrossage", "front": f"{n['camber_f']:.1f}°", "rear": f"{n['camber_r']:.1f}°"},
                {"label": "Pincement", "front": toe_txt(n["toe_f"], "f"), "rear": toe_txt(n["toe_r"], "r")},
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
            "kind": "single",
            "rows": [
                {"label": "Couple initial", "value": str(n["lsd_init"])},
                {"label": "Sensibilité accélération", "value": str(n["lsd_acc"])},
                {"label": "Sensibilité freinage", "value": str(n["lsd_dec"])},
            ] + (
                [{"label": "Répartition centrale", "value": f"{n['split_f']} / {n['split_r']}"}]
                if drivetrain == "4WD" else []
            ),
        },
        {
            "title": "TRANSMISSION",
            "kind": "single",
            "rows": [
                {"label": "Étalonnage auto · Vmax", "value": f"{gearing['max_speed']} km/h"},
                {"label": "Pont", "value": f"{gearing['final_drive']:.3f}"},
            ] + [
                {"label": f"{r['gear']}e", "value": f"{r['ratio']:.3f}"}
                for r in gearing["ratios"]
            ],
        },
        {
            "title": "FREINS",
            "kind": "single",
            "rows": [
                {"label": "Force de freinage", "value": str(n["brake_force"])},
                {"label": "Répartition", "value": bal_txt(n["brake_bal"])},
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

    diag_rows = []
    for sid in symptoms:
        spec = SYMPTOMS_BY_ID.get(sid)
        if not spec:
            continue
        changed = []
        for key, delta in SYMPTOM_DELTAS.get(sid, {}).items():
            if key in n and key in before:
                changed.append(f"{key} {before[key]} → {n[key]}")
        diag_rows.append({
            "symptom": spec["label"],
            "detail": spec.get("detail") or spec.get("hint") or "",
            "applied": True,
        })

    return {
        "numbers": n,
        "blocks": blocks,
        "gearing": gearing,
        "disclaimer": "Si un cran est hors plage sur cette auto, prends la valeur autorisée la plus proche. Les mm/kgf varient selon le châssis.",
        "diagnostics": {
            "ids": symptoms,
            "labels": [SYMPTOMS_BY_ID[s]["label"] for s in symptoms if s in SYMPTOMS_BY_ID],
            "items": diag_rows,
        },
        "pilot": {
            "controller": ctrl, "level": level, "attack": attack,
            "braking": braking, "throttle": throttle, "rotation": rotation,
        },
    }
