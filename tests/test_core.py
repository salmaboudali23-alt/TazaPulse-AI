import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd
from src.analysis import analyze
from src.classifier import load_model, classify
from src.seed_data import DEMO_EXAMPLES, ensure_training, ensure_demo
from src.routing import route
from src.priority import suggest_priority
from src.similarity import find_similar, group_incidents
from src.storage import read_reports, save_report, next_report_id, COLUMNS
from src.utils import ROOT, extract_details, validate_input

class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectorizer, cls.classifier = load_model()

    def test_routing_water_and_waste(self):
        self.assertEqual(route("EAU"), "Service eau / réseau – démonstration")
        self.assertEqual(route("DECHETS"), "Service propreté / gestion des déchets – démonstration")

    def test_seven_demonstration_classifications(self):
        for text, expected in DEMO_EXAMPLES:
            with self.subTest(text=text):
                self.assertEqual(classify(text, self.vectorizer, self.classifier)["category"], expected)

    def test_priority_transparent_and_not_category_based(self):
        self.assertEqual(suggest_priority("Coupure d'eau")["level"], "Faible")
        self.assertEqual(suggest_priority(DEMO_EXAMPLES[2][0])["level"], "Élevée")
        self.assertEqual(suggest_priority("câble dangereux devant l'école", 3)["level"], "Critique")
        self.assertEqual(suggest_priority("الزبل مجموع فالحي من خمسة أيام", 3)["level"], "Élevée")

    def test_duration_and_context(self):
        for text, expected in [("depuis 3 jours", 3), ("من خمسة أيام", 5), ("من البارح", 1), ("depuis trois jours", 3), ("من ٣ أيام", 3)]:
            self.assertEqual(extract_details(text)["duration_days"], expected)
        self.assertIn("centre de soins", extract_details("مستوصف")["contexts"])

    def test_invalid_inputs_and_short_input(self):
        for text, zone in [("", "Zone A"), ("eau", " "), ("x", "Zone A"), ("12345", "Zone A")]:
            with self.assertRaises(ValueError):
                validate_input(text, zone)
        validate_input("eau", "Zone A")
        prediction = classify("xyzqvbbb", self.vectorizer, self.classifier)
        self.assertTrue(prediction["needs_review"])

    def test_dataset_balanced_and_demo_cases_not_exact_training_copies(self):
        data = pd.read_csv(ensure_training())
        self.assertEqual(len(data), 150)
        self.assertFalse(data.text.duplicated().any())
        self.assertTrue((data.groupby("label").size() == 30).all())
        for text, _ in DEMO_EXAMPLES:
            self.assertNotIn(text, data.text.tolist())

    def test_id_uses_maximum_not_row_count(self):
        self.assertEqual(next_report_id(pd.DataFrame(columns=COLUMNS)), "TZA-0001")
        self.assertEqual(next_report_id(pd.DataFrame({"report_id": ["TZA-0001", "TZA-0100"]})), "TZA-0101")

    def test_missing_csv_save_reload_and_idempotency(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reports.csv"
            self.assertTrue(read_reports(path).empty)
            result = analyze(DEMO_EXAMPLES[0][0], "Zone A", read_reports(path), self.vectorizer, self.classifier)
            row = save_report(result, "test-one", path)
            self.assertEqual(row["report_id"], "TZA-0001")
            self.assertEqual(save_report(result, "test-one", path)["report_id"], row["report_id"])
            self.assertEqual(len(read_reports(path)), 1)
            self.assertEqual(read_reports(path).iloc[0].text, result["text"])
            save_report(result, "test-two", path)
            self.assertEqual(len(read_reports(path)), 2)

    def test_concurrent_confirmations_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reports.csv"
            result = analyze("ما عندناش الما", "Zone A", read_reports(path), self.vectorizer, self.classifier)
            with ThreadPoolExecutor(max_workers=4) as pool:
                rows = list(pool.map(lambda n: save_report(result, f"submission-{n}", path), range(8)))
            self.assertEqual(len({row["report_id"] for row in rows}), 8)
            self.assertEqual(len(read_reports(path)), 8)

    def test_similarity_same_zone_and_category(self):
        reports = pd.DataFrame([
            {"report_id":"TZA-0001", "text":"الماء مقطوع", "zone":"Zone A", "predicted_category":"EAU"},
            {"report_id":"TZA-0002", "text":"الما ما جا من الصباح", "zone":"Zone A", "predicted_category":"EAU"},
            {"report_id":"TZA-0003", "text":"ما عندناش الما", "zone":"Zone B", "predicted_category":"EAU"},
            {"report_id":"TZA-0004", "text":"ما عندناش الما", "zone":"Zone A", "predicted_category":"VOIRIE"},
        ])
        matches = find_similar("ما عندناش الما", "Zone A", "EAU", reports, self.vectorizer)
        self.assertEqual(set(matches.report_id), {"TZA-0001", "TZA-0002"})

    def test_grouped_incidents_cover_all_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports = read_reports(ensure_demo(Path(tmp) / "demo.csv"))
            incidents, mapping = group_incidents(reports, self.vectorizer)
            self.assertEqual(len(reports), 40)
            self.assertEqual(incidents["count"].sum(), len(reports))
            self.assertEqual(len(mapping), len(reports))
            self.assertGreater((incidents["count"] >= 2).sum(), 0)
            for incident in incidents.incident_id:
                members = reports[reports.report_id.map(mapping) == incident]
                self.assertEqual(members.zone.nunique(), 1)
                self.assertEqual(members.predicted_category.nunique(), 1)

    def test_missing_model_is_trained_automatically(self):
        with tempfile.TemporaryDirectory() as tmp:
            vectorizer, classifier = load_model(Path(tmp))
            self.assertTrue((Path(tmp) / "classifier.pkl").exists())
            self.assertEqual(classify(DEMO_EXAMPLES[1][0], vectorizer, classifier)["category"], "EAU")

    def test_corrupted_csv_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("unrelated,columns\na,b\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_reports(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "unrelated,columns\na,b\n")

if __name__ == "__main__":
    unittest.main()
