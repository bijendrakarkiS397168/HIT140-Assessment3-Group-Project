# Additional review

## Influence sensitivity

Exploratory coefficient comparison refits Task 2.1 using training matches only, omitting the already flagged Saudi Arabia–Uruguay fixture 760429. This is a sensitivity diagnostic, not a replacement submission model. No holdout metrics were consulted to choose the fit, and all 104 matches remain in the main dataset.

See results/training_coefficient_sensitivity.csv. Large coefficient changes weaken individual-coefficient interpretation; no missing historical matches or corrected rest values are invented.

## Forward validation

Task 2.1: five validation folds; OLS RMSE range 1.0123–2.1301. Pooled out-of-fold RMSE 1.6921; baseline 2.0671. Weighting by validation match count is equivalent to row weighting within each task. These predictions are from the training period, not the final holdout.

Task 2.2: five validation folds; OLS RMSE range 1.0216–1.3663. Pooled out-of-fold RMSE 1.2268; baseline 1.3155. Weighting by validation match count is equivalent to row weighting within each task. These predictions are from the training period, not the final holdout.

## Output correction

Previous runs saved results successfully but did not display them. The revised scripts now print actual/predicted values, metrics and equations, and open an offline HTML results page. --no-open disables browser opening for automated checks. Match identities now accompany held-out predictions. No targets, feature definitions, split policy or main fitted coefficients were changed.