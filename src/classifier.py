from pathlib import Path
import warnings
import joblib
from sklearn.exceptions import InconsistentVersionWarning
from src.utils import ROOT

LOW_CONFIDENCE = 0.45

def load_model(model_dir=None):
    model_dir = Path(model_dir or ROOT / "models")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", InconsistentVersionWarning)
            return joblib.load(model_dir / "vectorizer.pkl"), joblib.load(model_dir / "classifier.pkl")
    except (OSError, ValueError, EOFError, ImportError, InconsistentVersionWarning):
        from src.train_model import train
        return train(model_dir=model_dir, verbose=False)

def classify(text, vectorizer, classifier):
    matrix = vectorizer.transform([text])
    probabilities = classifier.predict_proba(matrix)[0]
    index = probabilities.argmax()
    return {"category": str(classifier.classes_[index]), "confidence": float(probabilities[index]),
            "needs_review": matrix.nnz == 0 or float(probabilities[index]) < LOW_CONFIDENCE,
            "unknown_vocabulary": matrix.nnz == 0}
