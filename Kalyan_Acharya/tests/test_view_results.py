"""Check the presentation uses saved measurements and links valid local graphs."""
from pathlib import Path
import sys,json,unittest,tempfile,contextlib,io
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import view_results as v

class ResultsPresentationTests(unittest.TestCase):
 def fixture(self,root):
  folder=root/'task_2_1'; folder.mkdir()
  metrics={key:dict(MAE=1.2,MSE=2.25,RMSE=1.5,NRMSE_training_range=.15,R2=.1) for key in ['linear_regression','training_mean']}
  (folder/'holdout_metrics.json').write_text(json.dumps(metrics))
  (folder/'model.json').write_text(json.dumps({'features':['x']*8,'coefficients':[.5]*8}))
  (folder/'equation.txt').write_text('goal_difference = 1 + 0.5 * x')
  (folder/'holdout_predictions.csv').write_text('match_id,team_a,team_b,actual,predicted\nTEST_NOT_REAL,A<script>,B,2,1.5\n')
  (folder/'forward_cv_metrics.csv').write_text('fold,RMSE\n1,1.5\n')
  for name in ['diagnostic_panel.png','correlations.png','predictor_relationships.png','target_distribution.png']:
   (folder/name).write_bytes(b'not a real image: HTML link fixture only')
  return folder
 def test_html_escapes_team_text_and_preserves_saved_values(self):
  with tempfile.TemporaryDirectory() as name:
   root=Path(name); self.fixture(root)
   page=v.generate(root,['2.1']).read_text()
   self.assertIn('A&lt;script&gt;',page); self.assertNotIn('A<script>',page)
   self.assertIn('1.5000',page)
   for image in ['correlations.png','diagnostic_panel.png','target_distribution.png','predictor_relationships.png']:
    self.assertIn('task_2_1/'+image,page)
    self.assertTrue((root/'task_2_1'/image).exists())
 def test_no_open_prints_metrics_and_identity(self):
  with tempfile.TemporaryDirectory() as name:
   root=Path(name); self.fixture(root)
   with patch.object(v.webbrowser,'open') as opened,contextlib.redirect_stdout(io.StringIO()) as output:
    v.present(root,['2.1'],open_browser=False)
   opened.assert_not_called()
   self.assertIn('RMSE=1.5000',output.getvalue())
   self.assertIn('A<script> vs B',output.getvalue())
 def test_browser_failure_preserves_results(self):
  with tempfile.TemporaryDirectory() as name:
   root=Path(name); self.fixture(root)
   with patch.object(v.webbrowser,'open',side_effect=OSError('test browser unavailable')),contextlib.redirect_stdout(io.StringIO()) as output:
    page=v.present(root,['2.1'])
   self.assertTrue(page.is_file())
   self.assertIn('Double-click RESULTS.html',output.getvalue())
