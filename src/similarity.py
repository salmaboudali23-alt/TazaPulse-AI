"""Similarité lexicale multilingue, pas un modèle sémantique profond."""
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from src.utils import normalize

SIMILARITY_THRESHOLD = 0.17

def find_similar(text, zone, category, reports, vectorizer, threshold=SIMILARITY_THRESHOLD):
    if reports.empty:
        return pd.DataFrame(columns=[*reports.columns, "similarity"])
    candidates = reports.loc[(reports.predicted_category == category) & (reports.zone.map(normalize) == normalize(zone))].copy()
    if candidates.empty:
        candidates["similarity"] = pd.Series(dtype=float)
        return candidates
    scores = cosine_similarity(vectorizer.transform([text]), vectorizer.transform(candidates.text.fillna("")))[0]
    candidates["similarity"] = scores
    return candidates.loc[candidates.similarity >= threshold].sort_values("similarity", ascending=False)

def group_incidents(reports, vectorizer, threshold=SIMILARITY_THRESHOLD):
    """Groupes déterministes par représentant, catégorie et zone. Inclut les singletons.

    Chaque nouveau rapport rejoint le représentant le plus proche dépassant le seuil.
    Évite la fusion transitive de deux incidents via un rapport intermédiaire.
    """
    columns = ["incident_id", "zone", "category", "count", "priority", "example"]
    if reports.empty:
        return pd.DataFrame(columns=columns), {}
    from src.priority import LEVELS
    ordered = reports.sort_values(["timestamp", "report_id"]).reset_index(drop=True)
    vectors = vectorizer.transform(ordered.text.fillna(""))
    similarities = cosine_similarity(vectors)
    groups, representatives, assignments = [], [], {}
    for i, row in ordered.iterrows():
        matches = [(similarities[i, rep], g) for g, rep in enumerate(representatives)
                   if groups[g]["category"] == row.predicted_category and normalize(groups[g]["zone"]) == normalize(row.zone)
                   and similarities[i, rep] >= threshold]
        if matches:
            _, g = max(matches)
            groups[g]["count"] += 1
            if LEVELS.index(row.priority) > LEVELS.index(groups[g]["priority"]):
                groups[g]["priority"] = row.priority
        else:
            g = len(groups)
            representatives.append(i)
            groups.append({"incident_id": f"INC-{row.report_id}", "zone": row.zone,
                           "category": row.predicted_category, "count": 1,
                           "priority": row.priority, "example": row.text})
        assignments[row.report_id] = groups[g]["incident_id"]
    return pd.DataFrame(groups, columns=columns).sort_values("count", ascending=False), assignments
