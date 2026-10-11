"""Tests réels des interactions Streamlit, avec CSV temporaire isolé."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from src.seed_data import ensure_demo, DEMO_EXAMPLES
from src.storage import read_reports
from src.utils import ROOT

class AppTests(unittest.TestCase):
    def test_citizen_confirmation_dashboard_and_all_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = ensure_demo(Path(tmp) / "reports.csv")
            with patch.dict(os.environ, {"TAZAPULSE_REPORTS_PATH":str(path)}):
                app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
                self.assertEqual(len(app.exception), 0)
                app.sidebar.radio[0].set_value("Signaler un problème").run()
                app.text_area[0].set_value(DEMO_EXAMPLES[2][0])
                next(b for b in app.button if b.label == "Analyser mon signalement").click().run()
                self.assertEqual(len(app.exception), 0)
                self.assertEqual(app.session_state["analysis"]["category"], "VOIRIE")
                self.assertIn(app.session_state["analysis"]["priority"]["level"], ["Élevée", "Critique"])
                app.button(key="confirm").click().run()
                self.assertEqual(len(app.exception), 0)
                self.assertEqual(len(read_reports(path)), 41)
                self.assertIn("TZA-0041", app.success[0].value)
                app.run()
                self.assertEqual(len(read_reports(path)), 41)
                app.sidebar.radio[0].set_value("Dashboard territorial").run()
                self.assertEqual(len(app.exception), 0)
                self.assertEqual(app.metric[0].value, "41")
                self.assertEqual(len(app.get("plotly_chart")), 4)
                app.multiselect[0].set_value(["Zone rurale B"]).run()
                self.assertEqual(len(app.exception), 0)
                for page in ["Analyse IA", "À propos", "Accueil"]:
                    app.sidebar.radio[0].set_value(page).run()
                    self.assertEqual(len(app.exception), 0)

    def test_empty_input_and_empty_dashboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"TAZAPULSE_REPORTS_PATH":str(Path(tmp) / "absent.csv")}):
                app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
                app.sidebar.radio[0].set_value("Signaler un problème").run()
                next(b for b in app.button if b.label == "Analyser mon signalement").click().run()
                self.assertEqual(len(app.exception), 0)
                self.assertTrue(any("décrire" in msg.value for msg in app.warning))
                app.sidebar.radio[0].set_value("Dashboard territorial").run()
                self.assertEqual(len(app.exception), 0)
                self.assertEqual(app.metric[0].value, "0")

if __name__ == "__main__":
    unittest.main()
