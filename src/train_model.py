"""Évaluation sur un sous-ensemble séparé, puis réentraînement final sur le corpus entier."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
import joblib
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from src.utils import ROOT, normalize
from src.seed_data import ensure_training

def build_vectorizer():
    return FeatureUnion([
        ("words", TfidfVectorizer(preprocessor=normalize, ngram_range=(1, 2), sublinear_tf=True)),
        ("chars", TfidfVectorizer(preprocessor=normalize, analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
    ])

def train(data_path=None, model_dir=None, verbose=True):
    data_path = ensure_training(data_path)
    model_dir = Path(model_dir or ROOT / "models")
    data = pd.read_csv(data_path).dropna(subset=["text", "label"]).drop_duplicates("text")
    from src.routing import LABELS
    if set(data.label) != set(LABELS) or data.groupby("label").size().min() < 5:
        raise ValueError("Le corpus doit couvrir les cinq catégories avec au moins cinq exemples chacune.")
    x_train, x_test, y_train, y_test = train_test_split(data.text, data.label, test_size=.25, stratify=data.label, random_state=42)
    vectorizer = build_vectorizer()
    classifier = LogisticRegression(C=5, max_iter=1500, random_state=42)
    classifier.fit(vectorizer.fit_transform(x_train), y_train)
    predictions = classifier.predict(vectorizer.transform(x_test))
    metrics = {"accuracy": accuracy_score(y_test, predictions), "test_size": len(y_test),
               "training_size": len(x_train), "synthetic_only": True,
               "report": classification_report(y_test, predictions, output_dict=True, zero_division=0),
               "sklearn_version": sklearn.__version__}
    if verbose:
        print(f"Accuracy (test SYNTHETIC uniquement) : {metrics['accuracy']:.3f}")
        print(classification_report(y_test, predictions, zero_division=0))
        print("Ces résultats ne représentent pas une performance réelle en production.")
    # Les métriques ci-dessus portent uniquement sur le modèle évalué avant ce réentraînement.
    vectorizer = build_vectorizer()
    classifier.fit(vectorizer.fit_transform(data.text), data.label)
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, model_dir / "vectorizer.pkl")
    joblib.dump(classifier, model_dir / "classifier.pkl")
    (model_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return vectorizer, classifier

if __name__ == "__main__":
    train()
