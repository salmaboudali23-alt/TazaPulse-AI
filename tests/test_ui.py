import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from streamlit.testing.v1 import AppTest
from src.seed_data import ensure_demo, DEMO_EXAMPLES
from src.storage import read_reports
from src.utils import ROOT
from src import ui

class UIFinishTests(unittest.TestCase):
    def test_home_cta_and_seven_clickable_examples_through_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = ensure_demo(Path(tmp) / 'reports.csv')
            with patch.dict(os.environ, {'TAZAPULSE_REPORTS_PATH': str(path)}):
                app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
                app.button(key='home_start').click().run()
                self.assertEqual(app.sidebar.radio[0].value, 'Signaler un problème')
                for index, (text, category) in enumerate(DEMO_EXAMPLES):
                    with self.subTest(scenario=index + 1):
                        app.button(key=f'example_{index}').click().run()
                        self.assertEqual(len(app.exception), 0)
                        self.assertEqual(app.text_area[0].value, text)
                        self.assertFalse(any(b.key == 'confirm' for b in app.button), 'Un exemple ne doit pas analyser automatiquement')
                        self.assertEqual(len(read_reports(path)), 40 + index)
                        next(b for b in app.button if b.label == 'Analyser mon signalement').click().run()
                        self.assertEqual(len(app.exception), 0)
                        self.assertEqual(app.session_state['analysis']['category'], category)
                        self.assertIn(ui.CATEGORY_NAMES[category], '\n'.join(m.value for m in app.markdown))
                        if category == 'VOIRIE':
                            self.assertIn(app.session_state['analysis']['priority']['level'], ['Élevée', 'Critique'])
                        app.button(key='confirm').click().run()
                        self.assertEqual(len(app.exception), 0)
                        self.assertIn(f'TZA-{41 + index:04d}', app.success[0].value)
                        self.assertEqual(len(read_reports(path)), 41 + index)
                        app.run()
                        self.assertEqual(len(read_reports(path)), 41 + index)
                        app.button(key='saved_dashboard').click().run()
                        self.assertEqual(len(app.exception), 0)
                        self.assertEqual(app.metric[0].value, str(41 + index))
                        self.assertEqual(len(app.get('plotly_chart')), 4)
                        app.sidebar.radio[0].set_value('Signaler un problème').run()

    def test_original_text_and_zone_are_escaped_in_html(self):
        with patch.object(ui.st, 'markdown') as render:
            ui.quote('<img src=x onerror=alert(1)> الماء', '<script>demo</script>')
            output = render.call_args.args[0]
            self.assertNotIn('<img', output)
            self.assertNotIn('<script>', output)
            self.assertIn('&lt;img', output)
            self.assertIn('dir="auto"', output)

    def test_category_labels_are_complete_and_priority_is_written(self):
        for code, name in ui.CATEGORY_NAMES.items():
            with self.subTest(category=code), patch.object(ui.st, 'markdown') as render:
                ui.analysis_cards({'category':code, 'confidence':.9, 'priority':{'level':'Critique'}})
                output = render.call_args.args[0]
                self.assertIn(name, output)
                self.assertIn('Critique', output)
                self.assertNotIn('...', output)

    def test_insights_report_ties_without_false_ranking(self):
        reports = pd.DataFrame({'predicted_category':['EAU','DECHETS'], 'zone':['Zone A','Zone C']})
        result = ui.insights(reports, pd.DataFrame({'count':[1,1]}))
        self.assertIn('égalité', result[0])
        self.assertIn('Aucun groupe', result[2])
        self.assertNotIn('deuxième', ' '.join(result))

    def test_similarity_wording_and_bidirectional_text(self):
        self.assertEqual(ui.similarity_message(0), 'Aucun signalement suffisamment similaire détecté dans cette zone.')
        self.assertEqual(ui.similarity_message(1), 'Un signalement similaire détecté dans cette zone.')
        self.assertEqual(ui.similarity_message(3), '3 signalements similaires détectés dans cette zone.')
        self.assertTrue(ui.is_rtl('الما مقطوع'))
        self.assertFalse(ui.is_rtl('Eau coupée'))

if __name__ == '__main__':
    unittest.main()
