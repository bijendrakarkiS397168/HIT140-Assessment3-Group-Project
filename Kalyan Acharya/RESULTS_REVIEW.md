# Results review for the group

These figures are calculated from the actual downloaded source data, not artificial tests. The targets include extra time and exclude shootouts. The full collection, timing and score-definition qualifications are in README.md, DATA_GUIDE.md and SOURCE_REVIEW.md.

## Chronological holdout

Training: 96 matches (192 team rows). Holdout: 7 matches (14 team rows), 10 to 19 July 2026. One 9 July fixture remains in the complete dataset but is purged from fitting because its conservative label-availability bound overlaps the first held-out kickoff. This is a small later-stage test set; results should not be generalised confidently to other tournaments.

| Task / model | MAE | MSE | RMSE | NRMSE, training range | R² |
|---|---:|---:|---:|---:|---:|
| 2.1 goal difference, OLS | 1.2112 | 1.9662 | 1.4022 | 0.1402 | 0.1079 |
| 2.1 training-mean baseline | 1.5030 | 2.8546 | 1.6896 | 0.1690 | -0.2951 |
| 2.2 team goals, OLS | 1.1269 | 2.7082 | 1.6456 | 0.2351 | -0.1246 |
| 2.2 training-mean baseline | 1.1429 | 2.5672 | 1.6023 | 0.2289 | -0.0660 |

The goal-difference regression has lower held-out absolute and squared error than its training-mean baseline. Its R² is positive but modest. The goals-scored regression has marginally lower MAE but higher MSE/RMSE than its baseline, with negative R². It does not demonstrate improved squared-error prediction on this holdout. Training fits should not be used to hide this outcome.

The model outputs are continuous; a real goal count is discrete. No rounding or clipping was used to make metrics look better. The model JSON, equation and raw predictions are available for inspection in each task folder.

## Diagnostics that need discussion

- Task 2.1's training adjusted R² is approximately 0.363; Task 2.2's is approximately 0.164. These are in-sample diagnostics, not estimates of predictive accuracy.
- Task 2.2 has a training Breusch-Pagan p-value around 0.020, consistent with non-constant residual variance. Match-clustered inference is supplied, but repeated-team dependence and small-sample inference remain concerns.
- Task 2.2's maximum VIF is about 6.49, for prior mean goals scored. Explain the correlated form measures and uncertainty in individual coefficients. There is no automatic deletion that would break the eight-predictor requirement.
- Both residual Q-Q plots show upper-tail departures. Goal-score distributions are not Gaussian, and the count target has a nonnegative boundary. Neither plot establishes that the linear model is an ideal data-generating description.
- **A particularly influential Task 2.1 training fixture is Saudi Arabia against Uruguay, ESPN ID 760429.** The history snapshot's last eligible Uruguay international before its opening match is dated 31 March, producing a 76-day interval; Saudi Arabia's corresponding interval is much shorter. The resulting interval difference drives leverage of about 0.966 and Cook's distance of about 6.63. This is a sourced schedule proxy, not a measurement of players' training/rest or a reason to silently delete a real match. Recheck historical coverage and discuss coefficient sensitivity before interpreting the interval coefficient.
- Outlier/influence flags are review prompts, not deletion instructions. All 104 real matches remain in the modelling datasets.

Five forward-validation periods, each following at least 20 earlier eligible matches, are saved separately in `forward_cv_metrics.csv`. Their performance varies. Describe that variation rather than assuming a single small holdout is a stable estimate. No model transformation or predictor substitution was selected by searching for a better final holdout score.

## Suggested evidence for the four-page report

Use the predictor definitions and source method, one compact held-out comparison table, each model's full equation, and a small selection of diagnostic figures. Explain the difference between a pre-match retrospective feature reconstruction and an archived pre-kickoff dataset. State the score-duration convention, paired team rows, exact four shared concepts, timing buffer assumptions and small test sample. The group must verify the discussion, not copy it as a claim of independent authorship.
