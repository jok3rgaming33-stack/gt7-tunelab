"""Diagnostic de comportement — tous les axes d'un réglage GT7 (route ou course)."""

from copy import deepcopy

SYMPTOMS = [
    # Courbe
    {"id": "us_entry", "group": "courbe", "group_fr": "Courbe",
     "label": "Sous-virage à l'attaque",
     "hint": "Le nez refuse de rentrer au freinage / trail-brake."},
    {"id": "us_mid", "group": "courbe", "group_fr": "Courbe",
     "label": "Sous-virage à mi-courbe",
     "hint": "Elle pousse large au cordon, pieds stables."},
    {"id": "us_exit", "group": "courbe", "group_fr": "Courbe",
     "label": "Sous-virage en sortie",
     "hint": "Tu remets les gaz, le nez s'ouvre."},
    {"id": "os_entry", "group": "courbe", "group_fr": "Courbe",
     "label": "Survirage à l'attaque",
     "hint": "L'arrière part dès que tu poses les freins."},
    {"id": "os_mid", "group": "courbe", "group_fr": "Courbe",
     "label": "Survirage à mi-courbe",
     "hint": "Elle survire en appui, même sans gaz."},
    {"id": "os_exit", "group": "courbe", "group_fr": "Courbe",
     "label": "Survirage à l'accélération",
     "hint": "Power-oversteer en sortie."},
    {"id": "os_lift", "group": "courbe", "group_fr": "Courbe",
     "label": "Snap au relâché",
     "hint": "Tu coupes les gaz, l'arrière décroche d'un coup."},
    # Freinage
    {"id": "brake_unstable", "group": "freinage", "group_fr": "Freinage",
     "label": "Instable au freinage",
     "hint": "L'arrière se balade, tu corriges en ligne."},
    {"id": "brake_weak", "group": "freinage", "group_fr": "Freinage",
     "label": "Manque de freinage",
     "hint": "Tu n'arrêtes pas la voiture, ou ABS trop tôt."},
    {"id": "brake_lock_f", "group": "freinage", "group_fr": "Freinage",
     "label": "Avant qui bloque",
     "hint": "Les pneus AV saturent, tu perds la direction."},
    {"id": "brake_dive", "group": "freinage", "group_fr": "Freinage",
     "label": "Trop de plongée",
     "hint": "Le nez s'écrase, l'arrière se décharge."},
    # Motricité
    {"id": "spin_exit", "group": "motricite", "group_fr": "Motricité",
     "label": "Patinage en sortie",
     "hint": "Les roues motrices partent en fumée au cordon."},
    {"id": "spin_inside", "group": "motricite", "group_fr": "Motricité",
     "label": "Roue intérieure qui patine",
     "hint": "LSD trop ouvert, une roue tourne dans le vide."},
    {"id": "launch_slow", "group": "motricite", "group_fr": "Motricité",
     "label": "Départ / 1re trop longue",
     "hint": "Ça cale ou ça n'accélère pas au feu / après l'épingle."},
    # Châssis
    {"id": "bottom", "group": "chassis", "group_fr": "Châssis",
     "label": "Talonnage",
     "hint": "Le fond frotte en compression ou sur vibreur."},
    {"id": "kerb", "group": "chassis", "group_fr": "Châssis",
     "label": "Instable sur les vibreurs",
     "hint": "Elle rebondit et part en travers."},
    {"id": "bounce", "group": "chassis", "group_fr": "Châssis",
     "label": "Oscille / rebondit",
     "hint": "La caisse n'arrête pas de pomper après une bosse."},
    {"id": "stiff", "group": "chassis", "group_fr": "Châssis",
     "label": "Trop ferme / saute",
     "hint": "Elle décolle, pas de grip mécanique."},
    {"id": "nervous", "group": "chassis", "group_fr": "Châssis",
     "label": "Trop nerveuse",
     "hint": "Le moindre input et elle change d'idée."},
    {"id": "no_rotate", "group": "chassis", "group_fr": "Châssis",
     "label": "Ne tourne pas (paresseuse)",
     "hint": "Il faut trop d'angle, elle refuse de yaw."},
    {"id": "squat", "group": "chassis", "group_fr": "Châssis",
     "label": "Trop d'accroupissement",
     "hint": "L'arrière s'écrase à l'accélération, le nez se lève."},
    # Haute vitesse / aéro
    {"id": "hs_us", "group": "aero", "group_fr": "Haute vitesse / aéro",
     "label": "Sous-virage en courbe rapide",
     "hint": "OK en lent, elle pousse dès que ça va vite."},
    {"id": "hs_os", "group": "aero", "group_fr": "Haute vitesse / aéro",
     "label": "Survirage en courbe rapide",
     "hint": "L'arrière lâche dans les grandes courbes."},
    {"id": "hs_wander", "group": "aero", "group_fr": "Haute vitesse / aéro",
     "label": "Instable en ligne droite",
     "hint": "Elle danse / demande des corrections à fond."},
    {"id": "drag", "group": "aero", "group_fr": "Haute vitesse / aéro",
     "label": "N'atteint pas la Vmax",
     "hint": "Trop de traînée, ou dernière trop courte."},
    # Pneus
    {"id": "heat_inner", "group": "pneus", "group_fr": "Pneus",
     "label": "Intérieur de pneu trop chaud",
     "hint": "Usure / T° bande intérieure."},
    {"id": "heat_outer", "group": "pneus", "group_fr": "Pneus",
     "label": "Extérieur de pneu trop chaud",
     "hint": "Pas assez de carrossage, elle roule sur l'épaule."},
    {"id": "wear_front", "group": "pneus", "group_fr": "Pneus",
     "label": "Avant qui meurt en premier",
     "hint": "Sous-virage + T° AV hautes."},
    {"id": "wear_rear", "group": "pneus", "group_fr": "Pneus",
     "label": "Arrière qui meurt en premier",
     "hint": "Survirage + T° AR hautes."},
    # Boîte
    {"id": "limiter_early", "group": "boite", "group_fr": "Boîte",
     "label": "Rupteur trop tôt en ligne",
     "hint": "Tu tapes le limiteur avant le freinage."},
    {"id": "limiter_never", "group": "boite", "group_fr": "Boîte",
     "label": "Jamais le rupteur en dernière",
     "hint": "La dernière est trop longue."},
    {"id": "gear_gap", "group": "boite", "group_fr": "Boîte",
     "label": "Trous entre les rapports",
     "hint": "Tu sors de la plage de couple à chaque montée."},
]

DETAILS = {
    "us_entry": "Le train avant saturé au trail-brake. En GT7 : baisse la sensibilité freinage du LSD, bascule 1 cran de frein vers l'avant, ouvre un peu le pincement AV, monte l'appui avant.",
    "us_mid": "Trop de roulis avant ou pas assez de carrossage AV. Ramollis la barre AV, durcis légèrement l'AR, carrossage AV plus négatif.",
    "us_exit": "Le LSD accélération trop élevé pousse le nez (FF/4WD surtout). Baisse Accél., envoie plus de couple à l'arrière en 4WD.",
    "os_entry": "L'arrière se décharge au freinage. Monte Décél. et Couple initial, freins vers l'avant, pince l'AR, plus d'appui AR.",
    "os_mid": "Arrière trop figé ou trop léger en appui. Barre AR plus souple, carrossage AR plus négatif, ressort AR un cran, aileron +.",
    "os_exit": "Power-oversteer : le LSD Accél. est trop fort. C'est le cran n°1. TCS +1 le temps de caler, appui AR +.",
    "os_lift": "L'arrière se décharge d'un coup au lift. Détente lente AR +1/+2, Couple initial +, barre AR −1.",
    "brake_unstable": "Transfert trop brutal ou LSD Décél. trop bas. Freins vers l'AV, force −1, ABS +1, Décél. +.",
    "brake_weak": "Force trop basse ou pneu trop dur. Force 7–8, ABS 1. Si Comfort, le pneu est le limiteur.",
    "brake_lock_f": "Avant saturé. Force −2, répartition un cran vers l'AR, ABS 1–2.",
    "brake_dive": "Ressort / comp. lente AV trop mous. Ressort AV +, compression lente AV +, hauteur AV +2 mm.",
    "spin_exit": "Pas assez de lock à l'accélération. Accél. +6, Init. +2, TCS +1.",
    "spin_inside": "Une roue dans le vide. Accél. et Init. plus élevés, barre AR +1 sur propulsion.",
    "launch_slow": "1re trop longue. L'étalonnage raccourcit la 1re et durcit le pont.",
    "bottom": "Garde au sol insuffisante. Hauteur AV +4 mm, AR +3 mm, compression rapide −1.",
    "kerb": "Amortos rapides trop fermes. Comp. rapide −2, barres −1.",
    "bounce": "La détente ne tient pas le retour. Détente lente +1/+2, compression lente +1.",
    "stiff": "Trop de constante / barre. Ressorts −0.5, barre AV −1, comp. rapide −1.",
    "nervous": "L'AR n'est pas assez pincé. Pincement AR IN +, Init. +, appui AR +.",
    "no_rotate": "L'auto refuse le lacet. Pincement AV OUT, AR moins pincé, caisse AR plus haute, Décél. −, barre AV −.",
    "squat": "Arrière trop mou à la remise des gaz. Ressort AR +, comp. lente AR +, appui AR +.",
    "hs_us": "Pas assez d'appui AV en courbe rapide. Appui avant +18, barre AV −1.",
    "hs_os": "Pas assez d'appui AR. Aileron +22, pincement AR IN +, Accél. −.",
    "hs_wander": "Ligne droite instable. Pince l'AR, pincement AV proche de 0, un peu d'appui des deux côtés.",
    "drag": "Trop d'aileron. Appui AV/AR fortement réduits, Vmax étalonnage plus haute.",
    "heat_inner": "Carrossage trop négatif. Reviens vers 0 (AV +0.5°, AR +0.4°).",
    "heat_outer": "Pas assez de carrossage. Plus négatif AV −0.4°, AR −0.3°.",
    "wear_front": "Tu surcharges l'AV. Freins vers l'AR, force −1, moins d'appui AV.",
    "wear_rear": "Power-oversteer qui grillle l'AR. Accél. −4, TCS +1, appui AR +.",
    "limiter_early": "Dernière trop courte. Vmax étalonnage +20 km/h, pont plus long.",
    "limiter_never": "Dernière trop longue. Vmax −20 km/h, pont plus court.",
    "gear_gap": "Écarts trop grands. Un rapport de plus / étalonnage plus serré.",
}
for s in SYMPTOMS:
    s["detail"] = DETAILS[s["id"]]

SYMPTOMS_BY_ID = {s["id"]: s for s in SYMPTOMS}

# Chaque symptôme → corrections concrètes menu GT7.
_FIXES = {
    "us_entry": [
        ("LSD", "Décel −5 à −10. L'arrière doit pouvoir glisser un peu pour faire rentrer le nez."),
        ("Freins", "Répartition 1–2 clics vers l'avant. Force −1 si l'avant sature."),
        ("Pincement AV", "Un peu plus ouvert (0.08–0.15°) pour l'entrée."),
        ("Aéro", "Appui avant +10, ou arrière −10 si déjà max à l'avant."),
    ],
    "us_mid": [
        ("ARB", "Barre AV −1/−2, barre AR +1. Moins de roulis avant = plus de rotation."),
        ("Carrossage AV", "Plus négatif (−0.3 à −0.5°) pour l'appui à mi-courbe."),
        ("Hauteur", "Avant −1 à −2 mm vs l'arrière (sans frotter)."),
    ],
    "us_exit": [
        ("LSD", "Accel −5 à −8. Trop de lock à l'accélération = pousse (surtout FF/4WD)."),
        ("Diff central 4WD", "Plus de couple à l'arrière (ex. 40/60 → 35/65)."),
        ("Aéro", "Moins d'appui arrière si elle refuse de sortir en glissant le nez."),
        ("TCS", "Si tu es à 0 et que ça pousse : TCS 1, pas plus d'angle."),
    ],
    "os_entry": [
        ("LSD", "Décel +4 à +8, Init +2. Plus de lock à l'attaque = arrière collé."),
        ("Freins", "Répartition vers l'avant (moins d'AR). Force −1."),
        ("Pincement AR", "Plus pincé (+0.05–0.10°) pour calmer l'entrée."),
        ("Aéro", "Appui arrière +15."),
    ],
    "os_mid": [
        ("ARB", "Barre AR −1/−2 (l'arrière doit vivre), AV +1 si besoin."),
        ("Carrossage AR", "Un peu plus négatif. Ressort AR +1 cran."),
        ("Aéro", "Arrière +10 à +20. Avant −5 si déjà élevé."),
    ],
    "os_exit": [
        ("LSD", "Accel −6 à −10. C'est LE réglage du power-oversteer."),
        ("TCS", "Chrono : 0–1. Stable : 2–3 le temps de caler le LSD."),
        ("Diff 4WD", "Un peu plus à l'avant si l'arrière part au gaz."),
        ("Aéro", "Arrière +10. Pas de wingless ici."),
    ],
    "os_lift": [
        ("Amortos", "Détente AR lente +1/+2 : l'arrière ne doit pas se décharger d'un coup."),
        ("LSD", "Init +2 à +4. Décel pas trop élevé (ça aggrave le snap)."),
        ("ARB AR", "−1. Un arrière trop figé claque au relâché."),
    ],
    "brake_unstable": [
        ("Freins", "Répartition vers l'avant, force −1, ABS +1."),
        ("LSD", "Décel +3 à +6 pour tenir l'arrière en ligne."),
        ("Hauteur / ressorts", "Avant un peu plus haut ou ressort AV +1 (moins de transfert brutal)."),
    ],
    "brake_weak": [
        ("Freins", "Force 7–8, plaquettes/disques racing. ABS 1 (pas 3)."),
        ("Pneus", "Si Comfort/Sports : le pneu est le vrai limiteur, pas l'étrier."),
    ],
    "brake_lock_f": [
        ("Freins", "Force −1/−2, répartition un clic vers l'arrière, ABS 1–2."),
        ("Carrossage AV", "Si l'intérieur AV survit : un peu moins de carrossage."),
    ],
    "brake_dive": [
        ("Ressorts / amortos", "Ressort AV +1, compression lente AV +1. Anti-plongée via la détente AR pas trop molle."),
        ("Hauteur AV", "+1–2 mm si tu talonnes en plus."),
    ],
    "spin_exit": [
        ("LSD", "Accel +4 à +8 (les deux roues poussent). Init +2."),
        ("TCS", "+1 cran. 4WD : couple un peu plus à l'avant."),
        ("Pneus", "Vérifie qu'ils sont chauds. Soft usé = patinage."),
    ],
    "spin_inside": [
        ("LSD", "Accel +6, Init +4. La rouse intérieure ne doit plus tourner dans le vide."),
        ("ARB AR", "+1 (moins de délestage intérieur) sur une propulsion."),
    ],
    "launch_slow": [
        ("Boîte", "1re plus courte, pont +0.15. Voir l'étalonnage recalculé."),
        ("Embrayage", "Volant racing déjà conseillé : ça aide le régime à monter."),
    ],
    "bottom": [
        ("Hauteur", "AV et AR +2 à +4 mm. Priorité à l'avant."),
        ("Compression rapide", "−1 (laisse la roue avaler) PUIS hauteur, pas l'inverse."),
    ],
    "kerb": [
        ("Amortos", "Compression rapide AV/AR −1 à −2. Détente rapide pas trop ferme."),
        ("ARB", "−1 des deux côtés. Une caisse figée rebondit sur le vibreur."),
    ],
    "bounce": [
        ("Amortos", "Détente lente +1/+2 (contrôle le retour). Compression lente +1."),
        ("Ressorts", "Si vraiment mou : +1 cran, pas +4."),
    ],
    "stiff": [
        ("Ressorts", "−1 à −2 crans. ARB −1."),
        ("Amortos", "Compression rapide −1. Tu veux du contact, pas du kart."),
    ],
    "nervous": [
        ("Pincement AR", "Plus pincé (+0.05–0.12°)."),
        ("LSD", "Init +3. Décel pas trop bas."),
        ("Direction", "Si volant : vs un cran plus faible. Aéro AR +10."),
    ],
    "no_rotate": [
        ("Pincement AV", "Plus ouvert. AR moins pincé."),
        ("Hauteur", "AR +2–4 mm vs l'avant."),
        ("LSD", "Décel −4. ARB AV −1, AR +1."),
    ],
    "squat": [
        ("Ressort AR", "+1/+2. Compression lente AR +1."),
        ("Hauteur AR", "+1 mm. Aéro AR +5 si dispo."),
    ],
    "hs_us": [
        ("Aéro", "Avant +15 à +25. Balance plus avant en courbe rapide."),
        ("ARB AV", "−1. Carrossage AV un peu plus négatif."),
    ],
    "hs_os": [
        ("Aéro", "Arrière +20 (custom 160–200). Avant −5 si besoin."),
        ("Pincement AR", "+0.05 pincé. LSD accel −3."),
    ],
    "hs_wander": [
        ("Pincement AR", "Pincé 0.15–0.25°. AV proche de 0."),
        ("Aéro", "Un peu d'appui des deux côtés, pas 0/0. ARB AV +1."),
    ],
    "drag": [
        ("Aéro", "Moins d'aileron, diffuseur plutôt que wing custom, wingless si oval/Route X."),
        ("Boîte", "Vmax étalonnage +20 km/h, pont plus long. Voir table."),
    ],
    "heat_inner": [
        ("Carrossage", "Moins négatif (revenir vers −1.6/−2.0 AV)."),
        ("Pression", "En jeu tu ne règles pas la pression : c'est 100% carrossage / toe / hauteur."),
    ],
    "heat_outer": [
        ("Carrossage", "Plus négatif (−0.3 à −0.6°)."),
        ("Pincement", "Évite un avant trop ouvert qui râpe l'épaule."),
    ],
    "wear_front": [
        ("Freins", "Un clic vers l'arrière, force −1."),
        ("Aéro / ARB", "Moins d'avant, plus d'arrière. Tu surcharges le train AV."),
    ],
    "wear_rear": [
        ("LSD", "Accel −4. TCS +1."),
        ("Aéro", "Arrière +10. Moins de power-oversteer = pneus AR qui vivent."),
    ],
    "limiter_early": [
        ("Boîte", "Étalonnage : Vmax +20 km/h. Pont plus long (valeur plus petite). Dernier rapport plus long."),
    ],
    "limiter_never": [
        ("Boîte", "Vmax −20 km/h. Pont plus court. La dernière doit ruper en bout de ligne."),
    ],
    "gear_gap": [
        ("Boîte", "Un rapport de plus si dispo, ou étalonnage plus serré (Vmax un peu plus basse + 1re courte)."),
    ],
}


def grouped_symptoms():
    groups = []
    seen = {}
    for s in SYMPTOMS:
        if s["group"] not in seen:
            seen[s["group"]] = len(groups)
            groups.append({"id": s["group"], "label": s["group_fr"], "items": []})
        groups[seen[s["group"]]]["items"].append(s)
    return groups


def apply_symptoms(setup: dict, symptoms: list[str]) -> dict:
    """Ajoute le bloc diagnostic + corrections au setup."""
    wanted = [s for s in symptoms or [] if s in SYMPTOMS_BY_ID]
    corrections = []
    for sid in wanted:
        spec = SYMPTOMS_BY_ID[sid]
        for area, text in _FIXES.get(sid, []):
            corrections.append({
                "symptom": spec["label"],
                "area": area,
                "text": text,
            })
    setup = deepcopy(setup)
    setup["diagnostics"] = {
        "ids": wanted,
        "labels": [SYMPTOMS_BY_ID[s]["label"] for s in wanted],
        "corrections": corrections,
    }
    return setup
