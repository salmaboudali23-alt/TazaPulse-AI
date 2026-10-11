LABELS = {
    "EAU": "💧 Eau", "VOIRIE": "🚧 Voirie / Routes",
    "DECHETS": "🗑️ Déchets / Propreté", "ECLAIRAGE": "💡 Éclairage public",
    "TRANSPORT": "🚌 Transport / Mobilité",
}
SERVICES = {
    "EAU": "Service eau / réseau – démonstration",
    "VOIRIE": "Service voirie / infrastructures – démonstration",
    "DECHETS": "Service propreté / gestion des déchets – démonstration",
    "ECLAIRAGE": "Service éclairage public – démonstration",
    "TRANSPORT": "Service mobilité / transport – démonstration",
}

def route(category):
    return SERVICES.get(category, "Orientation à vérifier par un humain – démonstration")
