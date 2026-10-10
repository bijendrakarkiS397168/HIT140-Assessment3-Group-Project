"""Reconstruct real-source predictors using only conservatively eligible earlier games.

No inferred result is inserted. Availability bounds are declared assumptions,
not fabricated first-publication timestamps. Current snapshots are retrospective.
"""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from project import ROOT, RAW_FEATURES_21, RAW_FEATURES_22, require, save_json

ALIASES = {'Congo DR': 'DR Congo', 'Bosnia-Herzegovina': 'Bosnia and Herzegovina',
           'Czechia': 'Czech Republic', 'Türkiye': 'Turkey'}
HISTORY_URL = 'https://raw.githubusercontent.com/martj42/international_results/b7a3a8ee5d37780c6a03101c188658fd439e241d/results.csv'


def read_history(sources):
    h = pd.read_csv(Path(sources) / 'international_results.csv')
    required = {'date', 'home_team', 'away_team', 'home_score', 'away_score', 'tournament', 'country', 'neutral'}
    require(required <= set(h), 'Unexpected historical data schema')
    h['date'] = pd.to_datetime(h.date, utc=True, errors='raise')
    h['ambiguous_duplicate_key'] = h.duplicated(['date', 'home_team', 'away_team', 'tournament'], keep=False)
    for col in ['home_score', 'away_score']:
        h[col] = pd.to_numeric(h[col], errors='raise')
        require((np.isfinite(h[col]) & (h[col] >= 0) & (h[col] % 1 == 0)).all(), 'Missing/invalid historical goals')
    h['history_id'] = ['H' + str(i) for i in range(len(h))]
    # Date-only records lack kickoff time/timezone. Two UTC midnights later
    # provides a conservative eligibility boundary, rather than a made-up end time.
    h['conservative_known_by_utc'] = h.date + pd.Timedelta(days=2)
    return h.sort_values(['date', 'history_id'])


def team_history(history, team):
    home = history.loc[history.home_team.eq(team)].copy()
    away = history.loc[history.away_team.eq(team)].copy()
    home['gf'], home['ga'] = home.home_score, home.away_score
    away['gf'], away['ga'] = away.away_score, away.home_score
    return pd.concat([home, away]).sort_values(['date', 'history_id'])


def form_snapshot(team_rows, kickoff):
    eligible = team_rows[team_rows.conservative_known_by_utc < kickoff]
    recent = eligible.tail(10)
    require(len(recent) == 10, 'Fewer than ten sourced earlier matches; do not invent form')
    gf, ga = recent.gf.to_numpy(), recent.ga.to_numpy()
    wc = eligible[(eligible.tournament == 'FIFA World Cup') & (eligible.date.dt.year < 2026)]
    values = {
        'goals_for_last10': float(gf.mean()), 'goals_against_last10': float(ga.mean()),
        'win_rate_last10': float((gf > ga).mean()),
        'days_since_last_match': int((kickoff.floor('D') - eligible.date.max()).days),
        'matches_last365': int((eligible.date >= kickoff.floor('D') - pd.Timedelta(days=365)).sum()),
        'goal_difference_std_last10': float(np.std(gf - ga, ddof=0)),
        'wc_appearances': int(wc.date.dt.year.nunique()),
        'scoring_rate_last10': float((gf > 0).mean()),
        'clean_sheet_rate_last10': float((ga == 0).mean()),
        'goals_for_std_last10': float(np.std(gf, ddof=0)),
        'draw_rate_last10': float((gf == ga).mean()),
    }
    evidence = {'recent_history_ids': recent.history_id.tolist(),
                'recent_dates': recent.date.dt.strftime('%Y-%m-%d').tolist(),
                'recent_goals_for': gf.tolist(), 'recent_goals_against': ga.tolist(),
                'latest_eligible_history_date': eligible.date.max().isoformat(),
                'latest_conservative_known_by_utc': eligible.conservative_known_by_utc.max().isoformat(),
                'world_cup_editions_before_2026': sorted(wc.date.dt.year.unique().tolist())}
    return values, evidence


def build(sources=ROOT / 'data/sources', raw=ROOT / 'data/raw'):
    sources, raw = Path(sources), Path(raw)
    raw.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((sources / 'source_manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['sha256'].items():
        actual = hashlib.sha256((sources / name).read_bytes()).hexdigest()
        require(actual == expected, f'Source snapshot changed: {name}. Audit and update source_manifest.json before rebuilding.')
    history = read_history(sources)
    events = json.loads((sources / 'espn_events.json').read_text(encoding='utf-8'))
    require(len(events) == 104, 'Expected exactly 104 independently sourced ESPN matches')
    participants = {ALIASES.get(c['team']['displayName'], c['team']['displayName'])
                    for record in events for c in record['event']['competitions'][0]['competitors']}
    relevant = history.home_team.isin(participants) | history.away_team.isin(participants)
    require(not history.loc[relevant, 'ambiguous_duplicate_key'].any(),
            'Ambiguous duplicate historical fixture involving a participating team; resolve from sources')
    history_2026 = history[(history.tournament == 'FIFA World Cup') & history.date.dt.year.eq(2026)]
    require(len(history_2026) == 104, 'Historical source does not contain 104 World Cup 2026 records')
    matches, prematch, provenance, checks, evidence_records = [], [], [], [], []
    all_features = list(dict.fromkeys(RAW_FEATURES_21 + RAW_FEATURES_22))
    cache = {}
    checked_history_ids = set()
    for record in sorted(events, key=lambda r: r['event']['date']):
        event = record['event']; competition = event['competitions'][0]
        require(competition['status']['type']['completed'], f'Unfinished match {event["id"]}')
        require(event['season']['year'] == 2026, 'Wrong ESPN season')
        competitors = {c['homeAway']: c for c in competition['competitors']}
        home, away = competitors['home'], competitors['away']
        team_a = ALIASES.get(home['team']['displayName'], home['team']['displayName'])
        team_b = ALIASES.get(away['team']['displayName'], away['team']['displayName'])
        kickoff = pd.Timestamp(event['date'])
        goals_a, goals_b = int(home['score']), int(away['score'])
        pair = history_2026[((history_2026.home_team == team_a) & (history_2026.away_team == team_b)) |
                            ((history_2026.home_team == team_b) & (history_2026.away_team == team_a))]
        pair = pair[(pair.date - kickoff.floor('D')).abs() <= pd.Timedelta(days=1)]
        require(len(pair) == 1, f'Cannot uniquely cross-check ESPN fixture {event["id"]}: {team_a}/{team_b}')
        other = pair.iloc[0]
        reversed_order = other.home_team == team_b
        checked_a = other.away_score if reversed_order else other.home_score
        checked_b = other.home_score if reversed_order else other.away_score
        require(checked_a == goals_a and checked_b == goals_b,
                f'Score discrepancy between sources for {event["id"]}; resolve from evidence')
        require(other.history_id not in checked_history_ids, 'Cross-check reused a historical fixture')
        checked_history_ids.add(other.history_id)
        matches.append({'match_id': event['id'], 'kickoff_utc': kickoff.isoformat(),
                        'results_known_by_utc': (kickoff + pd.Timedelta(hours=24)).isoformat(),
                        'team_a': team_a, 'team_b': team_b, 'goals_a': goals_a, 'goals_b': goals_b,
                        'score_definition': 'full_time_including_extra_time', 'source_url': record['source_url']})
        checks.append({'match_id': event['id'], 'history_id': other.history_id,
                       'team_a': team_a, 'team_b': team_b, 'goals_a': goals_a, 'goals_b': goals_b,
                       'source_agreement': True, 'historical_orientation_reversed': bool(reversed_order),
                       'historical_date': other.date.date().isoformat(),
                       'espn_kickoff_utc': kickoff.isoformat()})
        venue_country = competition['venue']['address']['country']
        country_alias = {'USA': 'United States', 'United States of America': 'United States',
                         'United States': 'United States', 'Mexico': 'Mexico', 'Canada': 'Canada'}
        venue_country = country_alias.get(venue_country, venue_country)
        for team in [team_a, team_b]:
            if team not in cache:
                cache[team] = team_history(history, team)
            values, evidence = form_snapshot(cache[team], kickoff)
            values['host_advantage'] = int(team in ['United States', 'Mexico', 'Canada'] and team == venue_country)
            require(pd.Timestamp(evidence['latest_conservative_known_by_utc']) < kickoff, 'History cutoff failed')
            prematch.append({'match_id': event['id'], 'team': team, **{f: values[f] for f in all_features}})
            eid = f'{event["id"]}:{team}'
            evidence_records.append({'evidence_id': eid, 'match_id': event['id'], 'team': team,
                                     'kickoff_utc': kickoff.isoformat(), 'venue_country': venue_country,
                                     **evidence, 'computed_values': values})
            for feature in all_features:
                is_host = feature == 'host_advantage'
                known_by = kickoff - pd.Timedelta(days=7) if is_host else pd.Timestamp(evidence['latest_conservative_known_by_utc'])
                # Host-country/venue classification is a scheduled context proxy.
                # Its seven-day cutoff is an explicit assumption, not an archive timestamp.
                provenance.append({'match_id': event['id'], 'team': team, 'feature': feature,
                                   'conservative_known_by_utc': known_by.isoformat(),
                                   'source_url': 'https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026' if is_host else HISTORY_URL,
                                   'evidence_note': f'feature_evidence.json evidence_id={eid}; value={values[feature]}; retrospective reconstruction; availability bound is a declared conservative assumption, not first-publication evidence'})
    require(len(checked_history_ids) == 104, 'Not all historical World Cup rows were cross-checked')
    pd.DataFrame(matches).to_csv(raw / 'matches.csv', index=False)
    pd.DataFrame(prematch).to_csv(raw / 'prematch.csv', index=False)
    pd.DataFrame(provenance).to_csv(raw / 'provenance.csv', index=False)
    pd.DataFrame(checks).to_csv(raw / 'match_crosscheck.csv', index=False)
    save_json(raw / 'feature_evidence.json', evidence_records)
    save_json(raw / 'collection_audit.json', {
        'status': 'real_source_results_crosschecked_retrospective_features',
        'matches': len(matches), 'team_match_rows': len(prematch), 'independent_score_agreements': len(checks),
        'history_rows': len(history), 'source_snapshots_sha256': manifest['sha256'],
        'unrelated_ambiguous_history_rows': int(history.ambiguous_duplicate_key.sum()),
        'unrelated_history_note': 'Two conflicting Tahiti/New Caledonia records dated 1974-02-17 are retained in the source snapshot, flagged, and do not enter any participating team history. No silent deduplication.',
        'score_convention': 'Final score including extra time, excluding penalty-shootout goals',
        'availability_assumptions': {'history': 'Eligible only after date + 2 UTC days, strictly before target kickoff',
                                     'training_labels': 'Known-by bound kickoff + 24 hours',
                                     'host_context': 'Assumed scheduled venue/host-country classification known seven days before kickoff'},
        'limitations': 'Snapshots were downloaded after the tournament. Availability bounds are conservative assumptions, not archival publication timestamps. Verify any rescheduling or retrospective corrections; source agreement is corroboration, not proof of source independence.'})
    return {'matches': len(matches), 'team_rows': len(prematch), 'crosschecked': len(checks)}


if __name__ == '__main__':
    print(build())
