# Data, predictors and reproducibility

The 104 target results come from ESPN's public World Cup scoreboard feed. Their scores agree with all 104 World Cup 2026 entries in the pinned international-results snapshot. Exact UTC kickoff times and first/second team orientation follow ESPN. The history source has 49,945 match rows through 6 October 2026; later rows are present in the snapshot but cannot enter a pre-match feature because the eligibility filter excludes them.

Historical scores include extra time and exclude shootouts. Both targets follow this convention: Task 2.1 is `goals_a - goals_b`; Task 2.2 is a team's final goals. Team A/B means ESPN's listed home/away order; it does not imply a true home-ground advantage.

## Historical window and timing

For each target team, select its last ten eligible senior international results across competitions. A date-only historical record becomes eligible at its date plus two UTC days, strictly earlier than the target kickoff. This deliberately leaves a buffer for unknown kickoff timezone and result completion. All participating teams have ten eligible earlier results; there are no invented first-match defaults. Population standard deviations use `ddof=0`.

This is a retrospective reconstruction from current source snapshots. The cutoff shows that the underlying matches precede the prediction, subject to the declared timing assumptions; it does not prove that the exact source row was published in that form before kickoff. Source corrections, team-history conventions and delayed results remain limitations.

## Task 2.1: eight predictors

Every model input below is team A minus team B.

| Raw field (model suffix `_diff`) | Calculation | Rationale |
|---|---|---|
| `goals_for_last10` | Mean goals scored across the last ten eligible internationals. | Relative scoring record. |
| `goals_against_last10` | Mean goals conceded across those ten games. | Relative defensive record. |
| `win_rate_last10` | Fraction of those games won on the final score, before shootouts. | Relative recent form. |
| `days_since_last_match` | UTC kickoff date minus the last eligible historical match date, whole days. | Recovery/schedule proxy; not exact hours since the previous final whistle. |
| `matches_last365` | Number of eligible matches dated within the preceding 365 days. | Relative international workload and match practice. |
| `goal_difference_std_last10` | Population standard deviation of scored-minus-conceded goals in the last ten games. | Relative variability/consistency. |
| `wc_appearances` | Number of distinct previous men's World Cup editions represented in the team's history, excluding 2026. | Tournament experience proxy. |
| `host_advantage` | 1 for USA/Mexico/Canada playing in its own country, else 0, using the recorded venue country. | Home-country context distinct from listed team order. |

## Task 2.2: eight predictors

| Model input | Calculation | Rationale |
|---|---|---|
| `goals_for_last10` | Own team's prior-ten mean goals scored. | Scoring level. |
| `opponent_goals_against_last10` | Opponent's prior-ten mean conceded goals. | Opposing defence. |
| `days_since_last_match` | Own team's date-based interval since its last eligible historical match. | Recovery/schedule proxy. |
| `opponent_win_rate_last10` | Opponent's prior-ten win fraction. | Strength/form of opposition. |
| `scoring_rate_last10` | Own team's fraction of prior-ten games with at least one goal. | Scoring frequency beyond mean goal volume. |
| `opponent_clean_sheet_rate_last10` | Opponent's fraction with zero goals conceded. | Frequency of opposition shutouts. |
| `goals_for_std_last10` | Own team's prior-ten population standard deviation of goals scored. | Volatility of attack. |
| `opponent_draw_rate_last10` | Opponent's prior-ten draw fraction, before shootouts. | Opposing result/style tendency. |

The first four underlying raw concepts are shared with Task 2.1. The last four are distinct. Changing a shared variable into a difference or an opponent field does not make it a new concept. Thus the overlap is **four**, exactly the allowed maximum.

These variables were selected for source availability, pre-match meaning and reproducibility, not by searching for a high holdout score. They are correlated observational summaries, not causal factors. The actual Task 2.2 VIF output flags moderate multicollinearity; do not silently remove variables because the brief requires eight.

## Cleaning and joins

`build_dataset.py` checks source SHA-256 hashes before rebuilding. It parses dates/scores, rejects invalid scores and cross-checks each ESPN fixture against a unique historical World Cup record within one calendar day, allowing for local/UTC dates. If source orientation is reversed, it compares goals for the same named teams. `match_crosscheck.csv` records those cases. Canonical name mappings are explicit: Congo DR → DR Congo; Bosnia-Herzegovina → Bosnia and Herzegovina; Czechia → Czech Republic; Türkiye → Turkey.

Two ambiguous 1974 Tahiti/New Caledonia records share the same historical fixture key but different scores. They are flagged and retained in the source snapshot, not silently deduplicated. Neither country participates in this World Cup, so they enter no participating team's feature history. Any such ambiguity involving a participating team stops the build.

`project.py` then enforces exactly 104 distinct target matches, no duplicate fixture under different IDs, the year 2026, valid integer goals and exactly the two correct team records per match. Whitespace is stripped, numeric/fraction/count fields checked, and availability bounds required to precede kickoff. It joins opposing records and explicitly selects eight model inputs. There is no feature derived from the target match's shots, goals, standings, or outcome.

## Files and evidence

- `matches.csv`: 104 rows with match ID, kickoff, conservative training-label known-by bound, team names, scores, score definition and source URL.
- `prematch.csv`: 208 rows, each with match/team keys and twelve raw feature concepts. Twelve source fields support two separate eight-input models with four shared concepts.
- `provenance.csv`: one record for each of the 2,496 observed raw feature cells, with conservative known-by bound, source URL and evidence pointer.
- `feature_evidence.json`: each team-match's last ten source IDs, dates, own/opponent goals, source eligibility bound, historical World Cup editions and computed feature values.
- `collection_audit.json`: real-source cross-check counts, source hashes, timing assumptions and known source ambiguities.
- `match_crosscheck.csv`: one corroboration record per target match, including any orientation reversal.

The conservative bounds are assumptions: date-only history becomes eligible two UTC days later, training labels 24 hours after kickoff, host-country context one week before kickoff. These are not archived source-publication times. This distinction is explicit in the field names and evidence notes; do not present them as measured timestamps.

No target score is imputed. Actual source-derived predictors have no missing cells. The reusable modelling pipeline can median-impute missing explanatory values inside training folds only; it stops if a predictor is wholly missing or the eight-predictor design is rank deficient. Genuine outlier scores remain in the complete 104/208-row datasets.

Confirm the extra-time convention with the instructor before final submission. If 90-minute targets are required, obtain trustworthy period scores and rebuild both the targets and historical score-derived predictors consistently; do not relabel these final-score results.
