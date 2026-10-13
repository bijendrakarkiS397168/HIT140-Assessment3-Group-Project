"""Tests of historical feature reconstruction and the bundled real data."""
import sys
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_dataset import form_snapshot, team_history, read_history, build
from project import ROOT, ingest, split_matches, expanding_folds


class HistoryTests(unittest.TestCase):
    def source(self):
        h = pd.DataFrame({'date': pd.date_range('2025-01-01', periods=12, freq='7D', tz='UTC'),
                          'gf': range(12), 'ga': [1] * 12, 'tournament': ['Friendly'] * 12,
                          'history_id': [f'ARTIFICIAL_{i}' for i in range(12)]})
        h['conservative_known_by_utc'] = h.date + pd.Timedelta(days=2)
        return h

    def test_prior_ten_window_values(self):
        h = self.source()
        values, evidence = form_snapshot(h, pd.Timestamp('2025-05-01T00:00:00Z'))
        self.assertAlmostEqual(values['goals_for_last10'], np.arange(2, 12).mean())
        self.assertAlmostEqual(values['goals_for_std_last10'], np.arange(2, 12).std(ddof=0))
        self.assertEqual(len(evidence['recent_history_ids']), 10)
        self.assertEqual(values['matches_last365'], 12)

    def test_current_and_future_outcomes_cannot_change_predictors(self):
        h = self.source()
        kickoff = pd.Timestamp('2025-05-01T00:00:00Z')
        expected, _ = form_snapshot(h, kickoff)
        future = h.iloc[[-1]].copy()
        future['date'] = kickoff
        future['conservative_known_by_utc'] = kickoff + pd.Timedelta(days=2)
        future['gf'], future['ga'] = 99, 88
        actual, _ = form_snapshot(pd.concat([h, future]), kickoff)
        self.assertEqual(actual, expected)

    def test_recent_unsettled_history_excluded(self):
        h = self.source()
        cutoff = h.conservative_known_by_utc.iloc[-1]
        _, evidence = form_snapshot(h, cutoff)
        self.assertNotIn(h.history_id.iloc[-1], evidence['recent_history_ids'])

    def test_bundled_real_data_contract_and_warmup(self):
        tables, audit = ingest(ROOT / 'data/raw')
        self.assertEqual(audit['matches'], 104)
        self.assertEqual(audit['team_rows'], 208)
        self.assertEqual(len(audit['shared_predictor_concepts']), 4)
        self.assertTrue(all(count == 0 for count in audit['missing_raw_features'].values()))
        train, test = split_matches(tables['2.2'])
        self.assertEqual(test.match_id.nunique(), 7)
        for _, fit, val in expanding_folds(train):
            self.assertGreaterEqual(fit.match_id.nunique(), 20)
            self.assertLess(fit.results_known_by_utc.max(), val.kickoff_utc.min())

    def test_all_real_matches_crosscheck_again_when_rebuilt(self):
        with tempfile.TemporaryDirectory(prefix='hit140_rebuild_') as tmp:
            audit = build(ROOT / 'data/sources', Path(tmp))
            self.assertEqual(audit, {'matches': 104, 'team_rows': 208, 'crosschecked': 104})
            rebuilt = pd.read_csv(Path(tmp) / 'prematch.csv')
            delivered = pd.read_csv(ROOT / 'data/raw/prematch.csv')
            pd.testing.assert_frame_equal(rebuilt, delivered)


if __name__ == '__main__':
    unittest.main(verbosity=2)
