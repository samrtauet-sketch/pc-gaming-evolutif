# Mise à jour automatique des annonces

Ce dépôt publie le site « Mon PC Gaming Évolutif » sur GitHub Pages.
Les annonces sont dans `source/annonces.json`. Le site (`index.html`) est **généré** par `python source/construire.py` : ne modifie jamais `index.html` à la main.

## Ta mission (une fois par jour)

1. **Vérifie chaque annonce existante** (`src` = `lbc` ou `vinted`) :
   - toujours en ligne ? Prix changé ? Mets à jour `price` et `age` (« 0 j », « 3 j »…).
   - Vendue ou disparue : supprime-la, **sauf** si `construire.py` dit que la page l'utilise (config prête). Dans ce cas, garde-la et mets `"risk": "annonce probablement vendue (absente le JJ/MM)"`.
2. **Vérifie les prix du neuf** (`src` = `new`) : mets à jour `price` s'il a changé, avec la date dans `where`.
   - Frais de port : mets toujours `"port"` (montant affiché par le marchand). S'il n'est pas affiché, mets une estimation et `"est": 1`. Livraison gratuite : `"port": 0` et `"portTxt": "offerte (raison)"`. Le site affiche pour chaque pièce : prix + protection acheteur (Leboncoin/Vinted, calculée par le site) + livraison + garantie.
3. **Cherche de nouvelles bonnes affaires** (Leboncoin, Vinted, comparateurs de prix du neuf, AliExpress seulement pour les petites pièces). Pas plus de 12 annonces par catégorie : garde les meilleures (prix livré / performance, fiabilité du vendeur, proximité de Vincennes 94).
4. Mets `"mise_a_jour"` à la date du jour (AAAA-MM-JJ).
5. Lance `python source/construire.py`. S'il refuse, corrige les données (jamais le script) jusqu'à ce qu'il accepte.
6. Commit « Annonces du JJ/MM/AAAA » sur `main` (`source/annonces.json`, `source/historique.json` et `index.html`) et push. Si rien n'a changé, ne commite rien.

`source/historique.json` est rempli automatiquement par `construire.py` (un point par changement de prix) : ne le modifie jamais à la main.

Si un site est inaccessible (domaine non autorisé, 403), passe aux autres sources. Si tu n'as pu vérifier aucune annonce, ne change rien et dis précisément quels domaines ont été refusés.

## Règles de sélection (obligatoires)

- Plateforme **AM4 / DDR4** uniquement. Cartes mères micro-ATX (mATX) ou plus petites.
- **RAM** : uniquement de la RAM de **PC fixe (DIMM)**. Mets `"dimm": "ok"` seulement si le titre le dit (« PC fixe », « bureau », « desktop », « DIMM », « PC4-…-U ») ou si la gamme n'existe qu'en PC fixe (Corsair Vengeance LPX/RGB, G.Skill Ripjaws/Trident, Kingston Fury Beast…), et explique-le dans `"why"`. Sinon `"dimm": "?"` + `"ask"`. Barrettes nues sans précision : `"dimm": "risk"` + `"risk"`. Jamais de SO-DIMM (portable) ni d'ECC (serveur).
- **Pièces sensibles neuves** : alimentation, carte mère, SSD. Pas d'occasion pour celles-ci (sauf carte mère neuve vendue sur Vinted).
- Petites pièces (pâte thermique, câbles, clé USB…) : neuves (l'occasion ne fait gagner que 1 ou 2 €).
- **Arnaques** : prix plus de 40 % sous la cote → `"risk"`. Vendeur sans avis + prix bas → `"risk"`. Paiement hors plateforme demandé → n'ajoute pas l'annonce.
- **Livraison obligatoire si l'annonce n'est pas à côté de Vincennes** (plus de 15 km, ou hors Île-de-France) : n'ajoute une annonce Leboncoin éloignée que si l'envoi est proposé (« Livraison possible », bouton « Acheter »), et mets alors `"livr": 1`. Remise en main propre seulement : `"livr": 0`, et si elle est à plus de 15 km, ne l'ajoute pas (supprime-la si elle y est). En Île-de-France, mets toujours `"idf": 1` et `"km"` (distance approximative de Vincennes). Vinted et le neuf sont toujours livrés. `construire.py` n'affiche pas les annonces Leboncoin à plus de 15 km (ou sans `km`) qui n'ont pas `"livr": 1` : vérifie la livraison de chacune.
- Ne contacte aucun vendeur, ne te connecte à aucun compte, n'écris aucune donnée personnelle (nom, téléphone, adresse) : seulement la ville et le département.

## Format d'une annonce

Champs communs : `id` (2 à 20 caractères a-z0-9, unique), `n` (nom), `src` (`lbc` | `vinted` | `new` | `none`), `price` (€), `port` (frais de port, obligatoire pour lbc/vinted), `where` (ville (dép.) ou site + date du prix), `url` (https://), `age`, `seller` (« 4,8/5 (20 avis) »), `cote` (prix habituel d'occasion), `idf`, `km`, `note`, `ask`, `risk`, `deal: 1` (bonne affaire), `est: 1` (frais de port estimés), `livr` (1 = envoi possible, 0 = main propre seulement ; obligatoire pour lbc).

Par catégorie :
- `cpu` : `cpuF` (1,0 = Ryzen 5 3600 ; 1,22 = 5600X ; 1,5 = 5800X3D), `watt`, `cooler` (true / false / "?"), `pcie3: 1` si PCIe 3.0 seulement (5500, 5600G…).
- `gpu` : `idx` (≈ performance relative en 1440p, RX 6700 XT ≈ 104), `vram` (Go), `w` (consommation W), `nv: 1` si NVIDIA, `x8: 1` si PCIe x8. Pour un nouveau modèle, ajoute aussi `len` (longueur mm), `pins8` (nombre de connecteurs 8 broches), `psurec` (alimentation conseillée par le fabricant, W), et si possible `rel: [1080p, 1440p]` (RX 6700 XT = 100).
- `ram` : `gb`, `sticks` (2, 4 ou "?"), `mhz`, `dimm`, `why`.
- `mb` : `slots` (2, 4 ou "?"), `pcie3: 1` pour les A520.
- `psu` : `watt`.
- Facultatif pour toutes : `specs` (liste de caractéristiques), `pw` (note de puissance /10 hors cpu/gpu).

Aucun texte ne doit contenir `<`, `>`, `` ` ``, `${`, `javascript:` (le script de construction refuse).
