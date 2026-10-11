import os
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from src.utils import ROOT, validate_input
from src.routing import route, LABELS
from src.priority import LEVELS

COLUMNS = ["report_id", "timestamp", "text", "zone", "predicted_category", "priority", "service", "status", "submission_id", "data_source"]

def default_path():
    # Utile aussi pour isoler les tests : aucun test ne modifie le CSV de démonstration livré.
    return Path(os.environ.get("TAZAPULSE_REPORTS_PATH", str(ROOT / "data/demo_reports.csv")))

def read_reports(path=None):
    path = Path(path or default_path())
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=COLUMNS)
    try:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError) as exc:
        raise ValueError("Le fichier de signalements est illisible. Conservez une copie avant de le réparer.") from exc
    missing = set(COLUMNS[:8]) - set(frame.columns)
    if missing:
        raise ValueError("Colonnes absentes du CSV : " + ", ".join(sorted(missing)))
    for name in COLUMNS[8:]:
        if name not in frame:
            frame[name] = ""
    if not frame.empty:
        if frame.report_id.duplicated().any() or not frame.report_id.str.fullmatch(r"TZA-\d+").all():
            raise ValueError("Les identifiants du CSV sont invalides ou dupliqués.")
        if not frame.predicted_category.isin(LABELS).all() or not frame.priority.isin(LEVELS).all():
            raise ValueError("Le CSV contient une catégorie ou une priorité inconnue.")
        if pd.to_datetime(frame.timestamp, format="ISO8601", utc=True, errors="coerce").isna().any():
            raise ValueError("Le CSV contient une date invalide.")
    return frame[COLUMNS]

def next_report_id(reports):
    numbers = [int(match.group(1)) for value in reports.get("report_id", []) if (match := re.fullmatch(r"TZA-(\d+)", str(value)))]
    return f"TZA-{max(numbers, default=0) + 1:04d}"

@contextmanager
def _lock(path):
    lock_path = path.with_suffix(".csv.lock")
    deadline = time.monotonic() + 5
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise OSError("Enregistrement occupé. Réessayez dans quelques secondes.")
            time.sleep(.05)
    try:
        os.close(fd)
        yield
    finally:
        lock_path.unlink(missing_ok=True)

def save_report(analysis, submission_id, path=None):
    validate_input(analysis["text"], analysis["zone"])
    if analysis["category"] not in LABELS or analysis["priority"]["level"] not in LEVELS:
        raise ValueError("Analyse invalide : relancez l’analyse du signalement.")
    if not submission_id:
        raise ValueError("Identifiant de confirmation manquant.")
    path = Path(path or default_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock(path):
        reports = read_reports(path)
        previous = reports.loc[reports.submission_id == submission_id]
        if not previous.empty:
            return previous.iloc[0].to_dict()
        row = {"report_id": next_report_id(reports), "timestamp": datetime.now(timezone.utc).isoformat(),
               "text": analysis["text"].strip(), "zone": analysis["zone"].strip(),
               "predicted_category": analysis["category"], "priority": analysis["priority"]["level"],
               "service": route(analysis["category"]), "status": "ROUTED_DEMO",
               "submission_id": submission_id, "data_source": "USER INPUT / DEMO ONLY"}
        updated = pd.concat([reports, pd.DataFrame([row])], ignore_index=True)
        temp = path.with_suffix(".csv.tmp")
        try:
            updated.to_csv(temp, index=False, encoding="utf-8")
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)
        return row
