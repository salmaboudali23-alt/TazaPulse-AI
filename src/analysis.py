from src.utils import validate_input, extract_details
from src.classifier import classify
from src.similarity import find_similar
from src.priority import suggest_priority
from src.routing import route

TOPICS = {"EAU": "un problème d’eau", "VOIRIE": "un problème de voirie",
          "DECHETS": "un problème de déchets", "ECLAIRAGE": "un problème d’éclairage public",
          "TRANSPORT": "un problème de transport"}

def analyze(text, zone, reports, vectorizer, classifier):
    validate_input(text, zone)
    result = classify(text, vectorizer, classifier)
    matches = find_similar(text, zone, result["category"], reports, vectorizer)
    return {**result, "text": text.strip(), "zone": zone.strip(),
            "summary": f"Signalement relatif à {TOPICS[result['category']]} dans {zone.strip()}.",
            "priority": suggest_priority(text, len(matches)), "details": extract_details(text),
            "similar_count": len(matches), "similar_reports": matches,
            "service": route(result["category"])}
