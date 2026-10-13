# Task 2.2 data documentation and results notes

Prepared for Ritesh Panta's part of the HIT140 Assessment 3 group project. This file documents the data behind Task 2.2 (goals scored by one team in one match), records the data quality checks, and explains the fitted model. Numbers come from `results/task_2_2/`, `data/raw/` and `DATA_GUIDE.md`.

A data dictionary is a table that states, for every variable, what it means, its unit, where it comes from and when it becomes known. A leakage check confirms that no predictor contains information from the match whose goals the model estimates.

## Data dictionary

Task 2.2 has 208 rows, two per match. "Own" is the team whose goals form the response. "Opponent" is the other team in the same match.

| Variable | Definition | Unit and range (training rows) | Known by |
|---|---|---|---|
| `match_id` | ESPN match identifier. Metadata, never a predictor. | Integer | Kickoff |
| `team`, `opponent` | Team names after alias mapping (Congo DR to DR Congo, Czechia to Czech Republic, and two others). Metadata. | Text | Kickoff |
| `goals_scored` (response) | Own final goals, including extra time and excluding shootouts. | Whole goals, 0 to 7 | After the match |
| `goals_for_last10` | Own mean goals scored in its last ten eligible senior internationals. | Goals per match, 0.5 to 3.7 | Date of each earlier match plus 2 UTC days |
| `opponent_goals_against_last10` | Opponent's mean goals conceded in its last ten eligible matches. | Goals per match, 0.2 to 2.2 | As above |
| `days_since_last_match` | Whole days from own last eligible match to the target kickoff date. A schedule proxy, not exact rest. | Days, 4 to 76 | As above |
| `opponent_win_rate_last10` | Share of the opponent's last ten matches won on the final score. | Fraction, 0.1 to 1.0 | As above |
| `scoring_rate_last10` | Share of own last ten matches with at least one goal scored. | Fraction, 0.4 to 1.0 | As above |
| `opponent_clean_sheet_rate_last10` | Share of the opponent's last ten matches with no goals conceded. | Fraction, 0.0 to 0.8 | As above |
| `goals_for_std_last10` | Population standard deviation (ddof 0) of own goals scored over the last ten matches. | Goals, 0.49 to 3.08 | As above |
| `opponent_draw_rate_last10` | Share of the opponent's last ten matches drawn on the final score. | Fraction, 0.0 to 0.7 | As above |

Source for all predictors: Mart Jürisoo's international-results dataset, pinned to commit `b7a3a8ee`. Source for the response, kickoff times and team order: ESPN's public scoreboard feed. Both snapshots date from 10 October 2026.

## Predictor matrix: Task 2.1 and Task 2.2

Four underlying concepts appear in both models, which is the allowed maximum. Turning a concept into a difference or an opponent field does not make it a new concept.

| Concept | Task 2.1 (team A minus team B) | Task 2.2 |
|---|---|---|
| Goals scored, last 10 | `goals_for_last10_diff` | `goals_for_last10` (own) |
| Goals conceded, last 10 | `goals_against_last10_diff` | `opponent_goals_against_last10` |
| Win rate, last 10 | `win_rate_last10_diff` | `opponent_win_rate_last10` |
| Days since last match | `days_since_last_match_diff` | `days_since_last_match` (own) |
| Matches in last 365 days | `matches_last365_diff` | not used |
| Goal difference spread | `goal_difference_std_last10_diff` | not used |
| World Cup experience | `wc_appearances_diff` | not used |
| Host advantage | `host_advantage_diff` | not used |
| Scoring rate | not used | `scoring_rate_last10` (own) |
| Clean-sheet rate | not used | `opponent_clean_sheet_rate_last10` |
| Spread of goals scored | not used | `goals_for_std_last10` (own) |
| Draw rate | not used | `opponent_draw_rate_last10` |

## Data quality log

| Check | Result |
|---|---|
| Matches and team rows | 104 matches, 208 team rows, two per match |
| Score agreement | All 104 ESPN scores match the historical dataset |
| Missing predictor cells | None. All 2,496 raw feature cells (208 rows by 12 concepts) carry a provenance record |
| Historical window | Every participating team has ten eligible earlier matches. No first-match defaults are used |
| Exclusions | One match (9 July) stays in the dataset but is left out of fitting. Its assumed outcome-availability time is later than the first held-out kickoff |
| Split | Training: 96 matches (192 rows). Holdout: 7 matches (14 rows), 10 to 19 July. Both rows of a match stay together |
| Ambiguous history | Two 1974 Tahiti and New Caledonia records share a fixture key with different scores. Neither team plays in 2026, so no feature uses them |
| Extreme value | `days_since_last_match` reaches 76 for one team (Uruguay). It stays in the data. Task 2.1 is more sensitive to it than Task 2.2 |
| Outliers | None removed. 11 training rows exceed the Cook's distance cut-off of 4/n and are reported, not deleted |

Source checks still open. The group must confirm:

- [x] Extra-time convention agreed with the instructor.
- [x] Rescheduled or delayed matches checked against the two-day eligibility rule.
- [x] Ritesh's own spot check of several rows against the source (team, opponent, features, goals).

## Leakage checks

- No predictor uses shots, possession, goals or any statistic from the target match.
- Each earlier match enters a feature only if its date plus two UTC days is strictly before the target kickoff.
- The response never enters its own row's predictors.
- The code fits median imputation and standardisation on training rows only. No cell needed imputing.
- The holdout was not used to choose predictors, transformations or exclusions.
- Limit: the features are a retrospective rebuild from current snapshots. The cut-offs are assumptions, not archived publication times.

## Task 2.2 model and results

The fitted equation, in original units, is:

```text
goals_scored = 1.9625
  + 0.8274 * goals_for_last10
  + 0.2554 * opponent_goals_against_last10
  - 0.0016 * days_since_last_match
  - 2.0299 * opponent_win_rate_last10
  - 0.6508 * scoring_rate_last10
  - 0.1006 * opponent_clean_sheet_rate_last10
  - 0.2316 * goals_for_std_last10
  - 1.2683 * opponent_draw_rate_last10
```

A coefficient is the change in predicted goals for a one-unit rise in that predictor with the others held fixed. It describes association, not cause.

**Holdout performance** (7 matches, 14 rows):

| Model | MAE | RMSE | R² |
|---|---|---|---:|
| Linear regression | 1.127 | 1.646 | -0.125 |
| Training mean | 1.143 | 1.602 | -0.066 |

The regression has a slightly lower MAE but a higher RMSE and a lower R² than predicting the training mean. It is not an improvement on this test period. The largest miss is a match with 6 actual goals against a prediction of 1.18. The model's predictions stay between about 0.6 and 2.2 goals, so it cannot reproduce high-scoring games.

**Training-period validation.** Across the five forward folds, the model has a lower RMSE than the training mean in folds 1 to 4 and about equal in fold 5 (six matches). The pooled out-of-fold RMSE is 1.227 against 1.316 for the baseline (`ADDITIONAL_REVIEW.md`). The model looks slightly useful earlier in the tournament and not in the seven-match holdout, but seven matches cannot settle which is the true picture.

**Coefficients.** Match-clustered standard errors on standardised predictors give:

- `goals_for_last10` is the only predictor with p below 0.05 (p = 0.034). The model predicts more goals for a team with a higher recent scoring average.
- `opponent_win_rate_last10` is borderline (p = 0.053) and negative: the model predicts fewer goals against stronger opponents.
- The other six predictors have p above 0.19, so their individual effects are not distinguishable from zero.

**Diagnostics.**

| Measure | Value | Reading |
|---|---|---|
| Training R² / adjusted R² | 0.199 / 0.164 | Weak fit. Not a test score |
| Maximum VIF | 6.49 (`goals_for_last10`) | Moderate collinearity |
| Breusch-Pagan p-value | 0.020 | Evidence of non-constant residual variance |
| Correlated pairs | `goals_for_last10` with `scoring_rate_last10` (0.77); `opponent_goals_against_last10` with `opponent_clean_sheet_rate_last10` (-0.80) | Related measures share information, so their separate signs are unreliable |

The negative signs on `scoring_rate_last10` and `opponent_draw_rate_last10` are not football effects. They likely come from the overlap in the preceding row, and neither differs statistically from zero.

## Limitations for the report

- A seven-match holdout is a fragile basis for any claim about accuracy.
- Goals are non-negative counts, and linear regression gives fractional predictions. This holdout produced no negative predictions.
- Team rows repeat across matches and time, so standard errors are approximate even with match clustering.
- Later knockout matches differ from group-stage matches, and the training window holds mostly group-stage matches.
- All eight predictors were kept, as the brief requires, despite the collinearity.
