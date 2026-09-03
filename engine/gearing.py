"""Étalonnage de boîte GT7 (Vmax auto + rapports + pont)."""

from __future__ import annotations


def _geom(n: int, first: float, last: float) -> list[float]:
    if n <= 1:
        return [round(first, 3)]
    ratio = (last / first) ** (1 / (n - 1))
    return [round(first * (ratio ** i), 3) for i in range(n)]


def build_gearing(track: dict, profile: dict, style: str, symptoms: list[str] | None = None) -> dict:
    symptoms = symptoms or []
    name = (track.get("name") or "").lower()
    layout = profile.get("layout") or "mixed"
    vmax = int(profile.get("target_speed") or 270)
    straight = int(track.get("longest_straight") or 0)

    gears = 6
    first, last, final = 3.850, 0.920, 3.950
    nurb = any(k in name for k in ("nordschleife", "nurburgring", "nürburgring", "green hell"))
    if "route x" in name:
        gears, vmax, first, last, final = 8, max(vmax, 430), 3.150, 0.720, 2.850
    elif profile.get("oval"):
        gears, vmax, first, last, final = 6, max(vmax, 320), 3.250, 0.780, 3.350
    elif nurb:
        gears, vmax, first, last, final = 7, 310, 3.200, 0.780, 3.250
    elif layout == "high_speed" or profile.get("endurance"):
        gears, vmax, first, last, final = 7, vmax, 3.450, 0.820, 3.550
    elif layout == "technical":
        gears, vmax, first, last, final = 6, min(vmax, 245), 4.150, 0.980, 4.250
    elif style == "drift":
        gears, first, last, final = 5, 3.600, 1.050, 4.400

    if "limiter_early" in symptoms:
        vmax += 20
        last = round(last * 0.94, 3)
        final = round(final - 0.20, 3)
    if "limiter_never" in symptoms:
        vmax = max(180, vmax - 20)
        last = round(last * 1.06, 3)
        final = round(final + 0.22, 3)
    if "launch_slow" in symptoms:
        first = round(first + 0.35, 3)
        final = round(final + 0.15, 3)
    if "gear_gap" in symptoms and gears < 8:
        gears += 1
        last = round(last * 1.02, 3)

    ratios = _geom(gears, first, last)
    rows = [{"gear": i + 1, "ratio": r} for i, r in enumerate(ratios)]

    howto = [
        f"Dans Réglages → Transmission (full custom / séquentielle) : lance l'étalonnage auto.",
        f"Régle la Vitesse max sur {vmax} km/h (ligne de {straight} m).",
        f"Pont (final gear) : {final:.3f}. Si tu ruptes avant le freinage → baisse le pont (allonge). Si tu n'arrives pas au rupteur → monte le pont.",
        "Raccourcis ensuite la 1re d'un cran si le départ est mou, sans retoucher la dernière.",
        "Les rapports du milieu doivent progresser régulièrement — pas de 'trou' entre 3 et 4.",
    ]
    if layout == "technical":
        howto.append("Circuit technique : privilégie la relance. Mieux vaut ruper 5 m trop tôt que de sortir de la plage de couple.")
    if layout == "high_speed":
        howto.append("Circuit rapide : la dernière doit arriver au rupteur pile en bout de ligne, pas 20 km/h trop longue.")

    return {
        "gears": gears,
        "max_speed": vmax,
        "final_drive": round(final, 3),
        "ratios": rows,
        "spread": "serré (relance)" if layout == "technical" else ("long (Vmax)" if layout == "high_speed" else "équilibré"),
        "howto": howto,
        "note": (
            "L'étalonnage auto de GT7 calcule les rapports à partir de la Vmax. "
            "Les chiffres ci-dessous sont la cible après ce calage — affine au 0.001 près selon le rupteur réel de l'auto."
        ),
    }
