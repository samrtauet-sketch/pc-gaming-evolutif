"""Vérifie source/annonces.json puis génère index.html (le site publié).

Usage : python source/construire.py [--artefact chemin.html]
Refuse de construire (code de sortie 1) si une donnée est invalide ou dangereuse.
"""
import json, os, re, sys, datetime

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
CSP = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src data:; connect-src 'self' https://*.trycloudflare.com; "
       "base-uri 'none'; form-action 'none'; object-src 'none'")
TETE = ('<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}"><meta name="referrer" content="no-referrer">'
        '<meta name="robots" content="noindex"></head><body>\n')
NUM = (int, float)
CATS_OK = ["cpu", "mb", "ram", "gpu", "ssd", "psu", "case", "cool", "fans", "wifi", "paste", "usb", "win", "strip", "tools", "screen", "dp", "kb"]
# champs obligatoires (en plus de id, n, src, price, where) pour une vraie offre de chaque catégorie
REQUIS = {"cpu": {"cpuF": NUM, "watt": NUM}, "gpu": {"idx": NUM, "vram": NUM, "w": NUM},
          "ram": {"gb": NUM, "dimm": str}, "mb": {"slots": (int, str)}, "psu": {"watt": NUM}}
erreurs = []


def err(m):
    erreurs.append(m)


def verifier_textes(v, ou):
    """Aucune balise HTML ni code dans les données (elles viennent d'annonces publiques)."""
    if isinstance(v, str):
        if re.search(r"[<>`]|javascript:|data:|\$\{", v, re.I):
            err(f"{ou} : caractère ou texte interdit dans « {v[:60]} »")
        if len(v) > 600:
            err(f"{ou} : texte trop long")
    elif isinstance(v, list):
        for k, x in enumerate(v):
            verifier_textes(x, f"{ou}[{k}]")
    elif isinstance(v, dict):
        for k, x in v.items():
            verifier_textes(x, f"{ou}.{k}")
    elif v is not None and not isinstance(v, (bool, int, float)):
        err(f"{ou} : type inattendu")


def main():
    page = open(os.path.join(ICI, "page.html"), encoding="utf-8").read()
    try:
        d = json.load(open(os.path.join(ICI, "annonces.json"), encoding="utf-8"))
    except ValueError as e:
        print("annonces.json n'est pas du JSON valide :", e)
        return 1
    try:
        datetime.date.fromisoformat(d.get("mise_a_jour", ""))
    except ValueError:
        err("mise_a_jour doit être une date AAAA-MM-JJ")
    cats = d.get("categories")
    if not isinstance(cats, list) or [c.get("key") for c in cats] != CATS_OK:
        err(f"categories : il faut exactement ces catégories, dans cet ordre : {CATS_OK}")
        cats = cats if isinstance(cats, list) else []
    verifier_textes(d, "annonces")
    ids = {}
    for c in cats:
        items = c.get("items")
        if not isinstance(items, list) or not items:
            err(f"{c.get('key')} : aucune annonce")
            continue
        for i in items:
            ou = f"{c.get('key')}/{i.get('id')}"
            if not re.fullmatch(r"[a-z0-9]{2,20}", str(i.get("id", ""))):
                err(f"{ou} : id invalide (2 à 20 caractères a-z, 0-9)")
            if i.get("id") in ids:
                err(f"{ou} : id en double")
            ids[i.get("id")] = c.get("key")
            if not isinstance(i.get("n"), str) or not i["n"]:
                err(f"{ou} : nom (n) manquant")
            if i.get("src") not in ("lbc", "vinted", "new", "none"):
                err(f"{ou} : src doit être lbc, vinted, new ou none")
            if not isinstance(i.get("price"), NUM) or i["price"] < 0 or i["price"] > 3000:
                err(f"{ou} : prix invalide")
            if i.get("src") == "none":
                continue
            if not re.fullmatch(r"https://[A-Za-z0-9.-]+\.[a-z]{2,}(/[^\s\"'<>]*)?", str(i.get("url", ""))):
                err(f"{ou} : url doit commencer par https://")
            if i.get("src") in ("lbc", "vinted") and not isinstance(i.get("port"), NUM):
                err(f"{ou} : frais de port (port) manquants")
            for k, t in REQUIS.get(c.get("key"), {}).items():
                if not isinstance(i.get(k), t):
                    err(f"{ou} : champ {k} manquant ou invalide")
            if c.get("key") == "ram" and i.get("dimm") not in ("ok", "?", "risk"):
                err(f"{ou} : dimm doit être ok, ? ou risk")
            if c.get("key") == "ram" and i.get("dimm") == "ok" and not i.get("why"):
                err(f"{ou} : dimm ok sans justification (why)")
    # pièces utilisées par la page (configs prêtes, montage par défaut) : elles doivent exister
    for cat, pid in set(re.findall(r'\b(' + "|".join(CATS_OK) + r'):"([a-z0-9]+)"', page)):
        if ids.get(pid) != cat:
            err(f"la page utilise {cat} « {pid} » (config prête ou montage par défaut) : cette annonce doit rester dans annonces.json, ou il faut modifier la config dans page.html")
    if erreurs:
        print("CONSTRUCTION REFUSÉE :")
        for e in erreurs:
            print(" -", e)
        return 1
    # Historique des prix : un point par annonce à chaque changement de prix (source/historique.json)
    ph = os.path.join(ICI, "historique.json")
    try:
        hist = json.load(open(ph, encoding="utf-8"))
        assert isinstance(hist, dict)
    except (OSError, ValueError, AssertionError):
        hist = {}
    jour = d["mise_a_jour"]
    for c in cats:
        for i in c["items"]:
            if i.get("src") == "none":
                continue
            h = [x for x in hist.get(i["id"], []) if isinstance(x, list) and len(x) == 2 and isinstance(x[1], NUM)]
            if not h or h[-1][1] != i["price"]:
                if h and h[-1][0] == jour:
                    h[-1] = [jour, i["price"]]
                else:
                    h.append([jour, i["price"]])
            hist[i["id"]] = h[-60:]
    txt = "{\n" + ",\n".join(f'"{k}": {json.dumps(v)}' for k, v in sorted(hist.items())) + "\n}\n"
    if not os.path.exists(ph) or open(ph, encoding="utf-8").read() != txt:
        open(ph, "w", encoding="utf-8", newline="\n").write(txt)
    d = dict(d, historique={k: v for k, v in hist.items() if k in ids})
    corps = page.replace("/*@@DONNEES@@*/null", json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"), 1)
    assert "/*@@DONNEES@@*/" not in corps
    open(os.path.join(RACINE, "index.html"), "w", encoding="utf-8", newline="\n").write(TETE + corps.rstrip("\n") + "\n</body></html>\n")
    if "--artefact" in sys.argv:
        open(sys.argv[sys.argv.index("--artefact") + 1], "w", encoding="utf-8", newline="\n").write(corps)
    print(f"OK : {len(ids)} annonces, mise à jour du {d['mise_a_jour']} -> index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
