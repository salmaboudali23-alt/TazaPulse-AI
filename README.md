# TAZAPULSE AI

**De la voix citoyenne à l’intelligence territoriale**  
**صوتك نبض منطقتك**

Prototype pour le Taza Innovation AI Challenge 2026 — « L’IA au service du développement régional ».

## 1. Présentation et problème

Un citoyen ne connaît pas nécessairement le service compétent et décrit son problème avec ses propres mots. Ces retours non structurés sont difficiles à synthétiser. TazaPulse facilite la saisie en darija écrite, arabe ou français et produit une vue territoriale de démonstration.

## 2. Solution et périmètre réellement fonctionnel

Formulaire → classification locale → extraction simple → recherche de rapports similaires → priorité suggérée → recommandation d’un service → confirmation → sauvegarde CSV → dashboard Plotly.

Cinq catégories : eau, voirie, déchets, éclairage public, transport. Le citoyen peut utiliser une zone proposée ou renseigner une autre zone de démonstration. L’analyse ne sauvegarde rien avant confirmation. Chaque confirmation reçoit un identifiant `TZA-0001`, une date UTC et un statut `ROUTED_DEMO`. Un jeton de confirmation prévient les doubles écritures lors des relances de page.

**Les services, le routage et l’historique sont simulés.** Aucune administration n’est connectée, aucun courriel n’est envoyé, aucune résolution officielle n’est simulée. La décision finale appartient toujours à un humain.

Les données utilisées dans le prototype sont synthétiques et ne représentent pas des signalements officiels de la région de Taza.

Le routage vers les services est simulé dans le prototype. Aucun organisme administratif n’est connecté à cette version.

## 3. Architecture

Une application Streamlit Python, des modules métier simples, un modèle scikit-learn local et deux CSV. Aucune API payante, clé OpenAI, authentification, base complexe ou infrastructure distante. Après installation, l’analyse fonctionne sans réseau.

```text
Texte + zone → TF-IDF → régression logistique → catégorie
             → extraction par règles → durée / contexte
Catégorie + zone + TF-IDF → cosinus → rapprochements potentiels
Contexte + durée + rapprochements → priorité suggérée
Catégorie → service de démonstration
Confirmation → demo_reports.csv → graphiques et incidents potentiels
```

## 4. Composantes IA

- Normalisation : casse, accents, diacritiques arabes, variantes de lettres et `الما` / `الماء`.
- Représentation : TF-IDF de mots (1,2) et de caractères `char_wb` (3,5), combinés avec `FeatureUnion`.
- Classification : `LogisticRegression(C=5, max_iter=1500, random_state=42)`.
- Évaluation : séparation stratifiée 75/25 ; vectorisation apprise uniquement sur le sous-ensemble d’entraînement. Accuracy et classification report dans la console et `models/metrics.json`. Le modèle livré est ensuite réentraîné sur les 150 exemples. Les sept scénarios du jury ne sont pas des copies exactes du corpus ; ils ne constituent toutefois pas une évaluation indépendante de conception.
- Confiance : probabilité non calibrée ; avertissement sous 45 % ou pour un vocabulaire absent. Un classifieur fermé propose toujours une des cinq catégories, même pour un sujet hors périmètre.
- Similarité **lexicale**, et non compréhension sémantique générale : même catégorie, même zone normalisée, cosinus TF-IDF ≥ **0,17**, constante `SIMILARITY_THRESHOLD` dans `src/similarity.py`. Ce seuil permissif sert la démo et doit être validé sur des données réelles. Les rapprochements entre langues sont limités.
- Regroupement : ordre chronologique, affectation au représentant le plus proche au-dessus du seuil, sans fusion transitive. Le tableau inclut les singletons ; le KPI « incidents regroupés » compte uniquement les groupes de deux rapports ou plus. Le nombre de voisins d’un rapport peut différer de la taille du groupe représentatif.
- Extraction : quelques durées françaises/arabes et contextes école, enfants, soins, route. Aucune extraction générative.
- Priorité : danger +3 ; contexte école/enfants/soins +2 ; obstacle +1 ; durée ≥3 jours +2 ; 1–2 voisins +1 ou ≥3 voisins +2. Score 0 : Faible ; 1–2 : Moyenne ; 3–5 : Élevée ; ≥6 : Critique. Une catégorie ne provoque jamais une priorité critique à elle seule. Les négations et ambiguïtés ne sont pas traitées exhaustivement.
- Routage : simple correspondance avec cinq services de démonstration. Les observations territoriales utilisent des comptages, sans LLM.

## 5. Installation

Python **3.12** (version utilisée pour la validation). Les cinq dépendances directes sont fixées aux versions testées. Depuis ce dossier :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/train_model.py
streamlit run app.py
```

Si PowerShell bloque l’activation, aucun changement de politique système n’est nécessaire :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/train_model.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Linux/macOS : `source .venv/bin/activate`, puis les mêmes commandes `pip`, `python` et `streamlit`.

## 6. Lancement et entraînement

```bash
streamlit run app.py
python src/train_model.py
```

Ouvrir l’adresse locale affichée, habituellement `http://localhost:8501`. Le lanceur Windows `Lancer_TazaPulse.cmd` utilise le Python du dossier `.venv`. Les fichiers du modèle sont livrés ; s’ils sont absents ou incompatibles avec la version scikit-learn, ils sont recréés localement. Après un réentraînement manuel, redémarrer Streamlit pour recharger son cache.

## 7. Structure du projet

```text
TazaPulse/
├── app.py
├── assets/style.css
├── requirements.txt
├── README.md
├── Lancer_TazaPulse.cmd
├── .streamlit/config.toml
├── data/training_reports.csv
├── data/demo_reports.csv
├── models/classifier.pkl
├── models/vectorizer.pkl
├── models/metrics.json
├── src/
│   ├── train_model.py
│   ├── classifier.py
│   ├── similarity.py
│   ├── routing.py
│   ├── priority.py
│   ├── analysis.py
│   ├── storage.py
│   ├── seed_data.py
│   ├── ui.py
│   └── utils.py
└── tests/
    ├── test_core.py
    ├── test_app.py
    └── test_ui.py
```

## 8. Données de démonstration

**Training and demonstration data are synthetic and created solely for the hackathon prototype.**

- `training_reports.csv` : 150 phrases distinctes, 30 par catégorie, 10 formulations dans chacune des trois langues par catégorie ; colonnes `text,label`.
- `demo_reports.csv` : 40 rapports historiques fictifs (plus une saisie de démonstration déjà présente et conservée lors de la finition), six zones, dates à partir du 20 septembre 2026 ; colonnes `report_id,timestamp,text,zone,predicted_category,priority,service,status,submission_id,data_source`.
- Les historiques portent `SYNTHETIC / DEMO DATA`. Les nouvelles saisies portent `USER INPUT / DEMO ONLY` pour ne pas présenter du texte utilisateur comme une source synthétique vérifiée.
- « Centre de Taza » est seulement une zone de démonstration, sans adresse officielle ni localisation réelle.
- Les priorités historiques sont calculées à partir du texte seul. Pour les nouvelles saisies, elles intègrent les voisins disponibles au moment de la confirmation. Elles ne sont pas recalculées rétroactivement.
- Si le CSV historique est absent, le lancement restaure les 40 données synthétiques. Un CSV vide déjà présent reste vide. Les fichiers existants ne sont jamais remplacés par le générateur.
- Les nouvelles saisies restent sur disque entre deux lancements. Aucun envoi externe. Ne pas saisir de renseignements personnels pendant la présentation.

## 9. Tests et démonstration au jury

```bash
python -m unittest discover -s tests -v
```

20 tests automatiques : présentation sécurisée, sept exemples cliquables sans analyse automatique, parcours jusqu’à la confirmation et au dashboard, puis routage, les sept classifications, priorité, extraction, validation, données, IDs, CSV absent, modèle absent, sauvegarde UTF-8, confirmations idempotentes et concurrentes, similarité, regroupement et CSV invalide. Les tests Streamlit simulent analyse, confirmation, compteur passant de 40 à 41, quatre graphiques, filtres et navigation, ainsi qu’un tableau de bord vide. Ils utilisent un CSV temporaire et ne modifient pas les données livrées.

Parcours de démonstration en trois minutes :

1. Accueil : expliquer « Décrire → Structurer → Comprendre » et les données synthétiques.
2. « Signaler un problème » : Zone A, cliquer sur un exemple de démonstration ou saisir un texte, cliquer « Analyser mon signalement ».
3. Montrer catégorie, confiance, extraction, rapprochements, priorité expliquée et service simulé.
4. Cliquer « Confirmer le signalement », montrer l’ID, puis ouvrir le dashboard et son registre.
5. Montrer les limites et rappeler la validation humaine.

| Entrée | Catégorie attendue |
|---|---|
| الزبل مجموع فالحي من خمسة أيام | DECHETS |
| الما مقطوع عندنا من البارح | EAU |
| كاينة حفرة كبيرة فالطريق قدام المدرسة | VOIRIE, priorité au moins élevée |
| المصابيح ما خدامينش فالزنقة | ECLAIRAGE |
| ما كاين حتى نقل من الدوار للمدينة | TRANSPORT |
| Les déchets sont accumulés dans le quartier depuis trois jours. | DECHETS |
| Il n’y a plus d’eau depuis hier. | EAU |

## 10. Limites et dépannage

Les scores du petit test synthétique ne décrivent **pas** des performances réelles en production. Orthographes, dialectes et formulations inconnues peuvent échouer. Pas de détection fiable de demandes multi-sujets, de sarcasme ou de négation. Les rapprochements peuvent fusionner des incidents distincts, notamment car ils ne comportent pas encore de fenêtre temporelle. La priorité ne vaut ni diagnostic ni décision administrative.

Stockage CSV pour une démonstration locale, pas pour un service public de production. Un verrou de fichier et un remplacement atomique évitent les pertes lors de confirmations proches ; le regroupement reste quadratique et adapté à un petit volume. Après un arrêt brutal pendant une écriture, un fichier `demo_reports.csv.lock` peut subsister : arrêter toutes les instances, conserver une copie du CSV, puis retirer uniquement ce verrou avant de relancer. Un CSV invalide est signalé et n’est pas écrasé silencieusement.

Un modèle `joblib` est un fichier de code sérialisé : utiliser uniquement les modèles générés par ce projet. Si l’installation initiale échoue, vérifier la connexion réseau et relancer `pip install -r requirements.txt`. L’application elle-même ne demande ensuite aucune API.

## 11. Améliorations futures (non intégrées)

Priorités : **(1)** validation du corpus et des classifications avec des données réelles et des partenaires institutionnels ; **(2)** meilleure prise en charge de la darija, du hors-périmètre et des textes multilingues avec des modèles NLP plus avancés ; **(3)** regroupement évalué avec une fenêtre temporelle et une localisation appropriée.

Autres perspectives : reconnaissance vocale darija/arabe/français ; géolocalisation ; ajout de photos et Computer Vision ; intégration institutionnelle officielle ; notifications citoyennes ; vraie base de données ; application mobile. Ces fonctions ne sont pas incluses dans le MVP.

## 12. Interface et finition

Navigation latérale ouverte sur ordinateur, palette pétrole et vert sobre, cartes homogènes, textes arabes en lecture RTL, libellés complets et graphiques harmonisés. Les sept exemples préremplissent le formulaire sans analyser ni enregistrer automatiquement. Le brouillon reste disponible pendant la navigation. La confirmation présente l’identifiant local et rappelle le caractère simulé du routage.

La présentation est isolée dans `src/ui.py` et `assets/style.css`. Cette passe ne modifie ni les modèles, ni les règles de priorité, ni le seuil de similarité, ni les données existantes.

## 13. Déploiement de démonstration

Préparé pour Streamlit Community Cloud avec Python **3.12**. Depuis un dépôt GitHub contenant le contenu de ce dossier, sélectionner `app.py` comme point d’entrée (ou son chemin relatif si le projet est dans un sous-dossier). `requirements.txt` doit rester à côté de `app.py`. Inclure `assets`, `src`, `data`, `models` et `.streamlit/config.toml`. Exclure `.venv`, caches et journaux. Aucune clé ni API externe n’est nécessaire.

Les chemins applicatifs sont relatifs aux fichiers Python. Les dépendances directes sont figées ; aucun paquet système additionnel n’est identifié. Sur Linux, installation et lancement :

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.port=8501 --server.headless=true
```

Les modèles entraînés sont fournis. En cas d’absence, lancer `.venv/bin/python src/train_model.py` avant le serveur. Sur Community Cloud, le port et l’exposition réseau sont gérés par la plateforme ; ne pas imposer l’adresse locale `127.0.0.1` dans la configuration déployée.

Le stockage CSV convient à cette démonstration : les nouvelles saisies sur un hébergement peuvent disparaître lors d’un redéploiement ou d’une recréation du conteneur. Aucun stockage durable distant n’est intégré. Le déploiement Cloud lui-même n’a pas été exécuté ; la validation réalisée est locale sous Windows.

Documentation officielle : [dépendances Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

## 14. Si le navigateur affiche « connexion refusée »

Cette adresse locale exige un processus Streamlit actif. Depuis ce dossier, lancer :

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --server.headless=true
```

Puis ouvrir **http://127.0.0.1:8501/** et garder le terminal du serveur ouvert. Le raccourci `Lancer_TazaPulse.cmd` permet également de démarrer l’application. Contrôle de santé : `http://127.0.0.1:8501/_stcore/health` doit répondre `ok`. Un port occupé nécessite d’identifier l’instance existante avant d’en lancer une autre.
