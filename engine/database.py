"""Charge et enrichit voitures, circuits et swaps GT7."""

from __future__ import annotations

import csv
import re
from functools import cached_property
from pathlib import Path

from .catalog import swap_cost

DATA = Path(__file__).resolve().parent.parent / "data"

HYPERCAR_KEYS = (
    "chiron", "veyron", "laferrari", "enzo", "fxx", "p1", "senna", "huayra",
    "zonda", "one-77", "carrera gt", "918 spyder", "valkyrie", "ccx", "agera",
    "jesko", "sf90", "reventon", "sian", "countach lpi", "vulcan", "monza sp",
    "speedtail", "elva", "amg one", "nismo r35",
)

TUNER_KEYS = (
    "amuse", "greddy", "re amemiya", "mine's", "nismo 380", "wicked",
    "roadster shop", "chris holstrom", "eckert", "greening", "garage rcr",
)

AWD_KEYS = (
    "quattro", "impreza", "wrx", "sti", "lancer evolution", "evolution final",
    "evolution iii", "evolution iv", "evolution v", "evolution vi",
    "evolution viii", "evolution ix", "celica gt-four", "gt-four",
    "focus rs", "raptor", "urus", "aventador", "huracan", "veneno",
    "sport quattro", "tts coupe", "escudo", "jimny", "rav4", "land cruiser",
    "tundra", "alphard", "unimog", "ioniq", "model s", "model 3", "taycan",
    "e-tron", "a 45 amg", "gr yaris", "gr corolla", "gto twin turbo",
    "918 spyder", "959", "g70 3.3t awd", "g70 gr4", "focus gr.b",
    "mustang gr.b", "86 gr.b", "nsx gr.b", "gt-r gr.b", "rcz gr.b",
    "wrx gr", "lancer evolution final gr", "genesis gr.b", "delta hf",
    "integrale", "countach",  # wait no
)

# Fine-grained name rules applied after generic keys.
AWD_NAME_RE = re.compile(
    r"quattro|impreza|wrx|lancer evolution|celica gt-four|gt-four|"
    r"focus rs|svt raptor|urus|aventador|hurac[aá]n|veneno|"
    r"tts coupe|escudo|jimny|rav4|land cruiser|tundra trd|alphard|"
    r"unimog|ioniq|model s |model 3 |taycan|e-tron|a 45 amg|"
    r"gr yaris|gr corolla|gto twin turbo|918 spyder| 959 |"
    r"g70 3\.3t awd|gr\.b|delta hf|integrale|gt-r (?!lm)|"
    r"r32 gt-r|r33 gt-r|r34 gt-r|skyline.*gt-r \(kpgc|"
    r"s1 pikes|audi r8 |r8 4\.2|r8 coup|r8 lms|nsx '17|nsx concept-gt|"
    r"wrc|rally car|4wd|e-power|hybrid '16|ts050|gr010|919 hybrid|"
    r"r18 |908 hdi|499p|9x8|963 |m hybrid v8",
    re.I,
)

FF_NAME_RE = re.compile(
    r"civic|integra|fit hybrid|golf|polo gti|scirocco|clio|megane|"
    r"captur|twingo|205 gti|208 gti|focus st |mini cooper|500 f |"
    r"500 1\.2|panda |ds 3|demio|swift sport|prius|aqua |c-hr |"
    r"n-one|cr-v |rcz |mito |v40 |kangoo|espace f1|mazda3|"
    r"mazda 3|elantra n(?! 2025)|corsa gse|ds 21|bx 19|2008 allure|"
    r"qashqai|hiace|carry kc|corolla levin 1600(?!.*d-tuned)",
    re.I,
)

MR_NAME_RE = re.compile(
    r"nsx type r|nsx gt500|nsx gr\.|mr2 |4c |f430|458 |enzo |"
    r"f40 |f50 |laferrari|f8 tributo|296 |fxx |mp4-12c|650s |"
    r"p1 |senna|ford gt |gt40 |countach|diablo|murcielago|miura |"
    r"cayman|boxster|x-bow|mono '|super formula|sf19|sf23|"
    r"787b|r92cp|962 c|917|xjr-9|c9 '|ts020|gt-one|"
    r"tomahawk|chaparral 2x|red bull x201|f1500|f3500|"
    r"huayra|zonda|carrera gt|lfa |mc20|merak|pantera|"
    r"mangusta|strada|tempesta|stratos|r.s.01| Megane Trophy|"
    r"bac |radical|sr3 |tvr tuscan|amuse s2000|greddy fugu|"
    r"rx-vision|vision gran turismo \(gr\.1|vgt \(gr\.1|"
    r"ferrari vision|lambo v12 vgt|porsche vgt",
    re.I,
)

RR_NAME_RE = re.compile(
    r"911 |356 a|r5 turbo|r8 gordini|a110 |beetle|delorean|"
    r"alpine vgt|911 turbo|911 gt3|911 rsr|911 gt1|911 carrera",
    re.I,
)

# Explicit ID overrides (gt7info car IDs) when name rules would lie.
DRIVETRAIN_OVERRIDE = {
    2127: "FR",   # GT-R LM NISMO '15 — LMP1 FWD/FR, not 4WD GT-R
    1484: "MR",   # Countach LP400
    1481: "MR",   # Countach 25th
    1990: "MR",   # Diablo GT
    1545: "4WD",  # Murcielago LP640 — AWD
    1770: "4WD",
    3392: "4WD",
    2167: "4WD",  # GT-R '17
    3345: "4WD",
    3553: "4WD",
    3524: "4WD",
    210: "4WD",
    489: "4WD",
    773: "4WD",
    3219: "4WD",  # NSX '17
    1365: "4WD",  # R8 4.2
    3412: "4WD",
    2171: "4WD",
    3266: "RR",   # i3
    3390: "4WD",  # Taycan
    1956: "FR",   # Viper GTS '13
    1373: "FR",
    1402: "FR",
    2138: "FR",   # Mustang GT
    82: "FR",     # Supra RZ
    205: "FR",
    1448: "FR",   # Silvia S15
    201: "FR",    # NA Roadster
    514: "FR",    # S2000
    3367: "FR",
    3418: "FR",
    3481: "FR",   # GR86
    3354: "FR",   # BRZ
    3506: "FR",
    2074: "FR",   # M4
    1399: "FR",
    3453: "FR",
    3389: "FR",
    3483: "FR",
    1507: "FR",   # SLS
    2149: "FR",
    3416: "FR",
    3485: "FR",
    1562: "FR",   # LFA
    2139: "FR",   # RC F
    3227: "FR",
    3469: "MR",
    3587: "MR",
    2162: "MR",
    1474: "MR",
    1409: "MR",
    3362: "MR",
    1504: "MR",
    1378: "MR",
    2174: "MR",
    1722: "MR",
    1540: "MR",
    3360: "MR",
    3402: "MR",
    1426: "MR",
    1935: "MR",
    3459: "4WD",
    3519: "4WD",
    3268: "RR",
    3539: "RR",
    3600: "RR",
    3311: "RR",
    3385: "RR",
    3431: "RR",
    3488: "MR",   # Cayman
    3310: "MR",
    3337: "RR",
    1796: "RR",
    3548: "4WD",  # Urus
    3473: "4WD",  # Chiron
    2049: "4WD",
    2050: "MR",
    3532: "MR",   # Valkyrie
    3371: "MR",
    3372: "MR",
    3528: "MR",
    3529: "MR",
    2060: "RR",   # kart
    3540: "4WD",
    1896: "4WD",
    3561: "4WD",
    3610: "4WD",
    3602: "4WD",  # Yangwang U9
    51: "FF",     # FTO
    37: "FF",
    204: "FF",
    203: "FF",
    821: "FF",
    3467: "FF",
    3536: "FF",
    3214: "FF",
    2141: "FF",
    3403: "FF",
    1385: "FF",
    3456: "FF",
    3601: "FF",
    3603: "FF",
    3220: "FF",
    1987: "FF",
    2155: "FF",
    1773: "FF",
    3215: "FF",
    3564: "FF",
    105: "4WD",   # 205 T16
    173: "RR",    # R5 Turbo
    829: "4WD",
    761: "4WD",
    2150: "4WD",
    2153: "4WD",
    3432: "4WD",
    451: "4WD",
    379: "4WD",
    3550: "4WD",
    3451: "4WD",
    3535: "4WD",
    3471: "4WD",
    781: "4WD",
    3384: "4WD",
    3420: "4WD",  # Focus RS
    3336: "4WD",
    3583: "4WD",
    3584: "4WD",
    3368: "4WD",
    3545: "4WD",
    3559: "4WD",
    808: "4WD",
    1927: "4WD",
    3511: "4WD",  # ID.R
    3312: "4WD",
    3313: "4WD",
    3499: "4WD",
    3605: "4WD",
    3604: "4WD",
    3334: "4WD",
    1965: "4WD",
    1646: "4WD",
    2101: "4WD",
    3606: "4WD",
    3607: "4WD",
    296: "MR",
    998: "MR",
    1067: "MR",
    3373: "MR",
    3410: "MR",
    954: "MR",
    116: "MR",
    3397: "FR",   # CLK-LM
    3349: "FR",
    3350: "FR",
    3523: "FR",
    485: "FR",
    1466: "FR",
    1470: "FR",
    1510: "MR",
    140: "MR",
    1516: "FR",
    2076: "MR",
    2077: "MR",
    2078: "MR",
    3374: "MR",
    3517: "MR",
    2108: "MR",
    2110: "MR",
    2111: "MR",
    3188: "MR",
    2107: "MR",
}

RACE_NAME_RE = re.compile(
    r"gr\.[1234b]|gt3|gt4|gt500|gt1 |gt2 |lmp|super formula|sf19|sf23|"
    r"race car|racing car|touring car|rally car|safety car|dtm|"
    r"lm nismo|lm spec|lm race|group 5|silhouette|hypercar '|"
    r"499p|9x8|963 |gr010|ts050|919 hybrid|r18 |908 hdi|787b|"
    r"xjr-9|c9 '|917|962 c|r92cp|clk-lm|gt-one|ts020",
    re.I,
)


def _norm(s: str) -> str:
    return (s or "").strip()


def slugify(text: str) -> str:
    raw = (text or "").lower().replace("'", "").replace("'", "").replace("'", "")
    raw = re.sub(r"\s+", "-", raw.strip())
    raw = re.sub(r"[^a-z0-9.()+_-]", "", raw)
    return re.sub(r"-{2,}", "-", raw).strip("-")


IMG_BASE = "https://gtplus.app/images/cars"
TRACK_IMG = "https://gtplus.app/images/tracks"

TRACK_SLUG_ALIASES = {
    "bb raceway": "broad-bean-raceway",
    "24 heures du mans racing circuit": "circuit-de-la-sarthe",
    "daytona tri-oval": "daytona-international-speedway",
    "daytona road course": "daytona-international-speedway",
    "brands hatch grand prix circuit": "brands-hatch",
    "brands hatch indy circuit": "brands-hatch",
}


def family_name(name: str) -> str:
    n = _norm(name)
    n = re.sub(r"\s+(Reverse|Clockwise|Counterclockwise)$", "", n, flags=re.I)
    if " - " in n:
        n = n.split(" - ")[0]
    if ":" in n:
        n = n.split(":")[0]
    n = re.sub(
        r"\s*\(Short\)|\s*No Chicane|\s*Grand Prix Circuit|\s*Indy Circuit|"
        r"\s*Grand Prix Layout.*|\s*Tourist Layout|\s*24h Layout|\s*Endurance|"
        r"\s*Sprint|\s*National|\s*Rallycross",
        "",
        n,
        flags=re.I,
    )
    return _norm(n)


def track_slug(name: str) -> str:
    fam = family_name(name).lower()
    if fam in TRACK_SLUG_ALIASES:
        return TRACK_SLUG_ALIASES[fam]
    s = slugify(fam)
    s = s.replace("nurburgringnordschleife", "nurburgring").replace("nurburgring-nordschleife", "nurburgring")
    if s.startswith("nurburgring"):
        return "nurburgring"
    if s.startswith("fuji"):
        return "fuji-international-speedway"
    return s


def car_images(maker: str, name: str) -> dict:
    full = slugify(f"{maker} {name}")
    short = slugify(name)
    return {
        "slug": full,
        "thumb": f"{IMG_BASE}/thumb/{full}.png",
        "image": f"{IMG_BASE}/{full}.jpg",
        "thumb_alt": f"{IMG_BASE}/thumb/{short}.png",
        "image_alt": f"{IMG_BASE}/{short}.jpg",
    }


def infer_category(name: str) -> str:
    n = name.lower()
    if "gr.1" in n or "gr. 1" in n:
        return "Gr.1"
    if "gr.2" in n:
        return "Gr.2"
    if "gr.3" in n:
        return "Gr.3"
    if "gr.4" in n:
        return "Gr.4"
    if "gr.b" in n:
        return "Gr.B"
    if "super formula" in n or n.startswith("sf19") or n.startswith("sf23"):
        return "Super Formula"
    if "kart" in n:
        return "Kart"
    return "Road"


def infer_car_type(name: str, category: str) -> str:
    n = name.lower()
    if "vgt" in n or "vision gran turismo" in n:
        return "Vision Gran Turismo"
    if any(k in n for k in HYPERCAR_KEYS):
        return "Hypercar"
    if any(k in n for k in TUNER_KEYS):
        return "Professionally-Tuned"
    if category != "Road" or RACE_NAME_RE.search(name):
        return "Racing Car"
    return "Road Car"


def infer_drivetrain(car_id: int, name: str, category: str) -> str:
    if car_id in DRIVETRAIN_OVERRIDE:
        return DRIVETRAIN_OVERRIDE[car_id]
    if category == "Gr.B":
        return "4WD"
    if category == "Super Formula" or category == "Kart":
        return "MR" if category == "Super Formula" else "RR"
    if AWD_NAME_RE.search(name) and "countach" not in name.lower():
        # GT-R LM already overridden. Plain "GT-R" road cars are 4WD.
        if re.search(r"gt-r lm", name, re.I):
            return "FR"
        return "4WD"
    if RR_NAME_RE.search(name):
        return "RR"
    if MR_NAME_RE.search(name):
        return "MR"
    if FF_NAME_RE.search(name):
        return "FF"
    return "FR"


def infer_pp_band(category: str, name: str) -> tuple[int | None, int | None]:
    """Fourchette PP stock indicative (pneus d'origine)."""
    n = name.lower()
    if category == "Gr.4":
        return 620, 655
    if category == "Gr.3":
        return 700, 735
    if category == "Gr.2":
        return 790, 860
    if category == "Gr.1":
        return 870, 960
    if category == "Gr.B":
        return 640, 680
    if category == "Super Formula":
        return 800, 880
    if category == "Kart":
        return 150, 220
    if "tomahawk" in n:
        return 900, 1350
    if "red bull x201" in n:
        return 900, 1100
    return None, None


def classify_track(track: dict) -> dict:
    name = track["name"]
    cat = track["category"]
    length = float(track["length"] or 0)
    straight = float(track["longest_straight"] or 0)
    corners = int(float(track["corners"] or 0))
    elev = float(track["elevation"] or 0)
    oval = bool(track["oval"])
    km = max(length / 1000.0, 0.01)
    density = corners / km
    sratio = straight / max(length, 1)

    if cat == "snow_dirt":
        surface = "snow" if "louise" in name.lower() else "dirt"
        if "barcelona" in name.lower() and "rally" in name.lower():
            surface = "dirt"
    else:
        surface = "tarmac"

    if oval or "route x" in name.lower() or "tri-oval" in name.lower():
        layout = "high_speed"
    elif sratio >= 0.28 or straight >= 1400 or (straight >= 900 and density < 3.2):
        layout = "high_speed"
    elif density >= 4.6 or (straight > 0 and straight < 480 and corners >= 10):
        layout = "technical"
    else:
        layout = "mixed"

    if elev >= 90:
        hills = "mountain"
    elif elev >= 40:
        hills = "hilly"
    else:
        hills = "flat"

    city = cat == "city"
    endurance = length >= 10000 or "24h" in name.lower() or "nordschleife" in name.lower()

    target_speed = 280
    if layout == "high_speed":
        target_speed = 340 if straight >= 1500 else 310
    elif layout == "technical":
        target_speed = 230
    else:
        target_speed = 270
    if "route x" in name.lower():
        target_speed = 450
    if oval:
        target_speed = 320

    labels = []
    if surface == "dirt":
        labels.append("Terre / rallye")
    elif surface == "snow":
        labels.append("Neige")
    if city:
        labels.append("Périphérique")
    if oval:
        labels.append("Oval")
    if endurance:
        labels.append("Endurance")
    if layout == "high_speed":
        labels.append("Très rapide")
    elif layout == "technical":
        labels.append("Technique")
    else:
        labels.append("Mixte")
    if hills != "flat":
        labels.append("Dénivelé")

    return {
        "surface": surface,
        "layout": layout,
        "hills": hills,
        "city": city,
        "oval": oval,
        "endurance": endurance,
        "corner_density": round(density, 2),
        "straight_ratio": round(sratio, 3),
        "target_speed": target_speed,
        "labels": labels,
    }


class Database:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else DATA

    @cached_property
    def countries(self) -> dict[int, dict]:
        out = {}
        path = self.root / "countries.csv"
        if not path.exists():
            return out
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = int(row["ID"])
                out[cid] = {
                    "id": cid,
                    "name": row.get("Name_fr") or row["Name"],
                    "code": row.get("Code") or "",
                }
        return out

    @cached_property
    def makers(self) -> dict[int, dict]:
        countries = self.countries
        out = {}
        with open(self.root / "makers.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = int(row["Country"]) if row.get("Country") not in (None, "") else 0
                region = countries.get(cid, {"name": "Autres", "code": ""})
                out[int(row["ID"])] = {
                    "id": int(row["ID"]),
                    "name": row["Name"],
                    "country": cid,
                    "region": region["name"],
                    "region_code": region.get("code") or "",
                }
        return out

    @cached_property
    def cars(self) -> list[dict]:
        makers = self.makers
        cars = []
        with open(self.root / "cars.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = int(row["ID"])
                name = _norm(row["ShortName"])
                maker_id = int(row["Maker"])
                maker = makers.get(maker_id, {"name": "Inconnu"})
                category = infer_category(name)
                car_type = infer_car_type(name, category)
                drivetrain = infer_drivetrain(cid, name, category)
                pp_lo, pp_hi = infer_pp_band(category, name)
                full = f"{maker['name']} {name}"
                imgs = car_images(maker["name"], name)
                cars.append({
                    "id": cid,
                    "name": name,
                    "full_name": full,
                    "maker_id": maker_id,
                    "maker": maker["name"],
                    "region_id": maker.get("country", 0),
                    "region": maker.get("region") or "Autres",
                    "category": category,
                    "car_type": car_type,
                    "drivetrain": drivetrain,
                    "pp_lo": pp_lo,
                    "pp_hi": pp_hi,
                    "is_race": car_type == "Racing Car" or category.startswith("Gr.") or category in ("Super Formula", "Kart"),
                    "search": f"{full} {category} {drivetrain} {car_type} {maker.get('region','')}".lower(),
                    **imgs,
                })
        cars.sort(key=lambda c: c["full_name"].lower())
        # attach swaps later
        swaps_by_car = self.swaps_by_car
        for c in cars:
            c["swaps"] = swaps_by_car.get(c["id"], [])
            c["has_swap"] = bool(c["swaps"])
        return cars

    @cached_property
    def cars_by_id(self) -> dict[int, dict]:
        return {c["id"]: c for c in self.cars}

    @cached_property
    def swaps_by_car(self) -> dict[int, list]:
        # engineswaps.csv: NewCar,OriginalCar,EngineName
        # NewCar = recipient, OriginalCar = donor
        raw = []
        with open(self.root / "swaps.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                raw.append((int(row["NewCar"]), int(row["OriginalCar"]), row["EngineName"]))
        # Need car names: load cars.csv lightly
        names = {}
        makers = self.makers
        with open(self.root / "cars.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                mid = int(row["Maker"])
                maker = makers.get(mid, {"name": "?"})["name"]
                names[int(row["ID"])] = f"{maker} {_norm(row['ShortName'])}"
        out: dict[int, list] = {}
        for recipient, donor, engine in raw:
            out.setdefault(recipient, []).append({
                "engine": engine,
                "donor_id": donor,
                "donor": names.get(donor, f"#{donor}"),
                "price": swap_cost(engine),
            })
        return out

    @cached_property
    def tracks(self) -> list[dict]:
        out = []
        with open(self.root / "tracks.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    tid = int(row["ID"])
                except (TypeError, ValueError):
                    continue
                track = {
                    "id": tid,
                    "name": _norm(row["Name"]),
                    "country": row.get("Country"),
                    "category": _norm(row.get("Category") or "circuit"),
                    "length": float(row["Length"] or 0),
                    "longest_straight": float(row["LongestStraight"] or 0),
                    "elevation": float(row["ElevationDiff"] or 0) if row.get("ElevationDiff") not in (None, "?", "") else 0.0,
                    "corners": int(float(row["NumCorners"] or 0)),
                    "oval": str(row.get("IsOval") or "0") == "1",
                    "reverse": str(row.get("IsReverse") or "0") == "1",
                    "no_rain": str(row.get("NoRain") or "0") == "1",
                    "layout": row.get("LayoutNumber"),
                }
                track["profile"] = classify_track(track)
                track["search"] = track["name"].lower()
                track["family"] = family_name(track["name"])
                track["base_id"] = int(row["Base"]) if row.get("Base") not in (None, "") else tid
                cid = int(row["Country"]) if row.get("Country") not in (None, "") else 0
                track["region_id"] = cid
                out.append(track)
        countries = self.countries
        for t in out:
            t["region"] = countries.get(t.get("region_id"), {}).get("name") or "Autres"
            t["slug"] = track_slug(t["family"] or t["name"])
            t["thumb"] = f"{TRACK_IMG}/{t['slug']}.jpg"
            t["thumb_alt"] = t["thumb"]
        out.sort(key=lambda t: t["name"].lower())
        return out

    @cached_property
    def tracks_by_id(self) -> dict[int, dict]:
        return {t["id"]: t for t in self.tracks}

    def search_cars(self, q="", category=None, drivetrain=None, car_type=None, has_swap=None,
                    maker_id=None, region_id=None, limit=80):
        q = (q or "").strip().lower()
        hits = []
        for c in self.cars:
            if q and q not in c["search"]:
                continue
            if maker_id is not None and c["maker_id"] != int(maker_id):
                continue
            if region_id is not None and c.get("region_id") != int(region_id):
                continue
            if category and c["category"] != category and not (
                category.startswith("N") and c["category"] == "Road"
            ):
                continue
            if drivetrain and c["drivetrain"] != drivetrain:
                continue
            if car_type and c["car_type"] != car_type:
                continue
            if has_swap is True and not c["has_swap"]:
                continue
            hits.append(c)
            if len(hits) >= limit:
                break
        return hits

    def garage(self) -> dict:
        regions: dict[int, dict] = {}
        makers_out = []
        for m in sorted(self.makers.values(), key=lambda x: x["name"].lower()):
            count = sum(1 for c in self.cars if c["maker_id"] == m["id"])
            if not count:
                continue
            rid = m.get("country", 0)
            regions.setdefault(rid, {
                "id": rid,
                "name": m.get("region") or "Autres",
                "code": m.get("region_code") or "",
                "count": 0,
            })
            regions[rid]["count"] += count
            makers_out.append({
                "id": m["id"],
                "name": m["name"],
                "region_id": rid,
                "region": m.get("region") or "Autres",
                "count": count,
            })
        swap_count = sum(len(c["swaps"]) for c in self.cars)
        cars_min = [{
            "id": c["id"],
            "name": c["name"],
            "full_name": c["full_name"],
            "maker_id": c["maker_id"],
            "maker": c["maker"],
            "region_id": c.get("region_id", 0),
            "category": c["category"],
            "drivetrain": c["drivetrain"],
            "has_swap": c["has_swap"],
            "swaps": c["swaps"],
            "thumb": c.get("thumb"),
            "thumb_alt": c.get("thumb_alt"),
            "image": c.get("image"),
        } for c in self.cars]
        return {
            "regions": sorted(regions.values(), key=lambda r: (-r["count"], r["name"])),
            "makers": makers_out,
            "cars": cars_min,
            "coverage": {
                "cars": len(self.cars),
                "swaps": swap_count,
                "patch": "1.71 (août 2026)",
                "cars_note": "Liste gt7info : les 4 voitures 1.71 (Caterham Seven, IONIQ 6 N, Chaser, Mark II) sont présentes.",
                "swaps_note": "Swaps gt7info + 10 combinaisons officielles 1.71. Des swaps ajoutés entre 1.62 et 1.70 peuvent manquer.",
            },
        }

    def circuits(self) -> dict:
        countries = self.countries
        families: dict[int, dict] = {}
        for t in self.tracks:
            bid = t.get("base_id") or t["id"]
            fam = families.setdefault(bid, {
                "id": bid,
                "name": t.get("family") or t["name"],
                "region_id": t.get("region_id", 0),
                "region": t.get("region") or "Autres",
                "slug": t.get("slug"),
                "thumb": t.get("thumb"),
                "variants": [],
            })
            # prefer shorter family name
            if len(t.get("family") or t["name"]) < len(fam["name"]):
                fam["name"] = t.get("family") or t["name"]
                fam["slug"] = t.get("slug")
                fam["thumb"] = t.get("thumb")
            fam["variants"].append({
                "id": t["id"],
                "name": t["name"],
                "length": t["length"],
                "corners": t["corners"],
                "reverse": t["reverse"],
                "labels": t["profile"].get("labels") or [],
                "thumb": t.get("thumb"),
            })
        circuits = sorted(families.values(), key=lambda c: c["name"].lower())
        regions: dict[int, dict] = {}
        for c in circuits:
            rid = c["region_id"]
            regions.setdefault(rid, {
                "id": rid,
                "name": c["region"],
                "count": 0,
            })
            regions[rid]["count"] += 1
        return {
            "regions": sorted(regions.values(), key=lambda r: (-r["count"], r["name"])),
            "circuits": circuits,
        }

    def search_tracks(self, q="", limit=80):
        q = (q or "").strip().lower()
        hits = []
        for t in self.tracks:
            if q and q not in t["search"]:
                continue
            hits.append(t)
            if len(hits) >= limit:
                break
        return hits
