"""Artificial unit-test fixtures only; never evidence about real football matches."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import project as p


def artificial_fixture(raw):
    """Write deliberately fictional TEST_* records inside a temporary directory."""
    rng = np.random.default_rng(140)
    raw.mkdir(parents=True, exist_ok=True)
    matches, teams, audit = [], [], []
    for i in range(104):
        kickoff = pd.Timestamp('2026-01-01T12:00:00Z') + pd.Timedelta(days=i // 2, hours=(i % 2) * 4)
        mid = f'TEST_NOT_REAL_{i:03d}'
        ta, tb = f'TEST_A_{i}', f'TEST_B_{i}'
        matches.append(dict(match_id=mid, kickoff_utc=kickoff.isoformat(),
                            results_known_by_utc=(kickoff + pd.Timedelta(hours=3)).isoformat(),
                            team_a=ta, team_b=tb, goals_a=int(rng.poisson(1.8)),
                            goals_b=int(rng.poisson(1.3)), score_definition='full_time_including_extra_time',
                            source_url='https://artificial-test.invalid/not-real'))
        for team in [ta, tb]:
            values = dict(goals_for_last10=rng.uniform(0, 4), goals_against_last10=rng.uniform(0, 4),
                          win_rate_last10=rng.uniform(0, 1), days_since_last_match=int(rng.integers(3, 20)),
                          matches_last365=int(rng.integers(6, 20)), goal_difference_std_last10=rng.uniform(.1, 3),
                          wc_appearances=int(rng.integers(0, 22)), host_advantage=int(rng.integers(0, 2)),
                          scoring_rate_last10=rng.uniform(0, 1), clean_sheet_rate_last10=rng.uniform(0, 1),
                          goals_for_std_last10=rng.uniform(.1, 3), draw_rate_last10=rng.uniform(0, 1))
            teams.append(dict(match_id=mid, team=team, **values))
            for feature in values:
                audit.append(dict(match_id=mid, team=team, feature=feature,
                                  conservative_known_by_utc=(kickoff - pd.Timedelta(days=1)).isoformat(),
                                  source_url='https://artificial-test.invalid/not-real',
                                  evidence_note='ARTIFICIAL SOFTWARE TEST ONLY'))
    pd.DataFrame(matches).to_csv(raw / 'matches.csv', index=False)
    pd.DataFrame(teams).to_csv(raw / 'prematch.csv', index=False)
    pd.DataFrame(audit).to_csv(raw / 'provenance.csv', index=False)


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='hit140_artificial_')
        self.root = Path(self.tmp.name)
        self.raw = self.root / 'raw'
        artificial_fixture(self.raw)

    def tearDown(self):
        self.tmp.cleanup()

    def edit(self, name, change):
        path = self.raw / name
        frame = pd.read_csv(path)
        change(frame)
        frame.to_csv(path, index=False)

    def test_shapes_targets_and_opponent_mapping(self):
        tables, _ = p.ingest(self.raw)
        self.assertEqual(len(tables['2.1']), 104)
        self.assertEqual(len(tables['2.2']), 208)
        self.assertEqual(len(p.FEATURES['2.1']), 8)
        self.assertEqual(len(p.FEATURES['2.2']), 8)
        self.assertEqual(len(set(p.RAW_FEATURES_21) & set(p.RAW_FEATURES_22)), 4)
        match = pd.read_csv(self.raw / 'matches.csv').iloc[0]
        raw = pd.read_csv(self.raw / 'prematch.csv')
        a, b = raw.iloc[0], raw.iloc[1]
        self.assertAlmostEqual(tables['2.1'].iloc[0].goals_for_last10_diff, a.goals_for_last10 - b.goals_for_last10)
        self.assertEqual(tables['2.1'].iloc[0].goal_difference, match.goals_a - match.goals_b)
        row = tables['2.2'].query('match_id == @match.match_id and team == @match.team_a').iloc[0]
        self.assertAlmostEqual(row.opponent_goals_against_last10, b.goals_against_last10)
        self.assertEqual(row.goals_scored, match.goals_a)

    def test_wrong_match_count_rejected(self):
        path = self.raw / 'matches.csv'
        pd.read_csv(path).iloc[:-1].to_csv(path, index=False)
        with self.assertRaisesRegex(ValueError, '104'):
            p.ingest(self.raw)

    def test_duplicate_match_rejected(self):
        self.edit('matches.csv', lambda f: f.loc.__setitem__((1, 'match_id'), f.loc[0, 'match_id']))
        with self.assertRaisesRegex(ValueError, 'Duplicate match_id'):
            p.ingest(self.raw)

    def test_team_pair_mismatch_rejected(self):
        self.edit('prematch.csv', lambda f: f.loc.__setitem__((0, 'team'), 'UNKNOWN_TEAM'))
        with self.assertRaisesRegex(ValueError, 'opposing pairs'):
            p.ingest(self.raw)

    def test_future_feature_rejected(self):
        self.edit('provenance.csv', lambda f: f.loc.__setitem__((0, 'conservative_known_by_utc'), '2030-01-01T00:00:00Z'))
        with self.assertRaisesRegex(ValueError, 'LEAKAGE'):
            p.ingest(self.raw)

    def test_missing_provenance_rejected(self):
        path = self.raw / 'provenance.csv'
        pd.read_csv(path).iloc[1:].to_csv(path, index=False)
        with self.assertRaisesRegex(ValueError, 'Missing provenance'):
            p.ingest(self.raw)

    def test_naive_time_rejected(self):
        self.edit('matches.csv', lambda f: f.loc.__setitem__((0, 'kickoff_utc'), '2026-01-01T12:00:00'))
        with self.assertRaisesRegex(ValueError, 'UTC offset'):
            p.ingest(self.raw)

    def test_non_numeric_feature_rejected(self):
        def damage(f):
            f['goals_for_last10'] = f.goals_for_last10.astype(object)
            f.loc[0, 'goals_for_last10'] = 'not_a_number'
        self.edit('prematch.csv', damage)
        with self.assertRaises(ValueError):
            p.ingest(self.raw)

    def test_wrong_year_rejected(self):
        self.edit('matches.csv', lambda f: f.loc.__setitem__((0, 'kickoff_utc'), '2000-01-01T12:00:00Z'))
        with self.assertRaisesRegex(ValueError, 'must be in 2026'):
            p.ingest(self.raw)

    def test_duplicate_fixture_with_different_id_rejected(self):
        def duplicate(f):
            f.loc[1, ['kickoff_utc', 'team_a', 'team_b']] = f.loc[0, ['kickoff_utc', 'team_a', 'team_b']].values
        self.edit('matches.csv', duplicate)
        with self.assertRaisesRegex(ValueError, 'Duplicate fixture'):
            p.ingest(self.raw)

    def test_holdout_and_folds_keep_matches_and_times_apart(self):
        tables, _ = p.ingest(self.raw)
        train, test = p.split_matches(tables['2.2'])
        self.assertFalse(set(train.match_id) & set(test.match_id))
        self.assertTrue(train.groupby('match_id').size().eq(2).all())
        self.assertTrue(test.groupby('match_id').size().eq(2).all())
        self.assertLess(train.results_known_by_utc.max(), test.kickoff_utc.min())
        for _, fit, val in p.expanding_folds(train):
            self.assertFalse(set(fit.match_id) & set(val.match_id))
            self.assertLess(fit.results_known_by_utc.max(), val.kickoff_utc.min())

    def test_delayed_results_purged(self):
        tables, _ = p.ingest(self.raw)
        frame = tables['2.1']
        train, test = p.split_matches(frame)
        mid = train.iloc[-1].match_id
        frame.loc[frame.match_id.eq(mid), 'results_known_by_utc'] = test.kickoff_utc.max() + pd.Timedelta(days=1)
        again, _ = p.split_matches(frame)
        self.assertNotIn(mid, set(again.match_id))

    def test_imputation_and_scaling_use_training_only(self):
        tables, _ = p.ingest(self.raw)
        train, test = p.split_matches(tables['2.1'])
        features = p.FEATURES['2.1']
        train.loc[train.index[0], features[0]] = np.nan
        model = p.fit_pipeline(train, features, p.TARGETS['2.1'])
        median = train[features[0]].median()
        self.assertAlmostEqual(model.steps[0][1].statistics_[0], median)
        test.loc[:, features[0]] = 1e12
        model.predict(test[features])
        self.assertAlmostEqual(model.steps[0][1].statistics_[0], median)

    def test_rank_deficiency_rejected(self):
        tables, _ = p.ingest(self.raw)
        train, _ = p.split_matches(tables['2.1'])
        train[p.FEATURES['2.1'][0]] = 1
        with self.assertRaisesRegex(ValueError, 'rank deficient'):
            p.fit_pipeline(train, p.FEATURES['2.1'], p.TARGETS['2.1'])

    def test_full_pipeline_and_transparent_model(self):
        out = self.root / 'artificial_results_never_submit'
        p.run_all(self.raw, out)
        tables, _ = p.ingest(self.raw)
        for task in ['2.1', '2.2']:
            taskdir = out / f'task_{task.replace(".", "_")}'
            artifact = json.loads((taskdir / 'model.json').read_text())
            _, test = p.split_matches(tables[task])
            expected = pd.read_csv(taskdir / 'holdout_predictions.csv').predicted
            np.testing.assert_allclose(p.predict(artifact, test), expected, rtol=1e-10, atol=1e-10)
            for name in ['diagnostic_panel.png', 'correlations.png', 'predictor_relationships.png', 'target_distribution.png']:
                self.assertGreater((taskdir / name).stat().st_size, 1000)
            self.assertEqual(len(pd.read_csv(taskdir / 'vif.csv')), 8)
            self.assertEqual(len(pd.read_csv(taskdir / 'forward_cv_metrics.csv')), 10)
        self.assertTrue((out / 'INTEGRATION_SUMMARY.md').is_file())
        self.assertTrue((out / 'run_manifest.json').is_file())


if __name__ == '__main__':
    unittest.main(verbosity=2)
