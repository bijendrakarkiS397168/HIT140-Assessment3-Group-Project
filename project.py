"""Shared, audited implementation for the four member entry points.

No download or invented data. Input contracts are documented in DATA_GUIDE.md.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import platform

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_FEATURES_21 = [
    'goals_for_last10', 'goals_against_last10', 'win_rate_last10', 'days_since_last_match',
    'matches_last365', 'goal_difference_std_last10', 'wc_appearances', 'host_advantage',
]
RAW_FEATURES_22 = [
    'goals_for_last10', 'goals_against_last10', 'days_since_last_match', 'win_rate_last10',
    'scoring_rate_last10', 'clean_sheet_rate_last10', 'goals_for_std_last10', 'draw_rate_last10',
]
FEATURES = {
    '2.1': [f'{x}_diff' for x in RAW_FEATURES_21],
    '2.2': ['goals_for_last10', 'opponent_goals_against_last10',
            'days_since_last_match', 'opponent_win_rate_last10',
            'scoring_rate_last10', 'opponent_clean_sheet_rate_last10',
            'goals_for_std_last10', 'opponent_draw_rate_last10'],
}
TARGETS = {'2.1': 'goal_difference', '2.2': 'goals_scored'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


def dates(series, name):
    """Reject naive times: a guessed timezone could invalidate leakage checks."""
    require(series.notna().all(), f'{name}: missing timestamp')
    require(series.astype(str).str.contains(r'(?:Z|[+-]\d{2}:\d{2})$', regex=True).all(),
            f'{name}: every timestamp needs Z or an explicit UTC offset')
    return pd.to_datetime(series, utc=True, errors='raise', format='mixed')


def read_csv(path, required):
    require(path.is_file(), f'Missing real input: {path}. See DATA_GUIDE.md; no results were generated.')
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    frame.columns = frame.columns.str.strip()
    require(not frame.columns.duplicated().any(), f'{path.name}: duplicate column names')
    require(set(frame.columns) == set(required),
            f'{path.name}: expected exactly columns {required}; found {frame.columns.tolist()}')
    for col in frame:
        frame[col] = frame[col].str.strip()
    return frame.replace('', np.nan)


def ingest(raw):
    """Validate scores, pair structure, feature ranges and cell-level provenance."""
    raw = Path(raw)
    match_cols = ['match_id', 'kickoff_utc', 'results_known_by_utc', 'team_a', 'team_b',
                  'goals_a', 'goals_b', 'score_definition', 'source_url']
    m = read_csv(raw / 'matches.csv', match_cols)
    require(len(m) == 104, f'Expected 104 actual matches; received {len(m)}')
    require(m.notna().all().all(), 'matches.csv: required cells are missing')
    require(m.match_id.is_unique, 'Duplicate match_id')
    require((m.team_a != m.team_b).all(), 'A team cannot play itself')
    m['kickoff_utc'] = dates(m.kickoff_utc, 'kickoff_utc')
    require(m.kickoff_utc.dt.year.eq(2026).all(), 'All target matches must be in 2026')
    fixture_keys = pd.DataFrame({'kickoff': m.kickoff_utc,
                                'pair': m[['team_a', 'team_b']].apply(lambda row: tuple(sorted(row)), axis=1)})
    require(not fixture_keys.duplicated().any(), 'Duplicate fixture under different match IDs')
    m['results_known_by_utc'] = dates(m.results_known_by_utc, 'results_known_by_utc')
    require((m.results_known_by_utc > m.kickoff_utc).all(), 'Results must become available after kickoff')
    require(m.score_definition.eq('full_time_including_extra_time').all(),
            'Use full_time_including_extra_time scores consistently, excluding shootouts. See DATA_GUIDE.md.')
    require(m.source_url.str.match(r'https?://\S+$').all(), 'Invalid match source URL')
    for col in ['goals_a', 'goals_b']:
        m[col] = pd.to_numeric(m[col], errors='raise')
        require((np.isfinite(m[col]) & (m[col] >= 0) & (m[col] % 1 == 0)).all(), 'Goals must be nonnegative integers')
    raw_features = list(dict.fromkeys(RAW_FEATURES_21 + RAW_FEATURES_22))
    p = read_csv(raw / 'prematch.csv', ['match_id', 'team'] + raw_features)
    require(len(p) == 208, f'Expected 208 pre-match team records; received {len(p)}')
    require(p[['match_id', 'team']].notna().all().all(), 'Missing team record keys')
    require(not p.duplicated(['match_id', 'team']).any(), 'Duplicate pre-match team record')
    expected = set(zip(m.match_id, m.team_a)) | set(zip(m.match_id, m.team_b))
    require(set(zip(p.match_id, p.team)) == expected, 'Pre-match records do not exactly match the 104 opposing pairs')
    for col in raw_features:
        p[col] = pd.to_numeric(p[col], errors='raise')
        values = p[col].dropna()
        require(np.isfinite(values).all(), f'{col}: nonfinite value')
        require((values >= 0).all(), f'{col}: negative value')
        if col in ['win_rate_last10', 'scoring_rate_last10', 'clean_sheet_rate_last10', 'draw_rate_last10', 'host_advantage']:
            require((values <= 1).all(), f'{col}: use fractions 0..1')
        if col == 'host_advantage':
            require(values.isin([0, 1]).all(), 'host_advantage must be 0 or 1')
        if col in ['wc_appearances', 'days_since_last_match', 'matches_last365']:
            require((values % 1 == 0).all(), f'{col}: expected whole numbers')
        if col == 'squad_mean_age':
            require(values.between(15, 50).all(), 'squad_mean_age outside plausible range; verify source')
    audit_cols = ['match_id', 'team', 'feature', 'conservative_known_by_utc', 'source_url', 'evidence_note']
    a = read_csv(raw / 'provenance.csv', audit_cols)
    require(a.notna().all().all(), 'Incomplete provenance records')
    keys = ['match_id', 'team', 'feature']
    require(not a.duplicated(keys).any(), 'Duplicate cell-level provenance')
    require(a.feature.isin(raw_features).all(), 'Provenance contains an unknown feature')
    require(set(zip(a.match_id, a.team)) <= expected, 'Provenance contains an unknown match/team')
    a['conservative_known_by_utc'] = dates(a.conservative_known_by_utc, 'conservative_known_by_utc')
    aa = a.merge(m[['match_id', 'kickoff_utc']], on='match_id', validate='many_to_one')
    require((aa.conservative_known_by_utc < aa.kickoff_utc).all(),
            'LEAKAGE: a feature was unavailable before its match kickoff')
    require(a.source_url.str.match(r'https?://\S+$').all(), 'Invalid feature source URL')
    known = set(map(tuple, a[keys].to_numpy()))
    for row in p.itertuples(index=False):
        for feature in raw_features:
            if pd.notna(getattr(row, feature)):
                require((row.match_id, row.team, feature) in known,
                        f'Missing provenance for {row.match_id}/{row.team}/{feature}')
    for task in FEATURES:
        require(len(FEATURES[task]) == 8, 'Exactly eight predictors required')
    require(len(set(RAW_FEATURES_21) & set(RAW_FEATURES_22)) <= 4, 'Too many shared predictor concepts')
    pa = m.merge(p, left_on=['match_id', 'team_a'], right_on=['match_id', 'team'], validate='one_to_one')
    pb = m.merge(p, left_on=['match_id', 'team_b'], right_on=['match_id', 'team'], validate='one_to_one')
    d21 = m[['match_id', 'kickoff_utc', 'results_known_by_utc', 'team_a', 'team_b']].copy()
    for feature in RAW_FEATURES_21:
        d21[feature + '_diff'] = pa[feature].to_numpy() - pb[feature].to_numpy()
    d21['goal_difference'] = m.goals_a - m.goals_b
    sides = []
    for own, opp, side in [(pa, pb, 'a'), (pb, pa, 'b')]:
        d = m[['match_id', 'kickoff_utc', 'results_known_by_utc']].copy()
        d['team'] = m['team_' + side]
        d['opponent'] = m['team_b' if side == 'a' else 'team_a']
        for feature in FEATURES['2.2']:
            if feature.startswith('opponent_'):
                d[feature] = opp[feature.removeprefix('opponent_')].to_numpy()
            else:
                d[feature] = own[feature].to_numpy()
        d['goals_scored'] = m['goals_' + side]
        sides.append(d)
    d22 = pd.concat(sides, ignore_index=True)
    tables = {'2.1': d21, '2.2': d22}
    summary = {'status': 'validated_input_data', 'matches': len(m), 'team_rows': len(p),
               'predictors_per_task': 8, 'shared_predictor_concepts': sorted(set(RAW_FEATURES_21) & set(RAW_FEATURES_22)),
               'missing_raw_features': p[raw_features].isna().sum().to_dict(),
               'source_warning': 'URLs and timestamps are checked structurally. Humans must verify source truth and the rolling-window calculations.'}
    return tables, summary


def input_hashes(raw):
    return {name: hashlib.sha256((Path(raw) / name).read_bytes()).hexdigest()
            for name in ['matches.csv', 'prematch.csv', 'provenance.csv']}


def prepare(raw, out):
    tables, summary = ingest(raw)
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    for task, frame in tables.items():
        frame.to_csv(out / f'task_{task.replace(".", "_")}.csv', index=False)
    summary['sha256'] = input_hashes(raw)
    save_json(out / 'data_audit.json', summary)
    return tables


def split_matches(frame, fraction=0.2):
    """Whole UTC days are held out; both team rows always stay together."""
    matches = frame[['match_id', 'kickoff_utc', 'results_known_by_utc']].drop_duplicates().copy()
    matches['day'] = matches.kickoff_utc.dt.floor('D')
    days = sorted(matches.day.unique())
    require(len(days) >= 8, 'Need at least eight distinct match days for chronological validation')
    ntest = max(1, int(np.ceil(len(days) * fraction)))
    test_ids = matches.loc[matches.day.isin(days[-ntest:]), 'match_id']
    cutoff = matches.loc[matches.match_id.isin(test_ids), 'kickoff_utc'].min()
    train_ids = matches.loc[(~matches.match_id.isin(test_ids)) &
                           (matches.results_known_by_utc < cutoff), 'match_id']
    train = frame[frame.match_id.isin(train_ids)].copy()
    test = frame[frame.match_id.isin(test_ids)].copy()
    require(train.match_id.nunique() >= 20 and test.match_id.nunique() >= 2,
            'Insufficient training/test matches')
    require(set(train.match_id).isdisjoint(test.match_id), 'Match leakage')
    require(train.results_known_by_utc.max() < test.kickoff_utc.min(), 'Outcome availability leakage')
    return train, test


def expanding_folds(train):
    """Five forward blocks after at least 20 eligible warm-up matches."""
    days = np.array(sorted(train.kickoff_utc.dt.floor('D').unique()), dtype=object)
    require(len(days) >= 6, 'Need six training days for five forward folds')
    first_validation = None
    for i, day in enumerate(days):
        cutoff = train.loc[train.kickoff_utc.dt.floor('D').eq(day), 'kickoff_utc'].min()
        if train.loc[train.results_known_by_utc < cutoff, 'match_id'].nunique() >= 20:
            first_validation = i
            break
    require(first_validation is not None and len(days) - first_validation >= 5,
            'Need 20 earlier eligible matches and five later training days for forward validation')
    blocks = np.array_split(days[first_validation:], 5)
    for fold, block in enumerate(blocks, 1):
        val = train[train.kickoff_utc.dt.floor('D').isin(block)].copy()
        cutoff = val.kickoff_utc.min()
        fit = train[(train.kickoff_utc.dt.floor('D') < block[0]) &
                    (train.results_known_by_utc < cutoff)].copy()
        require(len(fit) > 9, f'Fold {fold}: too few observations to fit eight predictors plus intercept')
        require(set(fit.match_id).isdisjoint(val.match_id), 'Fold match leakage')
        yield fold, fit, val


def pipeline():
    from sklearn.pipeline import make_pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LinearRegression
    return make_pipeline(SimpleImputer(strategy='median', keep_empty_features=True),
                         StandardScaler(), LinearRegression())


def fit_pipeline(train, features, target):
    require(not train[features].isna().all().any(),
            'A training predictor is entirely missing: collect data before fitting')
    model = pipeline()
    model.fit(train[features], train[target])
    transformed = model[:-1].transform(train[features])
    require(np.linalg.matrix_rank(np.column_stack([np.ones(len(train)), transformed])) == 9,
            'Training design is rank deficient: verify constant/collinear features before reporting coefficients')
    return model


def metrics(y, pred, training_y):
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    rmse = float(np.sqrt(mean_squared_error(y, pred)))
    span = float(np.max(training_y) - np.min(training_y))
    return {'MAE': float(mean_absolute_error(y, pred)), 'MSE': float(mean_squared_error(y, pred)),
            'RMSE': rmse, 'NRMSE_training_range': rmse / span if span else None,
            'R2': float(r2_score(y, pred)) if len(y) > 1 and np.var(y) > 0 else None}


def evaluate(task, frame, out):
    """All learned preprocessing is fitted separately on each training partition."""
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    features, target = FEATURES[task], TARGETS[task]
    train, test = split_matches(frame)
    folds = []; predictions = []
    for fold, fit, val in expanding_folds(train):
        model = fit_pipeline(fit, features, target)
        pred = model.predict(val[features])
        baseline = np.repeat(fit[target].mean(), len(val))
        for label, values in [('linear_regression', pred), ('training_mean', baseline)]:
            folds.append({'fold': fold, 'model': label, 'train_matches': fit.match_id.nunique(),
                          'validation_matches': val.match_id.nunique(),
                          **metrics(val[target], values, fit[target])})
        v = val[['match_id', 'kickoff_utc'] + (['team'] if task == '2.2' else [])].copy()
        v['actual'] = val[target]; v['predicted'] = pred; v['baseline'] = baseline; v['fold'] = fold
        predictions.append(v)
    model = fit_pipeline(train, features, target)
    pred = model.predict(test[features])
    baseline = np.repeat(train[target].mean(), len(test))
    holdout = {label: metrics(test[target], values, train[target])
               for label, values in [('linear_regression', pred), ('training_mean', baseline)]}
    holdout['negative_predictions'] = int((pred < 0).sum()) if task == '2.2' else None
    save_json(out / 'holdout_metrics.json', holdout)
    pd.DataFrame(folds).to_csv(out / 'forward_cv_metrics.csv', index=False)
    pd.concat(predictions).to_csv(out / 'forward_cv_predictions.csv', index=False)
    t = test[['match_id', 'kickoff_utc'] + (['team', 'opponent'] if task == '2.2' else ['team_a', 'team_b'])].copy()
    t['actual'] = test[target]; t['predicted'] = pred; t['baseline'] = baseline
    t['residual'] = t.actual - t.predicted
    t.to_csv(out / 'holdout_predictions.csv', index=False)
    ids = frame[['match_id', 'kickoff_utc', 'results_known_by_utc']].drop_duplicates().copy()
    ids['partition'] = np.where(ids.match_id.isin(train.match_id), 'train',
                                np.where(ids.match_id.isin(test.match_id), 'holdout', 'purged_unavailable_outcome'))
    ids.to_csv(out / 'split_manifest.csv', index=False)
    # Store the evaluation model as transparent JSON, avoiding pickle execution risks.
    imputer, scaler, regression = model.steps[0][1], model.steps[1][1], model.steps[2][1]
    original_beta = regression.coef_ / scaler.scale_
    intercept = regression.intercept_ - np.dot(original_beta, scaler.mean_)
    artifact = {'task': task, 'target': target, 'features': features,
                'imputation_medians': imputer.statistics_.tolist(),
                'coefficients': original_beta.tolist(), 'intercept': float(intercept),
                'training_matches': sorted(train.match_id.unique().tolist()),
                'note': 'Training-partition evaluation model; holdout was not used to fit it. Coefficients use original units after median imputation.'}
    save_json(out / 'model.json', artifact)
    equation = target + ' = ' + f'{intercept:.10g}' + ''.join(
        f' {b:+.10g} * {f}' for f, b in zip(features, original_beta))
    (out / 'equation.txt').write_text(equation + '\n', encoding='utf-8')
    diagnostics(task, train, model, t, out)
    return holdout


def diagnostics(task, train, model, holdout, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import statsmodels.api as sm
    from statsmodels.stats.diagnostic import het_breuschpagan
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from scipy import stats
    features, target = FEATURES[task], TARGETS[task]
    x = model[:-1].transform(train[features])
    design = sm.add_constant(x, has_constant='add')
    # Task 2.2 has two dependent responses per match: cluster uncertainty by match.
    fit = sm.OLS(train[target].to_numpy(), design).fit()
    robust = fit.get_robustcov_results(cov_type='cluster', groups=train.match_id.to_numpy()) if task == '2.2' else fit.get_robustcov_results(cov_type='HC3')
    (out / 'ols_summary.txt').write_text(robust.summary().as_text(), encoding='utf-8')
    ci = robust.conf_int()
    pd.DataFrame({'term': ['intercept_standardized'] + features, 'coefficient_standardized': robust.params,
                  'robust_standard_error': robust.bse, 'p_value': robust.pvalues,
                  'ci_95_low': ci[:, 0], 'ci_95_high': ci[:, 1]}).to_csv(out / 'coefficient_inference.csv', index=False)
    pd.DataFrame({'feature': features, 'VIF': [variance_inflation_factor(design, i + 1) for i in range(8)]}).to_csv(out / 'vif.csv', index=False)
    influence = fit.get_influence()
    cols = ['match_id'] + (['team'] if task == '2.2' else [])
    inf = train[cols].copy()
    inf['cooks_distance'] = influence.cooks_distance[0]
    inf['leverage'] = influence.hat_matrix_diag
    inf['studentized_residual'] = influence.resid_studentized_internal
    inf.to_csv(out / 'training_influence.csv', index=False)
    bp = het_breuschpagan(fit.resid, design)
    save_json(out / 'diagnostics.json', {
        'training_R2': float(fit.rsquared), 'training_adjusted_R2': float(fit.rsquared_adj),
        'breusch_pagan_LM_pvalue': float(bp[1]),
        'condition_number_standardized_design': float(np.linalg.cond(design)),
        'flagged_cooks_distance_gt_4_over_n': int((inf.cooks_distance > 4 / len(train)).sum()),
        'inference': 'match-clustered' if task == '2.2' else 'HC3 heteroskedasticity-robust',
        'caution': 'Exploratory diagnostics only. Repeated teams and time dependence remain; p-values are not causal evidence. No automatic outlier deletion.'})
    train[features + [target]].describe().to_csv(out / 'training_descriptives.csv')
    train[features].isna().sum().rename('missing_count').to_csv(out / 'training_missingness.csv')
    corr = train[features + [target]].corr()
    corr.to_csv(out / 'training_correlations.csv')
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap='coolwarm')
    ax.set_xticks(range(9), corr.columns, rotation=60, ha='right', fontsize=8)
    ax.set_yticks(range(9), corr.columns, fontsize=8)
    fig.colorbar(im, ax=ax); ax.set_title(f'Task {task}: training Pearson correlations')
    fig.tight_layout(); fig.savefig(out / 'correlations.png', dpi=160); plt.close(fig)
    fig, axes = plt.subplots(2, 4, figsize=(15, 7))
    for ax, feature in zip(axes.flat, features):
        ax.scatter(train[feature], train[target], alpha=.6, s=15)
        ax.set_xlabel(feature, fontsize=8); ax.set_ylabel(target, fontsize=8)
    fig.suptitle(f'Task {task}: training predictor relationships')
    fig.tight_layout(); fig.savefig(out / 'predictor_relationships.png', dpi=160); plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    axes[0, 0].scatter(fit.fittedvalues, fit.resid, alpha=.65)
    axes[0, 0].axhline(0, color='black', lw=1)
    axes[0, 0].set(xlabel='Training fitted target', ylabel='Training residual', title='Residuals vs fitted')
    stats.probplot(fit.resid, dist='norm', plot=axes[0, 1])
    axes[0, 1].set_title('Training residual normal Q-Q')
    axes[1, 0].scatter(holdout.actual, holdout.predicted, alpha=.65)
    low = min(holdout.actual.min(), holdout.predicted.min()); high = max(holdout.actual.max(), holdout.predicted.max())
    axes[1, 0].plot([low, high], [low, high], color='black', lw=1)
    axes[1, 0].set(xlabel='Actual', ylabel='Predicted', title='Untouched chronological holdout')
    axes[1, 1].scatter(inf.leverage, inf.cooks_distance, alpha=.65)
    axes[1, 1].axhline(4 / len(train), color='red', lw=1)
    axes[1, 1].set(xlabel='Leverage', ylabel="Cook's distance", title='Training influence (review, do not auto-delete)')
    fig.suptitle(f'Task {task}: regression diagnostics')
    fig.tight_layout(); fig.savefig(out / 'diagnostic_panel.png', dpi=160); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].hist(train[target], bins='auto', edgecolor='white'); axes[0].set(xlabel=target, ylabel='Training observations')
    axes[1].boxplot(train[target]); axes[1].set_ylabel(target)
    fig.tight_layout(); fig.savefig(out / 'target_distribution.png', dpi=160); plt.close(fig)


def predict(artifact, frame):
    features = artifact['features']
    x = frame[features].apply(pd.to_numeric, errors='raise').to_numpy(dtype=float)
    require(not np.isinf(x).any(), 'Infinite prediction input')
    x = np.where(np.isnan(x), np.asarray(artifact['imputation_medians']), x)
    return artifact['intercept'] + x @ np.asarray(artifact['coefficients'])


def run_all(raw, out):
    out = Path(out)
    tables = prepare(raw, out / 'prepared')
    results = {}
    for task, frame in tables.items():
        results[task] = evaluate(task, frame, out / f'task_{task.replace(".", "_")}')
    versions = {p: importlib.metadata.version(p) for p in ['numpy', 'pandas', 'scipy', 'scikit-learn', 'statsmodels', 'matplotlib']}
    save_json(out / 'run_manifest.json', {'status': 'completed_on_validated_input_data',
              'python': platform.python_version(), 'packages': versions, 'input_sha256': input_hashes(raw),
              'predictors': FEATURES, 'seed': 'not needed: deterministic chronological splits and OLS',
              'split': 'last 20% of UTC match days held out; five forward folds within earlier days; unavailable training outcomes purged',
              'score_definition': 'full_time_including_extra_time'})
    lines = ['# Generated integration summary', '',
             'These results describe the supplied data only. Check source authenticity before submission.', '']
    for task, result in results.items():
        lines += [f'## Task {task}', '', 'Chronological holdout:', '',
                  '| Model | MAE | MSE | RMSE | NRMSE (training range) | R² |', '|---|---:|---:|---:|---:|---:|']
        for name in ['linear_regression', 'training_mean']:
            r = result[name]
            vals = [('undefined' if r[k] is None else f'{r[k]:.4f}') for k in ['MAE', 'MSE', 'RMSE', 'NRMSE_training_range', 'R2']]
            lines += ['| ' + name + ' | ' + ' | '.join(vals) + ' |']
        lines += ['', f'See task_{task.replace(".", "_")}/ for coefficients, equation, fold metrics and plots.', '']
    lines += ['## Interpretation checklist', '',
              '- Compare holdout error with the training-mean baseline; do not claim a model is better without the comparison.',
              '- Describe coefficient units and direction while holding the other predictors fixed; associations are not causal effects.',
              '- Review residual patterns, VIF, influence and the count of negative goal predictions.',
              '- Report repeated-team dependence, the small sample and later-tournament distribution shifts.',
              '- Do not use the holdout to select predictors, transformations or remove observations.']
    (out / 'INTEGRATION_SUMMARY.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def entry(stage):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-open', action='store_true', help='Save results without opening the browser')
    parser.add_argument('--raw', type=Path, default=ROOT / 'data' / 'raw')
    parser.add_argument('--out', type=Path, default=ROOT / 'results')
    args = parser.parse_args()
    try:
        if stage == 'all':
            run_all(args.raw, args.out)
        elif stage == 'prepare':
            prepare(args.raw, args.out / 'prepared')
        else:
            tables, _ = ingest(args.raw)
            evaluate(stage, tables[stage], args.out / f'task_{stage.replace(".", "_")}')
    except (ValueError, FileNotFoundError, KeyError) as exc:
        parser.exit(2, f'DATA/VALIDATION ERROR: {exc}\n')
    print(f'Completed {stage}. Outputs: {args.out.resolve()}')
    if stage != 'prepare':
        from view_results import present
        present(args.out, tasks=['2.1', '2.2'] if stage == 'all' else [stage], open_browser=not args.no_open)
