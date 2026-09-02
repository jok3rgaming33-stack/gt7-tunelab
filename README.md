# GT7 TuneLab

Outil pour **automatiser les réglages Gran Turismo 7** : voiture + circuit + rang collectionneur + règlement → liste d’achats (atelier + GT Auto) et feuille de setup.

**Démo :** [https://gt7-tunelab.vercel.app](https://gt7-tunelab.vercel.app)

Ce n’est pas un dump officiel Polyphony. Les PP exacts, la dispo pièce par pièce et les swaps post-v1.61 peuvent différer en jeu. L’outil te donne un **plan d’attaque** à vérifier dans l’atelier.

## Lancer en local

Double-clic sur `lancer.bat`  
ou :

```bat
python -m pip install -r requirements.txt
python app.py
```

Puis ouvre [http://127.0.0.1:8765](http://127.0.0.1:8765)

## Déploiement Vercel

Flask est détecté automatiquement (`app.py` + `requirements.txt`). Les CSS/JS passent par `public/static` (CDN Vercel). Un push sur `main` redéploie la prod.

```bat
npx vercel --prod
```

## Workflow

1. Cherche une **voiture** (marque, nom, Gr.3…).
2. Cherche un **circuit**.
3. Règle ton **rang collectionneur** (débloque Sports → Extreme).
4. Ajoute le règlement si besoin :
   - pneus imposés (CH → RS, Dirt, pluie…)
   - limite PP
   - catégories (Road, Gr.1–4, Gr.B, Super Formula, Kart, N100–N1000)
   - type (Road / Racing / Hypercar / VGT / préparateur)
   - traction (FF, FR, MR, RR, 4WD)
5. Options : GT Auto, kit large, swap, pièces Ultimate (roulette).
6. **Générer le plan** — ou **Proposer une voiture** si tu n’as pas encore choisi.

## Ce que tu reçois

- Liste d’achats par étage d’atelier, avec fourchette de crédits et le *pourquoi*
- GT Auto : kit large, jantes, aéro (avant / diffuseur / aileron), swap classé
- Feuille de réglages : hauteur, ressorts, ARB, amortos, carrossage, LSD, aéro, boîte, ECU/lest, aides
- Plan de session (ordre de montage, PP, T° pneus)
- Copie presse-papiers / impression

## Données

| Source | Contenu |
| --- | --- |
| [gt7info](https://github.com/ddm999/gt7info) | IDs voitures, circuits, swaps |
| Wiki GT7 (atelier) | Catalogue Sports → Ultimate + GT Auto, rangs de déblocage |
| Moteur TuneLab | Profil de circuit (rapide / technique / terre / neige), priorité chassis vs puissance, detune PP |

La traction (FF/FR/MR/RR/4WD) est **déduite du nom** + table d’exceptions. Tu peux la forcer dans Options atelier.

## Limites honnêtes

- Pas de PP stock exact pour chaque road car (les Gr. ont une fourchette).
- Les Gr. / racing ont souvent les pièces déjà montées ou indisponibles : n’achète que ce que le menu affiche.
- Un swap change poids et PP : retaille ECU / lest / boîte après.
- Les pièces Ultimate ne s’achètent pas, elles sortent des tickets roulette 3★/4★.
- L’outil ne lit pas ta PS5 : c’est un copilote, pas un extracteur de replay.

## API

```
GET  /api/meta
GET  /api/cars?q=supra
GET  /api/tracks?q=spa
POST /api/tune     { car_id, track_id, collector_level, ... }
POST /api/suggest  { track_id, categories, drivetrains, ... }
```
