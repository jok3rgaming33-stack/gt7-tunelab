"""Moteur de recommandation : pièces, GT Auto, feuille de réglages."""

from __future__ import annotations

from copy import deepcopy

from .catalog import (
    PARTS,
    PARTS_BY_ID,
    TIERS,
    TIRE_COMPOUNDS,
    part_unlocked,
    price_for,
    swap_cost,
)
from .sheet import build_sheet


def _tire_by_code(code: str):
    for t in TIRE_COMPOUNDS:
        if t["id"] == code:
            return t
    return TIRE_COMPOUNDS[5]  # SS fallback


def pick_tires(profile, weather, tire_restriction, collector_level, has_ultimate):
    """Retourne le compound à monter + justification."""
    if tire_restriction:
        t = _tire_by_code(tire_restriction)
        return t, f"Imposé par le règlement : {t['name_fr']}."

    surface = profile["surface"]
    if surface == "dirt":
        return _tire_by_code("D"), "Circuit terre : pneus Dirt obligatoires pour performer (et souvent pour s'inscrire)."
    if surface == "snow":
        if collector_level >= 50:
            return _tire_by_code("SNOW"), "Lake Louise / neige : pneus neige (Extreme, rang 50)."
        return _tire_by_code("D"), "Neige mais rang < 50 : Dirt en pis-aller, tu n'as pas encore les pneus neige."

    if weather == "wet":
        if collector_level >= 50:
            return _tire_by_code("W"), "Pluie : Heavy Wet (Extreme)."
        return _tire_by_code("SS"), "Pluie mais Extreme verrouillé : Sports Soft, tu vas glisser."
    if weather == "damp":
        if collector_level >= 50:
            return _tire_by_code("IM"), "Piste humide : intermédiaires."
        return _tire_by_code("SS"), "Humide sans Extreme : Sports Soft, prudence."
    if weather == "variable":
        if collector_level >= 50:
            return _tire_by_code("IM"), "Météo changeante : partir en intermédiaires, prévoir un train de slicks/pluie."
        return _tire_by_code("SM"), "Météo changeante sans Extreme : Sports Medium, plus tolérant."

    # dry tarmac
    if profile.get("endurance") and collector_level >= 6:
        return _tire_by_code("RM"), "Stint long / endurance : Racing Medium, le meilleur compromis usure/chrono."
    if collector_level >= 6:
        if profile["layout"] == "high_speed" and profile.get("oval"):
            return _tire_by_code("RH"), "Oval : Racing Hard, moins de surchauffe et usure plus linéaire."
        return _tire_by_code("RS"), "Sec, rang 6+ : Racing Soft pour le chrono. Passe en RM si usure ou heat."
    return _tire_by_code("SS"), "Rang < 6 : Sports Soft, le meilleur pneu boutique disponible."


def _add(items, pid, why, priority, optional=False, extra=None):
    part = deepcopy(PARTS_BY_ID[pid])
    part["why"] = why
    part["priority"] = priority  # must | core | power | pp | optional | skip
    part["optional"] = optional
    if extra:
        part.update(extra)
    items.append(part)


def _best_available(collector_level, has_ultimate, chain):
    """chain = ids from best to worst."""
    for pid in chain:
        p = PARTS_BY_ID[pid]
        if part_unlocked(p, collector_level, has_ultimate):
            return pid
    return None


def recommend(car, track, opts):
    cl = int(opts.get("collector_level") or 1)
    weather = opts.get("weather") or "dry"
    tire_r = opts.get("tires") or None
    pp_limit = opts.get("pp_limit")
    pp_limit = float(pp_limit) if pp_limit not in (None, "", 0, "0") else None
    has_ultimate = bool(opts.get("has_ultimate"))
    has_gt_auto = bool(opts.get("has_gt_auto", True))
    swap_engine = str(opts.get("swap_engine") or "").strip()
    allow_swap = bool(swap_engine) or bool(opts.get("allow_swap"))
    allow_wide = bool(opts.get("allow_wide", True))
    style = opts.get("style") or "polyvalent"  # stable | polyvalent | chrono | drift
    drivetrain = opts.get("drivetrain_override") or car["drivetrain"]
    categories = opts.get("categories") or []
    drivetrain_filters = opts.get("drivetrains") or []
    car_types = opts.get("car_types") or []
    symptoms = opts.get("symptoms") or []
    pilot = opts.get("pilot") or {}

    profile = track["profile"]
    warnings = []
    notes = []

    if categories and car["category"] not in categories:
        # N-classes only apply loosely
        if not any(c.startswith("N") for c in categories):
            warnings.append(
                f"La {car['full_name']} est en {car['category']}, hors règlement ({', '.join(categories)})."
            )
    if drivetrain_filters and drivetrain not in drivetrain_filters:
        warnings.append(
            f"Traction détectée : {drivetrain}. Le règlement demande {', '.join(drivetrain_filters)}."
        )
    if car_types and car["car_type"] not in car_types:
        warnings.append(
            f"Type {car['car_type']} hors filtre ({', '.join(car_types)})."
        )
    if cl < 4:
        notes.append("Rang < 4 : Club Sports fermé (LSD, bore, bridle, ballast, Dirt).")
    if cl < 5:
        notes.append("Rang < 5 : pas de LSD full custom ni boîte full custom.")
    if cl < 6:
        notes.append("Rang < 6 : pas de suspension full custom, ni Racing tires, ni séquentielle.")
    if cl < 50:
        notes.append("Rang < 50 : Extreme + swap moteur verrouillés.")

    tire, tire_why = pick_tires(profile, weather, tire_r, cl, has_ultimate)
    if tire["id"] in ("IM", "W", "SNOW") and cl < 50:
        warnings.append("Les pneus météo Extreme demandent le rang 50.")

    shopping = []
    skipped = []
    gt_auto = []

    # ── Pneus ──────────────────────────────────────────────────────────
    _add(shopping, tire["part"], tire_why, "must")

    # ── Chassis ────────────────────────────────────────────────────────
    race_car = car["is_race"]
    if race_car:
        notes.append(
            "Voiture de course : beaucoup de pièces atelier sont déjà là ou grisées. "
            "La liste ne reprend que pneus / PP / éventuellement ECU — vérifie le menu de l'auto."
        )
        skipped.append("Suspension, LSD, embrayage, boîte, aéro GT Auto : déjà racing d'origine sur les Gr.")

    if not race_car:
        susp = _best_available(cl, has_ultimate, ["susp_full", "susp_sport_adj", "susp_sport", "susp_street"])
        if susp:
            why = {
                "susp_full": "Tous les curseurs. C'est LA pièce qui transforme le comportement.",
                "susp_sport_adj": "Hauteur réglable en attendant le rang 6.",
                "susp_sport": "Plus ferme que la street, meilleur support en appui.",
                "susp_street": "Premier palier : caisse plus basse, moins de roulis.",
            }[susp]
            _add(shopping, susp, why, "core")

        if cl >= 5:
            _add(shopping, "rigidity", "Caisse plus rigide = réponses plus propres, surtout combiné à l'allègement.", "core")

    wr_chain = ["wr5", "wr4", "wr3", "wr2", "wr1"]
    wr_best = _best_available(cl, has_ultimate, wr_chain)
    if wr_best and not race_car:
        # need to buy the chain
        order = ["wr1", "wr2", "wr3", "wr4", "wr5"]
        stop = order.index(wr_best)
        for pid in order[: stop + 1]:
            if part_unlocked(PARTS_BY_ID[pid], cl, has_ultimate):
                _add(
                    shopping,
                    pid,
                    "L'allègement est le meilleur Cr./PP du jeu. Stages enchaînés, irréversibles sans carrosserie neuve.",
                    "core",
                )
    elif wr_best and race_car:
        skipped.append("Allègement : souvent déjà au minimum sur une Gr. / racing. Vérifier en jeu.")

    # brakes / LSD / trans — déjà racing sur les Gr.
    if not race_car:
        pads = _best_available(cl, has_ultimate, ["pads_racing", "pads_sport"])
        discs = _best_available(cl, has_ultimate, ["brakes_slot", "brakes_sport"])
        if tire["grip"] >= 7:
            if pads:
                _add(shopping, pads, "Pneus racing : plaquettes racing, sinon tu n'arrêtes plus la voiture.", "core")
            if discs:
                _add(shopping, discs, "Disques racing (rainurés). Les percés sont identiques en perf.", "core")
        else:
            if pads:
                _add(shopping, pads, "Minimum freinage. Monte d'un cran si tu passes en Sports/Racing.", "core")
            if discs and tire["grip"] >= 4:
                _add(shopping, discs, "Disques sport/racing pour coller au niveau des pneus.", "core")
        if cl >= 6:
            _add(shopping, "brake_bal", "Répartiteur : 1–3 clics vers l'arrière en FR/MR, un peu plus avant en FF.", "core")

        lsd = _best_available(cl, has_ultimate, ["lsd_full", "lsd_2way", "lsd_1way"])
        if lsd:
            why = {
                "lsd_full": "Init / accel / decel : c'est 80% du feeling propulsion.",
                "lsd_2way": "En attendant le full custom : plus stable à l'attaque que le 1-way.",
                "lsd_1way": "Aide à la sortie de courbe. Passe 2-way dès que possible.",
            }[lsd]
            _add(shopping, lsd, why, "core")

        if drivetrain == "4WD" and cl >= 6:
            _add(shopping, "center_diff", "Répartition de couple 4WD. Sans ça tu ne règles pas le caractère de l'auto.", "core")
            _add(shopping, "active_lsd", "LSD actif : plus propre en 4WD qu'un 2-way figé, surtout sur l'avant.", "optional", optional=True)

        clutch = _best_available(cl, has_ultimate, ["clutch_racing", "clutch_semi", "clutch_sport"])
        if clutch:
            _add(shopping, clutch, "Volant allégé = réponse et frein moteur. Gain de ligne droite faible, gain de chassis réel.", "core")

        if has_ultimate:
            _add(shopping, "carbon_shaft", "Arbre carbone (Ultimate) : réponse à l'accélérateur plus vive.", "optional", optional=True)

        if cl >= 6:
            _add(
                shopping,
                "trans_seq",
                "Séquentielle full custom : rapports + pont. Vise la Vmax cible du circuit (voir feuille).",
                "core",
            )
        elif cl >= 5:
            _add(shopping, "trans_manual", "Boîte manuelle full custom : indispensable dès que tu pousses le moteur.", "core")
        else:
            if profile["layout"] == "high_speed":
                if cl >= 4:
                    _add(shopping, "trans_high", "Circuit rapide sans full custom : close-ratio longue.", "core")
            else:
                if cl >= 4:
                    _add(shopping, "trans_low", "Circuit technique sans full custom : close-ratio courte.", "core")
    elif cl >= 6:
        _add(shopping, "brake_bal", "Répartiteur (si le menu le propose) : 1–3 clics vers l'arrière en FR/MR.", "optional", optional=True)

    # ── Moteur ─────────────────────────────────────────────────────────
    # Sous une limite PP, on n'empile pas turbo + swap + Ultimate pour tout bride ensuite.
    if pp_limit is None or pp_limit >= 800:
        power_level = "max"
    elif pp_limit >= 700:
        power_level = "high"
    elif pp_limit >= 600:
        power_level = "mid"
    else:
        power_level = "low"
    if race_car:
        power_level = "low" if pp_limit else "mid"
    modest_power = power_level in ("low", "mid")
    skip_boost = race_car or power_level in ("low", "mid")
    skip_ultimate_power = power_level != "max"

    # ECU always useful (power + later detune)
    ecu = _best_available(cl, has_ultimate, ["ecu_full", "ecu_sport"])
    if ecu:
        why = (
            "Réglage du % de puissance : l'arme n°1 pour coller à une limite PP sans casser la courbe."
            if ecu == "ecu_full"
            else "Premier palier de carto. Passe full custom au rang 5 pour le % de puissance."
        )
        _add(shopping, ecu, why, "power")

    intake = _best_available(cl, has_ultimate, ["air_racing", "air_sport"])
    if intake and not race_car:
        _add(shopping, intake, "Admission : cheap, toujours prise.", "power")

    exhaust = _best_available(cl, has_ultimate, ["muffler_racing", "muffler_semi", "muffler_sport"])
    if exhaust and not race_car:
        _add(shopping, exhaust, "Ligne plus libre, plus de haut-régime.", "power")
    if cl >= 6 and not race_car:
        _add(shopping, "manifold", "Collecteur racing : complète la ligne.", "power")

    if not race_car and power_level != "low":
        # permanent NA path — dosé selon la limite PP
        if cl >= 4:
            _add(shopping, "bore", "Bore up : meilleur rapport prix/chevaux sur un NA. Irréversible.", "power")
            _add(shopping, "cam", "Cames haute levée : +300 tr/min, allonge le haut.", "power")
            if skip_boost:
                _add(shopping, "pistons_hc", "Pistons HC : NA only. Ne pas poser si tu prévois un turbo.", "power", optional=True)
        if cl >= 5 and power_level == "max" and style == "chrono":
            _add(shopping, "crank", "Vilebrequin racing : pic plus haut, irréversible.", "power", optional=True)
        if cl >= 6 and power_level == "max" and style == "chrono":
            _add(shopping, "stroke", "Stroke up : second palier de cylindrée. Irréversible.", "power", optional=True)
            _add(shopping, "balance", "Équilibrage : ×1.05 sur le rupteur, gros palier.", "power", optional=True)
            _add(shopping, "ports", "Polissage des conduits : haut-régime.", "power", optional=True)
        if has_ultimate and not skip_ultimate_power:
            for pid, why in [
                ("bore_s", "Ultimate : bore S remplace le bore standard."),
                ("stroke_s", "Ultimate : stroke S."),
                ("ti_rods", "Ultimate : bielles/pistons titane, moteur qui tourne plus libre."),
                ("cam_s", "Ultimate : cames S."),
            ]:
                _add(shopping, pid, why, "power", optional=True)
        elif has_ultimate and skip_ultimate_power:
            notes.append("Pièces Ultimate moteur ignorées : la limite PP ne justifie pas le surplus de chevaux.")

        # boost
        if cl >= 6 and power_level == "low":
            notes.append("Limite PP basse : on garde ECU / admission / ligne pour le couple, sans cylindrée ni turbo.")
        if not skip_boost and cl >= 5:
            if profile["layout"] == "technical" or profile["surface"] in ("dirt", "snow"):
                turbo = _best_available(cl, has_ultimate, ["turbo_low", "turbo_mid"])
                why = "Turbo bas/mi-régime : couple tôt sur piste technique ou terre."
            elif profile["layout"] == "high_speed":
                turbo = _best_available(cl, has_ultimate, ["turbo_uhigh", "turbo_high", "turbo_mid"])
                why = "Turbo haut-régime : pic pour les grandes courbes / lignes droites."
            else:
                turbo = _best_available(cl, has_ultimate, ["turbo_mid", "turbo_high"])
                why = "Turbo mi-régime : le plus propre à conduire."
            if turbo:
                _add(shopping, turbo, why, "power")
            ic = _best_available(cl, has_ultimate, ["ic_racing", "ic_sport"])
            if ic:
                _add(shopping, ic, "Intercooler dès qu'il y a de la suralimentation.", "power")
            if cl >= 6:
                _add(shopping, "als", "Anti-lag : le turbo reste en pression à la décélération.", "power")
            notes.append(
                "Ne cumule pas pistons haute compression et kit turbo/compressseur : le jeu retire les HC."
            )

    if style == "chrono" and cl >= 50 and profile["layout"] == "high_speed" and not pp_limit:
        _add(shopping, "nitro", "Nitro : burst sur oval / Route X. Évite en course PP.", "optional", optional=True)

    # PP tools
    if pp_limit is not None and cl >= 4:
        _add(
            shopping,
            "restrictor",
            f"Limite {pp_limit:.0f} PP : bridle en dernier recours (garde le couple bas).",
            "pp",
        )
        _add(
            shopping,
            "ballast",
            "Lest : 1) descendre le PP  2) bouger l'équilibre (FF : reculer / MR léger à l'arrière : avancer).",
            "pp",
        )
        if ecu == "ecu_full":
            notes.append(
                f"Procédure PP {pp_limit:.0f} : monte le chassis d'abord, la puissance ensuite, "
                "puis ECU (output %) jusqu'à passer sous la barre. Bridle si l'ECU mange trop le haut. "
                "Lest seulement s'il reste 1–2 PP ou pour l'équilibre."
            )
    elif cl >= 4:
        _add(shopping, "restrictor", "À avoir dans l'inventaire pour les Daily / salon PP.", "optional", optional=True)
        _add(shopping, "ballast", "Utile pour l'équilibre même sans limite PP.", "optional", optional=True)

    # ── GT Auto ────────────────────────────────────────────────────────
    if has_gt_auto:
        want_wide = allow_wide and not race_car and profile["surface"] == "tarmac"
        if want_wide:
            gt_auto.append({
                **deepcopy(PARTS_BY_ID["widebody"]),
                "why": "Voies plus larges + pneus plus larges après changement de jantes. Gros gain de grip, PP en hausse.",
                "priority": "core",
                "optional": False,
            })
            gt_auto.append({
                **deepcopy(PARTS_BY_ID["wheels"]),
                "why": "Après kit large : nouvelles jantes pour élargir les pneus. +1 taille si le règlement PP le permet.",
                "priority": "core",
                "optional": False,
            })
        elif allow_wide and race_car:
            skipped.append("Kit large : les Gr. ont déjà un body racing. Inutile / souvent indisponible.")

        if profile["surface"] == "tarmac" and not race_car:
            gt_auto.append({
                **deepcopy(PARTS_BY_ID["aero_front"]),
                "why": "Débloque l'appui avant 0–100. Prends le type qui existe (A ou B, peu importe le look).",
                "priority": "core",
                "optional": False,
            })
            rear_part = "aero_diffuser" if profile["layout"] != "high_speed" else "aero_rear"
            gt_auto.append({
                **deepcopy(PARTS_BY_ID[rear_part]),
                "why": (
                    "Diffuseur : appui AV+AR 50–100 et moins de traînée — souvent le meilleur deal."
                    if rear_part == "aero_diffuser"
                    else "Aéro arrière classique 0–100 si pas de diffuseur sur cette caisse."
                ),
                "priority": "core",
                "optional": False,
            })
            gt_auto.append({
                **deepcopy(PARTS_BY_ID["aero_side"]),
                "why": "Souvent cosmétique, parfois requis pour 'compléter' le pack. Installe si dispo.",
                "priority": "optional",
                "optional": True,
            })
            wing_id = "wing_custom" if profile["layout"] != "high_speed" else "wing_ab"
            if profile["layout"] == "high_speed" and (profile.get("oval") or "route x" in track["name"].lower()):
                wing_id = "wingless"
            gt_auto.append({
                **deepcopy(PARTS_BY_ID[wing_id]),
                "why": {
                    "wing_custom": "Aileron custom : 50–200 à l'arrière, plus de levier pour équilibrer.",
                    "wing_ab": "Type A/B : 50–150. Suffisant, moins de drag qu'un custom à fond.",
                    "wingless": "Grandes lignes droites / oval : drag minimum. Tu compenseras au châssis.",
                }[wing_id],
                "priority": "core" if wing_id != "wingless" else "optional",
                "optional": wing_id == "wingless",
            })

        if profile["surface"] in ("dirt", "snow") or style == "drift":
            if cl >= 50:
                gt_auto.append({
                    **deepcopy(PARTS_BY_ID["rollcage"]),
                    "why": "Look rallye / cage. Perf négligeable.",
                    "priority": "optional",
                    "optional": True,
                })

        # Engine swap — uniquement si le joueur en a choisi un (Options atelier).
        if car.get("swaps"):
            ranked = _rank_swaps(car["swaps"], pp_limit, profile)
            chosen = None
            if swap_engine:
                key = swap_engine.lower()
                chosen = next((s for s in ranked if s["engine"].lower() == key), None)
                if chosen is None:
                    chosen = next((s for s in ranked if key in s["engine"].lower()), None)
            if chosen:
                cr = int(chosen.get("price") or swap_cost(chosen["engine"]))
                if cl < 50:
                    warnings.append("Swap GT Auto : rang collectionneur 50 requis pour l'acheter.")
                gt_auto.append({
                    **deepcopy(PARTS_BY_ID["engine_swap"]),
                    "name_fr": f"Swap : {chosen['engine']}",
                    "why": (
                        f"Moteur {chosen['engine']} (issu de {chosen['donor']}). "
                        f"{cr:,} Cr.".replace(",", " ")
                        + (" — vérifie le PP après pose." if pp_limit else " — retaille ECU, lest et boîte après le swap.")
                    ),
                    "priority": "power",
                    "optional": cl < 50,
                    "swap_pick": chosen,
                    "swap_all": ranked,
                    "price_min": cr,
                    "price_max": cr,
                    "price_typical": cr,
                })
                notes.append(
                    "Après un swap : le moteur neuf 'reset' ne ramène PAS l'origine, il reset les mods du nouveau moteur. "
                    "Re-taille la boîte, le lest et l'ECU."
                )
            else:
                notes.append(
                    f"{len(car['swaps'])} swap(s) dispo — choisis le moteur dans Options atelier pour l'ajouter au plan."
                )
    else:
        notes.append("GT Auto décoché : kit large, aéro et swap ignorés.")

    # extras extreme
    if style == "drift" and cl >= 50:
        _add(shopping, "steering_angle", "Plus d'angle : drift / épingle terre.", "optional", optional=True)
        _add(shopping, "handbrake", "Frein à main hydro : rallye et drift.", "optional", optional=True)
    if profile["surface"] in ("dirt", "snow") and cl >= 50:
        _add(shopping, "handbrake", "Frein à main hydro : épingles terre / neige.", "optional", optional=True)

    # carbon ceramic : skip (same as racing)
    skipped.append("Freins carbone-céramique : même perf que les racing. Économise les Cr.")
    skipped.append("Moteur neuf / carrosserie neuve : uniquement pour ANNULER un permanent, pas pour aller plus vite.")

    setup = build_setup(
        car=car,
        track=track,
        profile=profile,
        drivetrain=drivetrain,
        tire=tire,
        style=style,
        cl=cl,
        pp_limit=pp_limit,
        weather=weather,
        has_gt_auto=has_gt_auto,
        allow_wide=allow_wide and not race_car,
        symptoms=symptoms,
        pilot=pilot,
    )

    # Dedupe then scale prices to THIS car (wiki road ≠ boutique Gr.3)
    shopping = _dedupe(shopping)
    gt_auto = _dedupe(gt_auto)
    _apply_car_prices(shopping, car)
    _apply_car_prices(gt_auto, car)

    must_core = [i for i in shopping if i["priority"] in ("must", "core", "pp", "power") and not i.get("optional")]
    cmin, ctyp, cmax = _sum_cost(must_core + [g for g in gt_auto if not g.get("optional")])

    strategy = _strategy_text(car, track, profile, drivetrain, tire, pp_limit, cl, style)

    return {
        "car": car,
        "track": track,
        "profile": profile,
        "drivetrain": drivetrain,
        "collector_level": cl,
        "tire": tire,
        "strategy": strategy,
        "shopping": shopping,
        "gt_auto": gt_auto,
        "setup": setup,
        "warnings": warnings,
        "notes": notes,
        "skipped": skipped,
        "cost_min": cmin,
        "cost_typical": ctyp,
        "cost_max": cmax,
        "price_note": "Prix indicatifs selon le type de voiture (les Gr. sont beaucoup moins chères que le wiki série).",
        "pp_limit": pp_limit,
        "style": style,
        "weather": weather,
    }


def _rank_swaps(swaps, pp_limit, profile):
    """Heuristique : gros moteurs d'abord, sauf limite PP basse."""
    POWER_HINTS = [
        ("chiron", 100), ("huayra", 92), ("demon", 88), ("hellcat", 80),
        ("vr38", 86), ("r26b", 90), ("2jz", 78), ("ls7", 74), ("ls9", 80),
        ("lt5", 76), ("lt4", 72), ("vrh35", 88), ("evo-final-gr.b", 84),
        ("k20c1", 60), ("b18c", 40), ("se75e", 55), ("mdya", 82),
        ("dkh-911", 80), ("m97", 70), ("h25a", 75), ("v8-suzuki", 85),
        ("3s-gte", 58), ("13b-rew", 62), ("rb26", 77), ("sr20", 52),
        ("1lr-gue", 83), ("f140", 90), ("f136", 70), ("l539", 88),
        ("byh-r8", 68), ("p65b44", 72), ("m159", 86), ("8.0-wr16", 100),
        ("windsor", 64), ("voodoo", 70), ("coyote", 66), ("k24a", 48),
        ("hr-414e", 80), ("vk45", 72), ("lz20b", 78), ("ej20", 60),
        ("k14c", 35), ("gti-vgt", 80), ("r5-20vt", 70), ("690t", 74),
        ("ctr38", 85), ("959.50", 78), ("m64", 55),
    ]
    ranked = []
    for s in swaps:
        key = s["engine"].lower()
        score = 50
        for needle, val in POWER_HINTS:
            if needle in key:
                score = val
                break
        if pp_limit and pp_limit < 600:
            score = 100 - score  # milder engines first
        if profile["surface"] in ("dirt", "snow") and any(x in key for x in ("evo", "ej20", "gr.b", "quattro")):
            score += 15
        ranked.append({**s, "score": score})
    ranked.sort(key=lambda x: -x["score"])
    return ranked


def _apply_car_prices(items, car):
    for it in items:
        if it.get("shop") == "roulette":
            it["price_min"] = it["price_max"] = it["price_typical"] = 0
            continue
        if it.get("id") == "engine_swap":
            cr = it.get("price_typical") or it.get("price_min") or 0
            if not cr and it.get("swap_pick"):
                cr = it["swap_pick"].get("price") or swap_cost(it["swap_pick"].get("engine"))
            it["price_min"] = it["price_max"] = it["price_typical"] = int(cr or 0)
            continue
        a, b, typ = price_for(it, car)
        it["price_min"] = a
        it["price_max"] = b
        it["price_typical"] = typ


def _sum_cost(items):
    total = 0
    for i in items:
        if i.get("optional") or i.get("shop") == "roulette":
            continue
        typ = i.get("price_typical")
        if typ is None:
            typ = ((i.get("price_min") or 0) + (i.get("price_max") or 0)) // 2
        total += int(typ or 0)
    lo = int(total * 0.9)
    hi = int(total * 1.1)
    return lo, total, hi


def _dedupe(items):
    seen = set()
    out = []
    rank = {"must": 0, "core": 1, "pp": 2, "power": 3, "optional": 4}
    items = sorted(items, key=lambda i: rank.get(i.get("priority"), 9))
    for it in items:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        out.append(it)
    return out


def build_setup(car, track, profile, drivetrain, tire, style, cl, pp_limit, weather, has_gt_auto, allow_wide, symptoms=None, pilot=None):
    symptoms = symptoms or []
    sheet = build_sheet(
        car, track, profile, drivetrain, tire, style, symptoms, pilot or {},
        cl, pp_limit, weather, has_gt_auto,
    )
    g = sheet["gearing"]
    n = sheet["numbers"]
    setup = {
        "tires": tire["name_fr"],
        "sheet": sheet,
        "gearing": g,
        "transmission": f"Étalonnage auto {g['max_speed']} km/h · pont {g['final_drive']:.3f}",
        "final_drive": f"{g['final_drive']:.3f}",
        "ecu": f"{n['ecu']} %",
        "ballast": f"{n['ballast_kg']} kg",
        "ballast_pos": str(n["ballast_pos"]),
        "brakes_force": str(n["brake_force"]),
        "brake_balance": str(n["brake_bal"]),
        "abs": str(n["abs"]),
        "tcs": str(n["tcs"]),
        "asm": "OFF",
        "countersteer": "ON" if n["countersteer"] else "OFF",
        "controller": _controller_note(drivetrain, profile["surface"], style),
        "session_plan": _session_plan(profile, drivetrain, pp_limit),
        "aero": {"front": str(n["aero_f"]), "rear": str(n["aero_r"]), "note": ""},
        "ride": {"front": f"{n['ride_f']} mm", "rear": f"{n['ride_r']} mm", "note": ""},
        "nfr": {"front": f"{n['nf_f']:.2f} Hz", "rear": f"{n['nf_r']:.2f} Hz", "note": ""},
        "arbs": {"front": str(n["arb_f"]), "rear": str(n["arb_r"])},
        "dampers": {
            "comp": f"{n['comp_f']} % / {n['comp_r']} %",
            "exp": f"{n['exp_f']} % / {n['exp_r']} %",
        },
        "lsd": {
            "initial": str(n["lsd_ri"]),
            "accel": str(n["lsd_ra"]),
            "decel": str(n["lsd_rd"]),
            "note": "",
        },
        "camber": {"front": f"{n['camber_f']:.1f}°", "rear": f"{n['camber_r']:.1f}°", "note": ""},
        "toe": {"front": str(n["toe_f"]), "rear": str(n["toe_r"])},
        "diagnostics": sheet["diagnostics"],
    }
    return setup



def _controller_note(drivetrain, surface, style):
    if style == "drift":
        return "Sensibilité direction 0 / vs 3–5. Couple de rappel faible."
    if drivetrain == "FF":
        return "N'attaque pas trop les vibreurs intérieurs : une FF se cale. Trail-brake léger pour la faire rentrer."
    if drivetrain == "MR":
        return "Sois propre à l'attaque. Relâche en courbe rapide = l'arrière part. Ajoute les gaz progressivement."
    if drivetrain == "4WD":
        return "Tu peux remettre les gaz tôt. Si sous-virage : moins d'angle, plus de gaz, ou couple vers l'arrière."
    return "Classique propulsion : rotate au frein, gaz au cordon. Si elle pousse : +decel LSD ou moins d'appui AR."


def _session_plan(profile, drivetrain, pp_limit):
    steps = [
        "1. Monte les pièces chassis (poids, susp, LSD, freins, boîte) AVANT le moteur.",
        "2. GT Auto : kit large + jantes, puis aéro (avant, diffuseur/arrière, aileron).",
        "3. Swap si prévu, ensuite seulement les kits moteur.",
        "4. 3 tours outlap pour chauffer. Lis les T° pneus (int/mid/ext).",
        "5. Ajuste carrossage (T°) puis LSD (comportement) puis aéro (courbes rapides).",
        "6. Boîte : si tu ruptes avant le freinage → allonge. Si tu n'arrives pas au rupteur → raccourcis.",
    ]
    if pp_limit:
        steps.append(f"7. PP {pp_limit:.0f} : ECU % → bridle → lest. Ne descends pas l'appui pour 'gagner' 2 PP.")
    if profile["surface"] != "tarmac":
        steps.append("7. Terre/neige : plus haut, plus souple, TCS un cran au-dessus, LSD plus ouvert.")
    return steps


def _strategy_text(car, track, profile, drivetrain, tire, pp_limit, cl, style):
    bits = [
        f"{car['full_name']} ({drivetrain}, {car['category']}) sur {track['name']}.",
        f"Profil circuit : {', '.join(profile['labels'])} — {int(track['length'])} m, "
        f"ligne {int(track['longest_straight'])} m, {track['corners']} virages, Δh {int(track['elevation'])} m.",
        f"Pneus : {tire['name_fr']}. Style : {style}. Rang collectionneur : {cl}.",
    ]
    if pp_limit:
        bits.append(f"Objectif : coller {pp_limit:.0f} PP sans vider la voiture — chassis d'abord, puissance ensuite, detune chirurgical.")
    else:
        bits.append("Pas de limite PP : on cherche le chrono (ou la stabilité, selon le style), pas le règlement.")
    if car.get("has_swap") and cl >= 50:
        bits.append(f"{len(car['swaps'])} swap(s) moteur disponibles.")
    return " ".join(bits)


def suggest_cars(db, track, opts, limit=12):
    """Propose des voitures qui collent au règlement / circuit."""
    cats = opts.get("categories") or []
    dts = opts.get("drivetrains") or []
    types = opts.get("car_types") or []
    want_swap = bool(opts.get("prefer_swap"))
    surface = track["profile"]["surface"]
    scored = []
    for c in db.cars:
        if cats and c["category"] not in cats:
            if not (c["category"] == "Road" and any(x.startswith("N") for x in cats)):
                continue
        if dts and c["drivetrain"] not in dts:
            continue
        if types and c["car_type"] not in types:
            continue
        score = 0
        if surface == "dirt" and (c["drivetrain"] == "4WD" or c["category"] == "Gr.B"):
            score += 40
        if surface == "tarmac" and c["category"] in ("Gr.3", "Gr.4") and not cats:
            score += 15
        if c["has_swap"]:
            score += 10 if want_swap else 3
        if c["drivetrain"] == "MR":
            score += 4
        if c["drivetrain"] == "FR":
            score += 3
        scored.append((score, c))
    scored.sort(key=lambda x: (-x[0], x[1]["full_name"]))
    return [c for _, c in scored[:limit]]
