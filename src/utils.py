import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZONES = ["Zone A", "Zone B", "Zone C", "Centre de Taza", "Zone rurale A", "Zone rurale B"]
DEMO_NOTICE = "Prototype de démonstration – les données et services affichés ne représentent pas des données administratives officielles."

def normalize(text):
    text = str(text).lower().replace("’", "'").replace("ـ", "")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    text = text.translate(str.maketrans("أإآى", "اااي"))
    text = re.sub(r"\bالما\b", "الماء", text)
    return re.sub(r"\s+", " ", text).strip()

def validate_input(text, zone):
    if not str(zone).strip():
        raise ValueError("Veuillez renseigner une zone ou un quartier de démonstration.")
    if len(str(zone).strip()) > 100:
        raise ValueError("La zone doit contenir au maximum 100 caractères.")
    if not str(text).strip():
        raise ValueError("Veuillez décrire le problème avant de lancer l’analyse.")
    if len(str(text).strip()) < 3 or not any(c.isalpha() for c in str(text)):
        raise ValueError("Ajoutez quelques mots pour décrire le problème.")
    if len(text) > 3000:
        raise ValueError("Le signalement est limité à 3 000 caractères.")

def extract_details(text):
    normalized = normalize(text)
    days = None
    match = re.search(r"(?:depuis|من|لمدة)\s*(\d+)\s*(?:jours?|ايام|يوم)", normalized)
    if match:
        days = int(match.group(1))
    else:
        expressions = [(1, ["depuis hier", "من البارح", "من امس"]),
            (2, ["depuis deux jours", "من يومين"]),
            (3, ["depuis trois jours", "من ثلاثة ايام", "من ثلاث ايام"]),
            (5, ["depuis cinq jours", "من خمسة ايام"]),
            (7, ["depuis une semaine", "من سيمانة", "من اسبوع"])]
        for value, phrases in expressions:
            if any(p in normalized for p in phrases):
                days = value
                break
    context = []
    for label, tokens in {"école / enfants": ["ecole", "مدرسة", "الدراري", "enfant", "اطفال"],
                          "centre de soins": ["hopital", "dispensaire", "مستوصف", "مستشفى"],
                          "route": ["route", "طريق"]}.items():
        if any(t in normalized for t in tokens):
            context.append(label)
    return {"duration_days": days, "contexts": context}
