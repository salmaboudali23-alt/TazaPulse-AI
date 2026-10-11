from src.utils import extract_details, normalize

LEVELS = ["Faible", "Moyenne", "Élevée", "Critique"]

def suggest_priority(text, similar_count=0):
    """Règles explicites, indépendantes de la catégorie. Jamais une décision officielle."""
    value = normalize(text)
    details = extract_details(text)
    score, reasons = 0, []
    danger = ["danger", "dangereux", "خطر", "حادث", "حريق", "طايح", "cable", "poteau", "route bloquee"]
    if any(word in value for word in danger):
        score += 3
        reasons.append("terme de danger détecté (+3)")
    if any(c in details["contexts"] for c in ["école / enfants", "centre de soins"]):
        score += 2
        reasons.append("contexte sensible : école, enfants ou soins (+2)")
    if any(word in value for word in ["حفرة", "nid de poule", "trou", "effondr", "انهيار"]):
        score += 1
        reasons.append("obstacle ou dégradation potentiellement dangereuse (+1)")
    if details["duration_days"] is not None and details["duration_days"] >= 3:
        score += 2
        reasons.append("durée mentionnée d’au moins trois jours (+2)")
    if similar_count >= 3:
        score += 2
        reasons.append("au moins trois autres signalements similaires (+2)")
    elif similar_count >= 1:
        score += 1
        reasons.append("au moins un autre signalement similaire (+1)")
    level = "Critique" if score >= 6 else "Élevée" if score >= 3 else "Moyenne" if score >= 1 else "Faible"
    return {"level": level, "score": score, "reason": "; ".join(reasons) or "aucun facteur aggravant détecté", **details}
