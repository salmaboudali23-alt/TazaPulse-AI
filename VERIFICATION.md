# Vérification finale — 11 octobre 2026

## Résultat local

Python 3.12.4, Windows ; Streamlit 1.65.0 installé. Les cinq dépendances directes correspondent exactement à requirements.txt ; pip check ne trouve aucune incompatibilité. Les deux fichiers .pkl entraînés sont présents et chargés. Aucun réentraînement nécessaire pour cette passe.

20 tests automatiques réussis, 0 échec : les 15 tests existants sont conservés, complétés par cinq tests de présentation et de parcours. Commande depuis le dossier du projet : `python -m unittest discover -s tests -v`. Durée mesurée : 18,297 secondes. Les avertissements ScriptRunContext proviennent du mode test Streamlit et ne sont pas des exceptions applicatives.

## Parcours dans le navigateur

Playwright autorisé par l’utilisateur, navigateur Microsoft Edge local. Les sept parcours ont été exécutés sur une copie du CSV via le port 8502 : clic sur l’exemple, préremplissage exact sans analyse automatique, analyse, catégorie attendue, confirmation, identifiant, sauvegarde, puis compteur du dashboard. La copie passe de 41 à 48 signalements ; identifiants TZA-0042 à TZA-0048. Le scénario voirie produit une priorité élevée ou critique.

| Phrase | Catégorie obtenue | Résultat |
|---|---|---|
| الزبل مجموع فالحي من خمسة أيام | Déchets / Propreté | OK |
| الما مقطوع عندنا من البارح | Eau | OK |
| كاينة حفرة كبيرة فالطريق قدام المدرسة | Voirie / Routes | OK |
| المصابيح ما خدامينش فالزنقة | Éclairage public | OK |
| ما كاين حتى نقل من الدوار للمدينة | Transport / Mobilité | OK |
| Les déchets sont accumulés dans le quartier depuis trois jours. | Déchets / Propreté | OK |
| Il n’y a plus d’eau depuis hier. | Eau | OK |

Les cinq pages sont contrôlées à 1440 × 1000 et à 390 × 844 : navigation, formulaire, analyse, dashboard et À propos. Les captures sont inspectées visuellement. Aucun débordement horizontal à 390 pixels ; aucune exception Streamlit sur les cinq pages. Les quatre libellés des KPI du dashboard ne sont pas tronqués. Aucune erreur JavaScript non interceptée durant les sept parcours. Les citations sont échappées et le texte arabe conserve sa direction RTL.

## Préservation

Comparaison SHA-256 avec la sauvegarde de début de passe : données, modèles, modules métier et tests existants inchangés. Le CSV réel contient 41 signalements, dont 40 historiques synthétiques et une saisie déjà présente avant cette finition. Aucune confirmation des contrôles n’a été ajoutée au CSV réel. Les règles de priorité, de routage, de classification et le seuil de similarité 0,17 restent identiques.

Seuls app.py, assets/style.css, src/ui.py, .streamlit/config.toml, tests/test_ui.py et la documentation sont concernés par cette passe.

## Évaluation et limites

L’évaluation conservée dans models/metrics.json donne environ 73,7 % d’accuracy sur 38 exemples synthétiques de test. Elle ne représente pas une performance sur des signalements réels. Le modèle final fourni utilise les 150 exemples d’entraînement synthétiques.

Projet préparé pour une démonstration sur Streamlit Community Cloud, Python 3.12, point d’entrée app.py. Aucun déploiement Cloud effectif ni test Linux natif n’a été réalisé. Les écritures CSV sur hébergement ne constituent pas un stockage durable et peuvent disparaître au redéploiement. Les instructions et limites figurent dans README.md.

## Dernier démarrage

Serveur relancé sur http://127.0.0.1:8501/ ; contrôle HTTP de santé : ok. Accueil, analyse RTL et quatre graphiques vérifiés dans le navigateur après redémarrage, sans exception applicative ni erreur JavaScript. Gradations de priorité espacées pour rester lisibles. L’instance de test sur 8502 a été arrêtée. Le serveur principal reste actif.
