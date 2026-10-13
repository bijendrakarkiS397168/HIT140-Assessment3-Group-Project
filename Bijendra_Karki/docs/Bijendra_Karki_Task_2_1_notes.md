# Bijendra Karki: Task 2.1 goal-difference model notes

These notes summarise `results/task_2_1/` and the shared pipeline in `project.py`. All numbers come from the saved result files.

## Model

Task 2.1 predicts the goal difference of one match (team A goals minus team B goals) from eight pre-match predictors. Each predictor is the difference between team A and team B. The data has 104 matches, so the model has 104 rows.

| Predictor (difference, A minus B) | Meaning |
|---|---|
| `goals_for_last10_diff` | Mean goals scored over the last ten eligible matches |
| `goals_against_last10_diff` | Mean goals conceded over the same matches |
| `win_rate_last10_diff` | Share of those matches won |
| `days_since_last_match_diff` | Days since the last eligible match |
| `matches_last365_diff` | Matches played in the previous 365 days |
| `goal_difference_std_last10_diff` | Spread of goal difference over the last ten matches |
| `wc_appearances_diff` | Earlier World Cup editions played |
| `host_advantage_diff` | 1 for a host nation playing in its own country, else 0 |

The fitted equation, in original units, is:

```text
goal_difference = 0.1193
  + 0.6814 * goals_for_last10_diff
  - 0.8005 * goals_against_last10_diff
  - 0.8315 * win_rate_last10_diff
  - 0.0003 * days_since_last_match_diff
  + 0.0181 * matches_last365_diff
  - 0.4651 * goal_difference_std_last10_diff
  + 0.0770 * wc_appearances_diff
  + 0.5203 * host_advantage_diff
```

## Holdout result

The holdout is the last 20% of match days: 7 matches from 10 to 19 July 2026. The training set has 96 matches.

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| Linear regression | 1.211 | 1.402 | 0.108 |
| Training mean | 1.503 | 1.690 | -0.295 |

The model beats the training mean on MAE, RMSE and R². The R² is positive but small, and seven matches are a fragile test. Inside the training period, the pooled out-of-fold RMSE is 1.692 against 2.067 for the baseline.

## Coefficients and diagnostics

Standard errors are HC3 robust. On standardised predictors, three predictors have p below 0.05: `goals_for_last10_diff` (0.039), `goals_against_last10_diff` (0.038) and `wc_appearances_diff` (0.005). `goal_difference_std_last10_diff` is borderline (0.089). The other four are not distinguishable from zero.

| Measure | Value |
|---|---|
| Training R² / adjusted R² | 0.416 / 0.363 |
| Breusch-Pagan p-value | 0.697 (no evidence of non-constant variance) |
| Cook's distance above 4/n | 8 training rows |

## Influential match

One training match, Saudi Arabia against Uruguay (ESPN ID 760429), has leverage of about 0.966 and a Cook's distance of about 6.63. Uruguay's last eligible earlier match is 76 days before its opening game, which produces an extreme value for the days-since-last-match difference. Refitting on training data without this match moves that coefficient from about -0.0003 to 0.179. The main model keeps the match, because it is a real result and no rule justifies dropping it. The coefficient on days since the last match should not be interpreted.

## Limitations

- Seven holdout matches cannot support a confident claim about accuracy.
- The features are a retrospective rebuild from snapshots, not an archive of values published before each match.
- Teams repeat across matches, so standard errors are approximate.
- The coefficients describe association, not cause.
