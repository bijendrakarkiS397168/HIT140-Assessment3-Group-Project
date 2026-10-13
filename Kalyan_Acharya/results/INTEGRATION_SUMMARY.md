# Generated integration summary

These results describe the supplied data only. Check source authenticity before submission.

## Task 2.1

Chronological holdout:

| Model | MAE | MSE | RMSE | NRMSE (training range) | R² |
|---|---:|---:|---:|---:|---:|
| linear_regression | 1.2112 | 1.9662 | 1.4022 | 0.1402 | 0.1079 |
| training_mean | 1.5030 | 2.8546 | 1.6896 | 0.1690 | -0.2951 |

See task_2_1/ for coefficients, equation, fold metrics and plots.

## Task 2.2

Chronological holdout:

| Model | MAE | MSE | RMSE | NRMSE (training range) | R² |
|---|---:|---:|---:|---:|---:|
| linear_regression | 1.1269 | 2.7082 | 1.6456 | 0.2351 | -0.1246 |
| training_mean | 1.1429 | 2.5672 | 1.6023 | 0.2289 | -0.0660 |

See task_2_2/ for coefficients, equation, fold metrics and plots.

## Interpretation checklist

- Compare holdout error with the training-mean baseline; do not claim a model is better without the comparison.
- Describe coefficient units and direction while holding the other predictors fixed; associations are not causal effects.
- Review residual patterns, VIF, influence and the count of negative goal predictions.
- Report repeated-team dependence, the small sample and later-tournament distribution shifts.
- Do not use the holdout to select predictors, transformations or remove observations.
